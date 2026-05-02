import logging
import asyncio
import time
from functools import lru_cache
from typing import List, Dict, Any

from app.agents.base import BaseTool, ToolResult, AgentContext

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _get_paddle_ocr():
    
    try:
        from paddleocr import PaddleOCR
        
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang="arabic",       
            show_log=False,
            enable_mkldnn=False, 
        )
        return ocr
    except ImportError:
        logger.warning("PaddleOCR not installed. PaddleOCRTool will be unavailable.")
        return None


def _run_ocr_sync(image_bytes: bytes) -> List[Any]:
    
    import tempfile, os
    ocr = _get_paddle_ocr()
    if ocr is None:
        return []
    
    import numpy as np
    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    result = ocr.ocr(img, cls=True)
    return result or []


class PaddleOCRTool(BaseTool):
    

    @property
    def name(self) -> str:
        return "paddle_ocr"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(
                tool_name=self.name,
                output=None,
                confidence=0.0,
                processing_time_ms=0.0,
                error="No image_bytes provided",
            )

        loop = asyncio.get_event_loop()
        raw_result = await loop.run_in_executor(None, _run_ocr_sync, image_bytes)

        
        lines = []
        full_text_parts = []
        confidences = []

        for page in raw_result:
            if not page:
                continue
            for item in page:
                bbox, (text, conf) = item
                lines.append({"text": text, "bbox": bbox, "confidence": conf})
                full_text_parts.append(text)
                confidences.append(conf)

        full_text = "\n".join(full_text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return ToolResult(
            tool_name=self.name,
            output={
                : full_text,
                : lines,
                : avg_confidence,
                : len(lines),
            },
            confidence=avg_confidence,
            processing_time_ms=0.0,
        )
