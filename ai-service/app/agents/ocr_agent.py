import logging
import re
from typing import List, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.paddleocr_tool import PaddleOCRTool
from app.tools.tesseract_tool import TesseractTool
from app.tools.gemini_tool import GeminiOCRTool
from app.tools.image_preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

ARABIC_RE = re.compile(r'[\u0600-\u06FF]')
FRENCH_RE = re.compile(r'[a-zA-ZÀ-ÿ]')


def _detect_language(text: str) -> str:
    arabic_count = len(ARABIC_RE.findall(text))
    french_count = len(FRENCH_RE.findall(text))
    if arabic_count > french_count * 2:
        return "ar"
    elif french_count > arabic_count * 2:
        return "fr"
    return "ar+fr"


class OCRAgent(BaseAgent):
    """
    Multi-engine OCR with adaptive preprocessing and self-correction.
    Tool order: PaddleOCR → Tesseract → GPT-4o Vision (last resort)
    """

    @property
    def name(self) -> str:
        return "ocr"

    @property
    def tools(self) -> List[BaseTool]:
        return [PaddleOCRTool(), TesseractTool(), GeminiOCRTool()]

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name="ocr", output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes provided")

        # Preprocess and estimate quality
        try:
            preprocessed = ImagePreprocessor.preprocess(image_bytes, profile="FAST")
            quality_score = preprocessed["metadata"]["quality_score"]
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using raw bytes")
            quality_score = 50.0  # Assume medium quality
            preprocessed = {"image_bytes": image_bytes, "metadata": {}}

        # Choose preprocessing profile based on quality
        if quality_score > 70:
            profile = "FAST"
        elif quality_score > 40:
            profile = "STANDARD"
        else:
            profile = "AGGRESSIVE"

        # Re-preprocess with the correct profile if needed
        if profile != "FAST":
            try:
                preprocessed = ImagePreprocessor.preprocess(image_bytes, profile=profile)
            except Exception:
                pass

        processed_bytes = preprocessed.get("image_bytes", image_bytes)
        kwargs_with_processed = {**kwargs, "image_bytes": processed_bytes}

        best_result: Optional[ToolResult] = None
        tools_to_try: List[BaseTool] = list(self.tools)

        # If very low quality, start directly with GPT-4o
        if quality_score < 30:
            tools_to_try = [GeminiOCRTool()]

        for tool in tools_to_try:
            try:
                result = await tool.execute(context, **kwargs_with_processed)
                context.add_trace(self.name, tool.name, result.confidence,
                                  f"quality={quality_score:.0f}, profile={profile}")

                if result.confidence >= self.confidence_threshold:
                    # Enrich output with language detection
                    text = (result.output or {}).get("text", "")
                    result.output["language"] = _detect_language(text)
                    context.results[self.name] = result
                    return result

                if not best_result or result.confidence > best_result.confidence:
                    best_result = result

            except Exception as e:
                context.add_trace(self.name, tool.name, 0.0, f"ERROR: {e}")

        if best_result:
            text = (best_result.output or {}).get("text", "")
            if isinstance(best_result.output, dict):
                best_result.output["language"] = _detect_language(text)
            context.results[self.name] = best_result
            return best_result

        return ToolResult(tool_name="ocr", output=None, confidence=0.0,
                          processing_time_ms=0.0, error="All OCR tools failed")
