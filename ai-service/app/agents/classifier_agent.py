import logging
import re
from typing import List, Optional, Dict, Any

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.classifier_tools import KeywordClassifierTool, VisualSimilarityTool
from app.tools.gpt4o_vision_tool import GPT4oClassifierTool

logger = logging.getLogger(__name__)


class ClassifierAgent(BaseAgent):
    """
    Classifies uploaded documents by type.
    Tool order: Keywords (free, fast) → Visual Similarity (free) → GPT-4o Vision (paid, accurate)
    """

    @property
    def name(self) -> str:
        return "classifier"

    @property
    def tools(self) -> List[BaseTool]:
        return [
            KeywordClassifierTool(),
            VisualSimilarityTool(),
            GPT4oClassifierTool(),
        ]

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)
