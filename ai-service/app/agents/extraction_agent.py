from app.agents.base import BaseAgent, BaseTool
from app.tools.extraction_tools import PositionalExtractorTool, RegexExtractorTool, LLMVisionExtractorTool
from typing import List

class ExtractionAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "extraction"

    @property
    def tools(self) -> List[BaseTool]:
        return [
            PositionalExtractorTool(),
            RegexExtractorTool(),
            LLMVisionExtractorTool()
        ]

    def __init__(self, confidence_threshold: float = 0.6):
        super().__init__(confidence_threshold)
