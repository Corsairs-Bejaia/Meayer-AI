import time
import logging
import httpx
from fastapi import APIRouter, Depends

from app.agents.base import AgentContext
from app.agents.authenticity_agent import AuthenticityAgent
from app.dependencies import verify_api_key
from app.schemas.schemas import AuthenticityRequest, AuthenticityResponse, AuthenticityCheck

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/authenticity", tags=["authenticity"])
_agent = AuthenticityAgent()


@router.post("", response_model=AuthenticityResponse, summary="Verify Document Authenticity")
async def check_authenticity(
    request: AuthenticityRequest,
    _: str = Depends(verify_api_key),
):
    start = time.time()
    context = AgentContext()

    image_bytes = None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(request.file_url)
            resp.raise_for_status()
            image_bytes = resp.content
    except Exception as e:
        logger.error(f"Failed to fetch document: {e}")

    result = await _agent.run(context, image_bytes=image_bytes, doc_type=request.doc_type)
    output = result.output or {}
    elapsed = round((time.time() - start) * 1000, 1)

    checks = [
        AuthenticityCheck(
            check=c.get("check", ""),
            passed=c.get("passed", False),
            score=c.get("score", 0.0),
            details=c.get("details"),
        )
        for c in output.get("checks", [])
    ]

    return AuthenticityResponse(
        authenticity_score=output.get("authenticity_score", 0.0),
        is_suspicious=output.get("is_suspicious", True),
        checks=checks,
        processing_time_ms=elapsed,
        trace=context.trace,
    )
