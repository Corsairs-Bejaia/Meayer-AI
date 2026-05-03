import time
import logging
from fastapi import APIRouter, Depends

from app.agents.base import AgentContext
from app.agents.scoring_agent import ScoringAgent
from app.dependencies import verify_api_key
from app.schemas.schemas import ScoreRequest, ScoreResponse, LayerScore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/score", tags=["score"])
_agent = ScoringAgent()


@router.post("", response_model=ScoreResponse, summary="Calculate Trust Score")
async def calculate_score(
    request: ScoreRequest,
    _: str = Depends(verify_api_key),
):
    start = time.time()
    context = AgentContext()

    if request.authenticity_results:
        from app.agents.base import ToolResult
        context.results["authenticity"] = ToolResult(
            tool_name="authenticity_aggregate",
            output=request.authenticity_results,
            confidence=request.authenticity_results.get("authenticity_score", 50.0) / 100.0,
            processing_time_ms=0.0,
        )
    if request.consistency_result:
        from app.agents.base import ToolResult
        context.results["consistency"] = ToolResult(
            tool_name="consistency_checks",
            output=request.consistency_result,
            confidence=request.consistency_result.get("consistency_score", 50.0) / 100.0,
            processing_time_ms=0.0,
        )

    result = await _agent.run(
        context,
        kyc_result=request.kyc_result,
        cnas_result=request.cnas_result,
        casnos_result=request.casnos_result,
        documents_submitted=request.documents_submitted,
        required_docs=request.required_docs,
        trust_threshold=request.trust_threshold,
    )

    output = result.output or {}
    round((time.time() - start) * 1000, 1)

    layer_scores = {}
    for k, v in output.get("layer_scores", {}).items():
        layer_scores[k] = LayerScore(
            layer=v.get("layer", k),
            name=v.get("name", k),
            score=v.get("score", 0.0),
            weight=v.get("weight", 0.0),
            documents_submitted=v.get("documents_submitted", []),
            documents_required=v.get("documents_required", 1),
            is_satisfied=v.get("is_satisfied", False),
            details=v.get("details"),
        )

    return ScoreResponse(
        score=output.get("score", 0.0),
        layer_scores=layer_scores,
        blockers=output.get("blockers", []),
        flags=output.get("flags", []),
        documents_coverage=output.get("documents_coverage", {}),
        decision=output.get("decision", "review"),
        trace=context.trace,
    )
