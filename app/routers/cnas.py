from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.cnas import (
    CNASVerifyRequest,
    CNASVerifyResponse,
)
from app.services.cnas_scraper import scrape_cnas
from app.dependencies import verify_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cnas", tags=["cnas"], dependencies=[Depends(verify_api_key)]
)


@router.post(
    "/verify",
    response_model=CNASVerifyResponse,
    summary="Verify Employer Attestation",
    description="Verifies the validity of a CNAS employer affiliation attestation using the certificate number and employer ID.",
)
async def verify_cnas(request: CNASVerifyRequest):
    logger.info(
        f"Received CNAS verification request for attestation {request.attestation_number}"
    )

    try:
        result = await scrape_cnas(
            attestation_number=request.attestation_number,
            employer_number=request.employer_number,
        )

        if result["status"] == "rate_limited":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Service is rate limited. Please try again later.",
                headers={"Retry-After": "5"},
            )

        return result

    except Exception as e:
        logger.error(f"Unexpected error in verify_cnas: {e}")
        return {
            "valid": None,
            "status": "error",
            "error": str(e),
            "attempts": 0,
            "processing_time_ms": 0,
        }


