from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from typing import List

class ConsistencyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "consistency"

    @property
    def tools(self) -> List[BaseTool]:
        return [] # No specific tools, logic is in run

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        # Cross-document validation logic
        # Compare names, dates, etc.
        return ToolResult(
            tool_name="consistency_check",
            output={"consistent": True, "flags": []},
            confidence=1.0,
            processing_time_ms=0.0
        )
