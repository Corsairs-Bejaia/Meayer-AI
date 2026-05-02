import time
import logging
from fastapi import APIRouter, Depends

from app.agents.base import AgentContext
from app.agents.consistency_agent import ConsistencyAgent
from app.dependencies import verify_api_key
from app.schemas.schemas import ConsistencyRequest, ConsistencyResponse, ConsistencyFlag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/consistency", tags=["consistency"])
_agent = ConsistencyAgent()


@router.post("", response_model=ConsistencyResponse, summary="Cross-Document Consistency Check")
async def check_consistency(
    request: ConsistencyRequest,
    _: str = Depends(verify_api_key),
):
    start = time.time()
    context = AgentContext()

    result = await _agent.run(context, documents=request.documents)
    output = result.output or {}
    elapsed = round((time.time() - start) * 1000, 1)

    flags = [
        ConsistencyFlag(
            type=f.get("type", "info"),
            check=f.get("check", ""),
            message=f.get("message", ""),
        )
        for f in output.get("flags", [])
    ]

    return ConsistencyResponse(
        overall_consistent=output.get("overall_consistent", False),
        consistency_score=output.get("consistency_score", 0.0),
        checks=output.get("checks", []),
        flags=flags,
        processing_time_ms=elapsed,
        trace=context.trace,
    )
