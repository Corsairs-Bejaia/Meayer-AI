import time
import logging
import httpx
from fastapi import APIRouter, Depends

from app.agents.base import AgentContext
from app.agents.classifier_agent import ClassifierAgent
from app.dependencies import verify_api_key
from app.schemas.schemas import ClassifyRequest, ClassifyResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/classify", tags=["classify"])
_agent = ClassifierAgent()


@router.post("", response_model=ClassifyResponse, summary="Classify a Single Document")
async def classify_document(
    request: ClassifyRequest,
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

    templates = [t.model_dump() for t in request.available_templates]
    result = await _agent.run(context, image_bytes=image_bytes, available_templates=templates)

    output = result.output or {}
    return ClassifyResponse(
        doc_type=output.get("doc_type"),
        matched_template_slug=output.get("matched_template_slug") or output.get("matched_template"),
        confidence=result.confidence,
        language=output.get("language"),
        reasoning=output.get("reasoning"),
        tool_used=result.tool_name,
        trace=context.trace,
    )
