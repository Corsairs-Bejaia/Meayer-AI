import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext


class MockTool(BaseTool):
    def __init__(self, name: str, confidence: float, error: str = None):
        self._name = name
        self._confidence = confidence
        self._error = error

    @property
    def name(self) -> str:
        return self._name

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        if self._error:
            raise Exception(self._error)
        return ToolResult(
            tool_name=self._name,
            output={"value": f"result_from_{self._name}"},
            confidence=self._confidence,
            processing_time_ms=10.0,
        )


class MockAgent(BaseAgent):
    def __init__(self, tools, threshold=0.7):
        super().__init__(confidence_threshold=threshold)
        self._tools = tools

    @property
    def name(self) -> str:
        return "mock_agent"

    @property
    def tools(self):
        return self._tools


class TestToolResult:
    def test_tool_result_fields(self):
        r = ToolResult(tool_name="t", output={"x": 1}, confidence=0.9, processing_time_ms=50.0)
        assert r.tool_name == "t"
        assert r.confidence == 0.9
        assert r.error is None

    def test_tool_result_with_error(self):
        r = ToolResult(tool_name="t", output=None, confidence=0.0,
                       processing_time_ms=0.0, error="failed")
        assert r.error == "failed"


class TestAgentContext:
    def test_context_defaults(self):
        ctx = AgentContext()
        assert ctx.documents == []
        assert ctx.results == {}
        assert ctx.trace == []
        assert ctx.verification_id  

    def test_add_trace(self):
        ctx = AgentContext()
        ctx.add_trace("agent1", "tool1", 0.85, "ok")
        assert len(ctx.trace) == 1
        assert ctx.trace[0]["agent"] == "agent1"
        assert ctx.trace[0]["confidence"] == 0.85

    def test_get_result_returns_none_for_missing(self):
        ctx = AgentContext()
        assert ctx.get_result("nonexistent") is None

    def test_get_result_returns_stored_result(self):
        ctx = AgentContext()
        r = ToolResult(tool_name="t", output={}, confidence=0.9, processing_time_ms=0.0)
        ctx.results["myagent"] = r
        assert ctx.get_result("myagent") == r


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_stops_at_threshold(self):
        
        tools = [
            MockTool("fast_tool", confidence=0.9),   
            MockTool("slow_tool", confidence=0.95),  
        ]
        agent = MockAgent(tools, threshold=0.7)
        ctx = AgentContext()
        result = await agent.run(ctx)

        assert result.tool_name == "fast_tool"
        assert result.confidence == 0.9
        
        assert len(ctx.trace) == 1
        assert ctx.trace[0]["tool"] == "fast_tool"

    @pytest.mark.asyncio
    async def test_falls_back_to_next_tool(self):
        
        tools = [
            MockTool("weak_tool", confidence=0.4),
            MockTool("strong_tool", confidence=0.85),
        ]
        agent = MockAgent(tools, threshold=0.7)
        ctx = AgentContext()
        result = await agent.run(ctx)

        assert result.tool_name == "strong_tool"
        assert len(ctx.trace) == 2

    @pytest.mark.asyncio
    async def test_returns_best_when_no_tool_meets_threshold(self):
        
        tools = [
            MockTool("tool_a", confidence=0.3),
            MockTool("tool_b", confidence=0.5),
            MockTool("tool_c", confidence=0.4),
        ]
        agent = MockAgent(tools, threshold=0.8)
        ctx = AgentContext()
        result = await agent.run(ctx)

        assert result.tool_name == "tool_b"
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_handles_tool_exceptions_gracefully(self):
        
        tools = [
            MockTool("crash_tool", confidence=0.0, error="Connection refused"),
            MockTool("backup_tool", confidence=0.8),
        ]
        agent = MockAgent(tools, threshold=0.7)
        ctx = AgentContext()
        result = await agent.run(ctx)

        assert result.tool_name == "backup_tool"
        assert any("ERROR" in entry["note"] for entry in ctx.trace)

    @pytest.mark.asyncio
    async def test_result_stored_in_context(self):
        
        tools = [MockTool("winner", confidence=0.9)]
        agent = MockAgent(tools, threshold=0.7)
        ctx = AgentContext()
        await agent.run(ctx)

        assert "mock_agent" in ctx.results
        assert ctx.results["mock_agent"].tool_name == "winner"
