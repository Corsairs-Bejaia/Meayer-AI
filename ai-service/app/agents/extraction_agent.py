import logging
from typing import List, Dict, Any, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.extraction_tools import PositionalExtractorTool, RegexExtractorTool
from app.tools.gemini_tool import GeminiExtractorTool
from app.config import settings

logger = logging.getLogger(__name__)


class ExtractionAgent(BaseAgent):
    

    @property
    def name(self) -> str:
        return "extraction"

    @property
    def tools(self) -> List[BaseTool]:
        return [
            PositionalExtractorTool(),
            RegexExtractorTool(),
            GeminiExtractorTool(),
        ]

    def __init__(self, confidence_threshold: float = 0.6):
        super().__init__(confidence_threshold)
        self._positional = PositionalExtractorTool()
        self._regex = RegexExtractorTool()
        self._llm = GeminiExtractorTool()

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        fields: List[Dict] = kwargs.get("fields", [])
        doc_type: str = kwargs.get("doc_type", "document")

        if not fields:
            return ToolResult(tool_name=self.name, output={"fields": {}},
                              confidence=0.0, processing_time_ms=0.0, error="No fields defined")

        
        positional_result = await self._positional.execute(context, **kwargs)
        context.add_trace(self.name, "positional_extractor",
                          positional_result.confidence, "positional pass")
        merged: Dict[str, Any] = dict(positional_result.output.get("fields", {}))

        
        regex_result = await self._regex.execute(context, **kwargs)
        context.add_trace(self.name, "regex_extractor",
                          regex_result.confidence, "regex pass")
        for fname, fdata in regex_result.output.get("fields", {}).items():
            if fname not in merged:  
                merged[fname] = fdata

        
        required_fields = [f for f in fields if f.get("is_required", False)]
        missing = [
            f for f in required_fields
            if f["field_name"] not in merged
            or merged[f["field_name"]].get("confidence", 0) < 0.4
        ]

        
        retries = 0
        while missing and retries < settings.MAX_SELF_CORRECTION_RETRIES:
            retries += 1
            logger.info(f"ExtractionAgent self-correcting: {len(missing)} missing fields (retry {retries})")
            llm_result = await self._llm.execute(
                context,
                image_bytes=image_bytes,
                doc_type=doc_type,
                fields=fields,
                missing_fields=missing,
            )
            context.add_trace(self.name, "gemini_extractor",
                              llm_result.confidence, f"self-correction retry {retries}")

            if llm_result.output:
                for fname, fdata in llm_result.output.get("fields", {}).items():
                    if isinstance(fdata, dict) and fdata.get("value") is not None:
                        merged[fname] = {**fdata, "source": "llm_vision"}

            
            missing = [
                f for f in required_fields
                if f["field_name"] not in merged
                or merged[f["field_name"]].get("confidence", 0) < 0.4
            ]

        
        for field in fields:
            fname = field["field_name"]
            if fname not in merged:
                continue
            val = merged[fname].get("value")
            if val is None:
                continue

            ftype = field.get("field_type", "text")
            val_regex = field.get("validation_regex")

            
            try:
                if ftype == "integer":
                    merged[fname]["value"] = int(str(val).strip())
                elif ftype == "boolean":
                    merged[fname]["value"] = str(val).lower() in ("oui", "yes", "true", "1")
                elif ftype == "date":
                    import re
                    from app.tools.extraction_tools import _normalize_date
                    if re.search(r"\d{2}[/-]\d{2}[/-]\d{4}", str(val)):
                        merged[fname]["value"] = _normalize_date(str(val))
            except (ValueError, TypeError):
                pass

            
            if val_regex:
                import re
                if not re.fullmatch(val_regex, str(merged[fname].get("value", "")), re.IGNORECASE):
                    merged[fname]["confidence"] = 0.0
                    merged[fname]["validation_failed"] = True

        
        all_confs = [v.get("confidence", 0) for v in merged.values() if isinstance(v, dict)]
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0.0

        
        if missing:
            penalty = len(missing) / len(required_fields)
            avg_conf *= (1 - penalty * 0.5)

        result = ToolResult(
            tool_name=self.name,
            output={
                "extracted_fields": merged,
                "missing_fields": [f["field_name"] for f in missing],
                "method": "hybrid",
            },
            confidence=avg_conf,
            processing_time_ms=0.0,
        )
        context.results[self.name] = result
        return result
