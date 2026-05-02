from app.agents.base import BaseTool, ToolResult, AgentContext
import logging

logger = logging.getLogger(__name__)

class PaddleOCRTool(BaseTool):
    @property
    def name(self) -> str:
        return "paddle_ocr"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        # Placeholder for PaddleOCR
        return ToolResult(
            tool_name=self.name,
            output={"text": "Extracted text from PaddleOCR"},
            confidence=0.8,
            processing_time_ms=0.0
        )

class TesseractTool(BaseTool):
    @property
    def name(self) -> str:
        return "tesseract_ocr"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            output={"text": "Extracted text from Tesseract"},
            confidence=0.6,
            processing_time_ms=0.0
        )

class GPT4oVisionOCRTool(BaseTool):
    @property
    def name(self) -> str:
        return "gpt4o_vision_ocr"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            output={"text": "Extracted text from GPT-4o"},
            confidence=0.95,
            processing_time_ms=0.0
        )
