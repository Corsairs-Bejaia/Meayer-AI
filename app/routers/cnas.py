from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.cnas import (
    CNASVerifyRequest,
    CNASVerifyResponse,
    CNASEmployeeVerifyRequest,
    CNASEmployeeVerifyResponse,
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


@router.post(
    "/verify-employee",
    response_model=CNASEmployeeVerifyResponse,
    summary="Verify Individual Employee",
    description="Verifies if an individual employee (by SSN) is registered under a specific employer and attestation.",
)
async def verify_cnas_employee(request: CNASEmployeeVerifyRequest):
    logger.info(
        f"Received CNAS employee verification request for SSN {request.ssn} in attestation {request.attestation_number}"
    )

    try:
        result = await scrape_cnas(
            attestation_number=request.attestation_number,
            employer_number=request.employer_number,
            ssn=request.ssn,
        )

        if result["status"] == "rate_limited":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Service is rate limited. Please try again later.",
                headers={"Retry-After": "5"},
            )

        return result

    except Exception as e:
        logger.error(f"Unexpected error in verify_cnas_employee: {e}")
        return {
            "valid": None,
            "status": "error",
            "error": str(e),
            "attempts": 0,
            "processing_time_ms": 0,
        }
