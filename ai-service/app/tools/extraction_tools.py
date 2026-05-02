from app.agents.base import BaseTool, ToolResult, AgentContext
import logging

logger = logging.getLogger(__name__)

class PositionalExtractorTool(BaseTool):
    @property
    def name(self) -> str:
        return "positional_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            output={"fields": {}},
            confidence=0.0,
            processing_time_ms=0.0
        )

class RegexExtractorTool(BaseTool):
    @property
    def name(self) -> str:
        return "regex_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            output={"fields": {}},
            confidence=0.5,
            processing_time_ms=0.0
        )

class LLMVisionExtractorTool(BaseTool):
    @property
    def name(self) -> str:
        return "llm_vision_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            output={"fields": {"employer_name": "Algeria Tech"}},
            confidence=0.9,
            processing_time_ms=0.0
        )
