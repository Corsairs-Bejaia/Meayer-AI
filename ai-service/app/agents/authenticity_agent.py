import asyncio
import logging
from typing import List, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.authenticity_tools import (
    ELATool, StampDetectorTool, SignatureDetectorTool,
    PhotocopyDetectorTool, MetadataAnalyzerTool, AIGenerationDetectorTool
)

logger = logging.getLogger(__name__)


class AuthenticityAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "authenticity"

    @property
    def tools(self) -> List[BaseTool]:
        return [
            ELATool(),
            StampDetectorTool(),
            SignatureDetectorTool(),
            PhotocopyDetectorTool(),
            MetadataAnalyzerTool(),
            AIGenerationDetectorTool(),
        ]

    def __init__(self):
        super().__init__(confidence_threshold=0.5)
        self._ela = ELATool()
        self._stamp = StampDetectorTool()
        self._signature = SignatureDetectorTool()
        self._photocopy = PhotocopyDetectorTool()
        self._metadata = MetadataAnalyzerTool()
        self._ai_detect = AIGenerationDetectorTool()

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        kwargs.get("image_bytes")

        quick_results = await asyncio.gather(
            self._stamp.execute(context, **kwargs),
            self._signature.execute(context, **kwargs),
            self._photocopy.execute(context, **kwargs),
            self._ai_detect.execute(context, **kwargs),
            return_exceptions=True,
        )

        ela_result = await self._ela.execute(context, **kwargs)

        ambiguous = any(
            isinstance(r, ToolResult) and r.confidence < 0.6
            for r in quick_results
        )
        metadata_result: Optional[ToolResult] = None
        if ambiguous:
            metadata_result = await self._metadata.execute(context, **kwargs)

        all_results = [r for r in quick_results if isinstance(r, ToolResult)]
        all_results.append(ela_result)
        if metadata_result:
            all_results.append(metadata_result)

        weights = {
            "ai_generation_detector": 0.35,
            "ela_analysis": 0.20,
            "stamp_detector": 0.20,
            "signature_detector": 0.15,
            "photocopy_detector": 0.10,
            "metadata_analyzer": 0.10,
        }

        weighted_sum = 0.0
        total_weight = 0.0
        checks_output = []

        for r in all_results:
            w = weights.get(r.tool_name, 0.1)
            weighted_sum += r.confidence * w
            total_weight += w
            checks_output.append({
                "tool": r.tool_name,
                "passed": r.confidence >= 0.6,
                "score": round(r.confidence * 100, 1),
                "details": r.output,
            })

        aggregate_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5
        authenticity_score = round(aggregate_confidence * 100, 1)
        is_suspicious = aggregate_confidence < 0.5

        for r in all_results:
            context.add_trace(self.name, r.tool_name, r.confidence, str(r.output))

        result = ToolResult(
            tool_name="authenticity_aggregate",
            output={
                "authenticity_score": authenticity_score,
                "is_suspicious": is_suspicious,
                "checks": checks_output,
            },
            confidence=aggregate_confidence,
            processing_time_ms=0.0,
        )

        context.results[self.name] = result
        return result
