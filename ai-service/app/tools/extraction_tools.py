import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.gpt4o_vision_tool import GPT4oExtractorTool

logger = logging.getLogger(__name__)


FIELD_PATTERNS = {
    : re.compile(r"\b(\d{2}/\d{7})\b"),
    : re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b"),
    : re.compile(r"\b(\d{18})\b"),
    : re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b"),
    : re.compile(r"\b(0[5-7]\d{8})\b"),
}


def _normalize_date(raw: str) -> str:
    
    for sep in "/", "-":
        parts = raw.split(sep)
        if len(parts) == 3:
            if len(parts[0]) == 4:  
                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            else:  
                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return raw


class RegexExtractorTool(BaseTool):
    

    @property
    def name(self) -> str:
        return "regex_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        fields: List[Dict] = kwargs.get("fields", [])
        
        ocr_result = context.get_result("ocr")
        text = ""
        if ocr_result and ocr_result.output:
            text = ocr_result.output.get("text", "")

        if not text or not fields:
            return ToolResult(tool_name=self.name, output={"fields": {}},
                              confidence=0.0, processing_time_ms=0.0)

        extracted: Dict[str, Any] = {}
        matched_count = 0

        for field in fields:
            fname = field.get("field_name", "")
            val_regex = field.get("validation_regex")

            
            if val_regex:
                try:
                    m = re.search(val_regex, text, re.IGNORECASE)
                    if m:
                        extracted[fname] = {"value": m.group(0).strip(), "confidence": 0.85, "source": "regex"}
                        matched_count += 1
                        continue
                except re.error:
                    pass

            
            for pattern_key, pattern in FIELD_PATTERNS.items():
                if pattern_key in fname.lower():
                    m = pattern.search(text)
                    if m:
                        val = m.group(1)
                        if "date" in pattern_key:
                            val = _normalize_date(val)
                        extracted[fname] = {"value": val, "confidence": 0.75, "source": "regex_builtin"}
                        matched_count += 1
                        break

        required_count = sum(1 for f in fields if f.get("is_required", False))
        matched_required = sum(
            1 for f in fields
            if f.get("is_required") and f.get("field_name") in extracted
        )
        confidence = matched_required / required_count if required_count > 0 else (
            matched_count / len(fields) if fields else 0.0
        )

        return ToolResult(
            tool_name=self.name,
            output={"fields": extracted},
            confidence=min(confidence, 0.85),
            processing_time_ms=0.0,
        )


class PositionalExtractorTool(BaseTool):
    

    @property
    def name(self) -> str:
        return "positional_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        import cv2
        import numpy as np
        image_bytes: bytes = kwargs.get("image_bytes")
        fields: List[Dict] = kwargs.get("fields", [])

        positional_fields = [f for f in fields if f.get("position_hint")]
        if not image_bytes or not positional_fields:
            return ToolResult(tool_name=self.name, output={"fields": {}},
                              confidence=0.0, processing_time_ms=0.0)

        try:
            from app.tools.paddleocr_tool import PaddleOCRTool
            paddle = PaddleOCRTool()
        except Exception:
            return ToolResult(tool_name=self.name, output={"fields": {}},
                              confidence=0.0, processing_time_ms=0.0, error="PaddleOCR unavailable")

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        h, w = img.shape[:2]

        extracted: Dict[str, Any] = {}
        confidences: List[float] = []

        for field in positional_fields:
            fname = field["field_name"]
            hint = field["position_hint"]  
            try:
                x1 = int(hint["x"] * w)
                y1 = int(hint["y"] * h)
                x2 = int((hint["x"] + hint["width"]) * w)
                y2 = int((hint["y"] + hint["height"]) * h)

                
                x1 = max(0, x1 - 5)
                y1 = max(0, y1 - 5)
                x2 = min(w, x2 + 5)
                y2 = min(h, y2 + 5)

                roi = img[y1:y2, x1:x2]
                _, buf = cv2.imencode(".png", roi)
                roi_bytes = buf.tobytes()

                r = await paddle.execute(context, image_bytes=roi_bytes)
                text = (r.output or {}).get("text", "").strip()
                conf = r.confidence if text else 0.0

                if text:
                    extracted[fname] = {"value": text, "confidence": conf, "source": "positional"}
                    confidences.append(conf)
            except Exception as e:
                logger.warning(f"Positional extraction failed for field {fname}: {e}")

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return ToolResult(
            tool_name=self.name,
            output={"fields": extracted},
            confidence=avg_conf,
            processing_time_ms=0.0,
        )
