import time
import logging
import httpx
from fastapi import APIRouter, Depends

from app.agents.base import AgentContext
from app.agents.ocr_agent import OCRAgent
from app.agents.extraction_agent import ExtractionAgent
from app.dependencies import verify_api_key
from app.schemas.schemas import ExtractRequest, ExtractResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extract", tags=["extract"])
_ocr_agent = OCRAgent()
_extract_agent = ExtractionAgent()


@router.post("", response_model=ExtractResponse, summary="Extract Fields from a Document")
async def extract_fields(
    request: ExtractRequest,
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

    fields = [f.model_dump() for f in request.template.fields]

    # Run OCR first to build context
    await _ocr_agent.run(context, image_bytes=image_bytes)
    ocr_result = context.get_result("ocr")
    raw_text = (ocr_result.output or {}).get("text") if ocr_result else None
    lang = (ocr_result.output or {}).get("language") if ocr_result else None

    # Run extraction
    result = await _extract_agent.run(
        context,
        image_bytes=image_bytes,
        fields=fields,
        doc_type=request.doc_type,
    )

    output = result.output or {}
    elapsed = round((time.time() - start) * 1000, 1)

    return ExtractResponse(
        extracted_fields=output.get("extracted_fields", {}),
        raw_text=raw_text,
        language_detected=lang,
        extraction_method=output.get("extraction_method", "hybrid"),
        missing_required=output.get("missing_required", []),
        processing_time_ms=elapsed,
        trace=context.trace,
    )
