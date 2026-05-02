from fastapi import APIRouter, Depends, status, HTTPException
from app.dependencies import verify_api_key

router = APIRouter(
    tags=["stubs"],
    dependencies=[Depends(verify_api_key)]
)

@router.post("/api/cnas/verify-employee", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def verify_cnas_employee():
    return {"status": "not_implemented", "message": "Verify individual employee status is not yet implemented."}

@router.post("/api/mesrs/verify-diploma", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def verify_mesrs_diploma():
    return {"status": "not_implemented", "message": "MESRS diploma verification is not yet implemented."}

@router.post("/api/ordre-medecins/verify", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def verify_ordre_medecins():
    return {"status": "not_implemented", "message": "Ordre National des Médecins verification is not yet implemented."}
