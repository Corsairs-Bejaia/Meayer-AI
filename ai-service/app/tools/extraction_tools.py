import re
import logging
from typing import Dict, List, Optional, Any

from app.agents.base import BaseTool, ToolResult, AgentContext

logger = logging.getLogger(__name__)

FIELD_PATTERNS = {
    "nin": re.compile(r"\b(\d{18})\b"),
    "ssn": re.compile(r"\b(\d{2}/\d{7})\b"),
    "date": re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b"),
    "year": re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b"),
    "phone": re.compile(r"\b(0[5-7]\d{8})\b"),
}


def _normalize_date(date_str: str) -> str:
    date_str = date_str.replace("/", "-")
    parts = date_str.split("-")
    if len(parts) == 3:
        if len(parts[0]) == 4:
            return date_str
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return date_str


class RegexExtractorTool(BaseTool):
    @property
    def name(self) -> str:
        return "regex_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        ocr_result = context.get_result("ocr")
        if not ocr_result or not ocr_result.output:
            return ToolResult(tool_name=self.name, output={"fields": {}}, confidence=0.0, processing_time_ms=0.0)

        text = ocr_result.output.get("text", "")
        fields_to_extract: List[Dict] = kwargs.get("fields", [])
        extracted = {}
        found_count = 0

        for field in fields_to_extract:
            fname = field.get("field_name")
            ftype = field.get("field_type", "text")
            regex = field.get("validation_regex")

            pattern = None
            if regex:
                try:
                    pattern = re.compile(regex, re.IGNORECASE)
                except Exception:
                    pass
            if not pattern:
                pattern = FIELD_PATTERNS.get(ftype)

            if pattern:
                match = pattern.search(text)
                if match:
                    val = match.group(1) if pattern.groups > 0 else match.group(0)
                    if ftype == "date":
                        val = _normalize_date(val)
                    extracted[fname] = {"value": val, "confidence": 0.85}
                    found_count += 1

        confidence = (found_count / len(fields_to_extract)) if fields_to_extract else 0.0
        return ToolResult(
            tool_name=self.name,
            output={"fields": extracted},
            confidence=confidence,
            processing_time_ms=0.0,
        )


class PositionalExtractorTool(BaseTool):
    @property
    def name(self) -> str:
        return "positional_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        ocr_result = context.get_result("ocr")
        if not ocr_result or not ocr_result.output:
            return ToolResult(tool_name=self.name, output={"fields": {}}, confidence=0.0, processing_time_ms=0.0)

        lines = ocr_result.output.get("lines", [])
        fields_to_extract: List[Dict] = kwargs.get("fields", [])
        extracted = {}
        
        for field in fields_to_extract:
            hint = field.get("position_hint")
            if not hint:
                continue
            
            target_x = hint.get("x", 0.5)
            target_y = hint.get("y", 0.5)
            
            best_match = None
            min_dist = 100.0
            
            for line in lines:
                bbox = line.get("bbox")
                if not bbox: continue
                # bbox is usually [[x,y], [x,y], [x,y], [x,y]] or [x,y,w,h]
                # simplification:
                if isinstance(bbox[0], list):
                    cx = (bbox[0][0] + bbox[2][0]) / 2.0
                    cy = (bbox[0][1] + bbox[2][1]) / 2.0
                else:
                    cx = bbox[0] + bbox[2]/2.0
                    cy = bbox[1] + bbox[3]/2.0
                
                dist = ((cx - target_x)**2 + (cy - target_y)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    best_match = line.get("text")
            
            if best_match and min_dist < 0.1:
                extracted[field["field_name"]] = {"value": best_match, "confidence": 0.7}

        return ToolResult(
            tool_name=self.name,
            output={"fields": extracted},
            confidence=0.5 if extracted else 0.0,
            processing_time_ms=0.0,
        )
