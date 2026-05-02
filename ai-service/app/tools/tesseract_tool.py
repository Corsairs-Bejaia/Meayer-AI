import asyncio
import logging
import io
from typing import List, Dict, Any

import pytesseract
from PIL import Image

from app.agents.base import BaseTool, ToolResult, AgentContext

logger = logging.getLogger(__name__)


def _tesseract_sync(image_bytes: bytes) -> Dict[str, Any]:
    
    img = Image.open(io.BytesIO(image_bytes))
    
    data = pytesseract.image_to_data(
        img,
        lang="fra+ara",
        output_type=pytesseract.Output.DICT,
    )

    words = []
    full_text_parts = []
    confidences = []

    for i, word in enumerate(data["text"]):
        word = word.strip()
        if not word:
            continue
        conf = int(data["conf"][i])
        if conf < 0:  
            continue
        words.append({"text": word, "confidence": conf / 100.0})
        full_text_parts.append(word)
        confidences.append(conf / 100.0)

    full_text = " ".join(full_text_parts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        : full_text,
        : words,
        : avg_confidence,
        : len(words),
    }


class TesseractTool(BaseTool):
    

    @property
    def name(self) -> str:
        return "tesseract_ocr"

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

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _tesseract_sync, image_bytes)
            return ToolResult(
                tool_name=self.name,
                output=result,
                confidence=result["avg_confidence"],
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return ToolResult(
                tool_name=self.name,
                output=None,
                confidence=0.0,
                processing_time_ms=0.0,
                error=str(e),
            )
