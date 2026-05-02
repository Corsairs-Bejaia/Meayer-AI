import logging
import re
from typing import List, Optional, Dict, Any

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.classifier_tools import KeywordClassifierTool, VisualSimilarityTool, GeminiClassifierTool

logger = logging.getLogger(__name__)


class ClassifierAgent(BaseAgent):
    

    @property
    def name(self) -> str:
        return "classifier"

    @property
    def tools(self) -> List[BaseTool]:
        return [
            KeywordClassifierTool(),
            VisualSimilarityTool(),
            GeminiClassifierTool(),
        ]

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)
