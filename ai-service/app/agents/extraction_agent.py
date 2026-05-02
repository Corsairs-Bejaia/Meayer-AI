import logging
from typing import List, Dict, Any, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.extraction_tools import PositionalExtractorTool, RegexExtractorTool
from app.tools.gpt4o_vision_tool import GPT4oExtractorTool
from app.config import settings

logger = logging.getLogger(__name__)


class ExtractionAgent(BaseAgent):
    """
    Template-aware field extraction with hybrid strategy and self-correction.
    """

    @property
    def name(self) -> str:
        return "extraction"

    @property
    def tools(self) -> List[BaseTool]:
        return [
            PositionalExtractorTool(),
            RegexExtractorTool(),
            GPT4oExtractorTool(),
        ]

    def __init__(self, confidence_threshold: float = 0.6):
        super().__init__(confidence_threshold)
        self._positional = PositionalExtractorTool()
        self._regex = RegexExtractorTool()
        self._llm = GPT4oExtractorTool()

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        fields: List[Dict] = kwargs.get("fields", [])
        doc_type: str = kwargs.get("doc_type", "document")

        if not fields:
            return ToolResult(tool_name=self.name, output={"fields": {}},
                              confidence=0.0, processing_time_ms=0.0, error="No fields defined")

        # Step 1: Positional extraction for fields with position_hint
        positional_result = await self._positional.execute(context, **kwargs)
        context.add_trace(self.name, "positional_extractor",
                          positional_result.confidence, "positional pass")
        merged: Dict[str, Any] = dict(positional_result.output.get("fields", {}))

        # Step 2: Regex extraction for remaining fields
        regex_result = await self._regex.execute(context, **kwargs)
        context.add_trace(self.name, "regex_extractor",
                          regex_result.confidence, "regex pass")
        for fname, fdata in regex_result.output.get("fields", {}).items():
            if fname not in merged:  # Don't override positional results
                merged[fname] = fdata

        # Step 3: Find missing required fields
        required_fields = [f for f in fields if f.get("is_required", False)]
        missing = [
            f for f in required_fields
            if f["field_name"] not in merged
            or merged[f["field_name"]].get("confidence", 0) < 0.4
        ]

        # Self-correction loop: try LLM for missing fields
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
            context.add_trace(self.name, "gpt4o_extractor",
                              llm_result.confidence, f"self-correction retry {retries}")

            if llm_result.output:
                for fname, fdata in llm_result.output.get("fields", {}).items():
                    if isinstance(fdata, dict) and fdata.get("value") is not None:
                        merged[fname] = {**fdata, "source": "llm_vision"}

            # Recheck which are still missing
            missing = [
                f for f in required_fields
                if f["field_name"] not in merged
                or merged[f["field_name"]].get("confidence", 0) < 0.4
            ]

        # Post-processing: validate and coerce field types
        for field in fields:
            fname = field["field_name"]
            if fname not in merged:
                continue
            val = merged[fname].get("value")
            if val is None:
                continue

            ftype = field.get("field_type", "text")
            val_regex = field.get("validation_regex")

            # Type coercion
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

            # Regex validation
            if val_regex:
                import re
                if not re.fullmatch(val_regex, str(merged[fname].get("value", "")), re.IGNORECASE):
                    merged[fname]["confidence"] = 0.0
                    merged[fname]["validation_failed"] = True

        # Calculate overall confidence
        all_confs = [v.get("confidence", 0) for v in merged.values() if isinstance(v, dict)]
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0.0

        # Penalize if required fields are still missing
        if missing:
            penalty = len(missing) / len(required_fields)
            avg_conf *= (1 - penalty * 0.5)

        result = ToolResult(
            tool_name=self.name,
            output={
                "extracted_fields": merged,
                "missing_required": [f["field_name"] for f in missing],
                "extraction_method": "hybrid",
            },
            confidence=avg_conf,
            processing_time_ms=0.0,
        )
        context.results[self.name] = result
        return result
