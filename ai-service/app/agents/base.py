from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Union
import time
import uuid

@dataclass
class ToolResult:
    tool_name: str
    output: Any
    confidence: float
    processing_time_ms: float
    error: Optional[str] = None

@dataclass
class AgentContext:
    verification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    documents: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, ToolResult] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)

    def get_result(self, agent_name: str) -> Optional[ToolResult]:
        return self.results.get(agent_name)

    def add_trace(self, agent_name: str, tool_name: str, confidence: float, note: str):
        self.trace.append({
            "timestamp": time.time(),
            "agent": agent_name,
            "tool": tool_name,
            "confidence": confidence,
            "note": note
        })

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        pass

class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def tools(self) -> List[BaseTool]:
        pass

    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        """Try tools in ranked order until confidence >= threshold."""
        best_result: Optional[ToolResult] = None
        
        for tool in self.tools:
            start_time = time.time()
            try:
                result = await tool.execute(context, **kwargs)
                processing_time = (time.time() - start_time) * 1000
                result.processing_time_ms = processing_time
                
                context.add_trace(self.name, tool.name, result.confidence, f"Executed tool {tool.name}")
                
                if result.confidence >= self.confidence_threshold:
                    context.results[self.name] = result
                    return result
                
                if not best_result or result.confidence > best_result.confidence:
                    best_result = result
                    
            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                context.add_trace(self.name, tool.name, 0.0, f"ERROR: {str(e)}")
                
        # If no tool met threshold, return the best one
        if best_result:
            context.results[self.name] = best_result
            return best_result
        
        return ToolResult(
            tool_name="none",
            output=None,
            confidence=0.0,
            processing_time_ms=0.0,
            error="All tools failed or no tools available"
        )
