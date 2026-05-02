import logging
import asyncio
import time
from functools import lru_cache
from typing import List, Dict, Any

from app.agents.base import BaseTool, ToolResult, AgentContext

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _get_paddle_ocr():
    """Lazy-load PaddleOCR to avoid slow startup. Cached as singleton."""
    try:
        from paddleocr import PaddleOCR
        # Use multilingual model — handles Arabic + French + digits
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang="arabic",       # Arabic model with Latin script support
            show_log=False,
            enable_mkldnn=False, # Disable for compatibility
        )
        return ocr
    except ImportError:
        logger.warning("PaddleOCR not installed. PaddleOCRTool will be unavailable.")
        return None


def _run_ocr_sync(image_bytes: bytes) -> List[Any]:
    """Synchronous OCR call — will be run in executor."""
    import tempfile, os
    ocr = _get_paddle_ocr()
    if ocr is None:
        return []
    # PaddleOCR needs a file path or numpy array
    import numpy as np
    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    result = ocr.ocr(img, cls=True)
    return result or []


class PaddleOCRTool(BaseTool):
    """
    Fast multi-language OCR using PaddleOCR.
    Best for: clean typed documents in Arabic/French.
    """

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

        # Parse PaddleOCR output: [[[bbox, (text, confidence)], ...]]
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
                "text": full_text,
                "lines": lines,
                "avg_confidence": avg_confidence,
                "line_count": len(lines),
            },
            confidence=avg_confidence,
            processing_time_ms=0.0,
        )
