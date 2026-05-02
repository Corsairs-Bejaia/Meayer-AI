from fastapi import Header, HTTPException, status
from app.config import settings


async def verify_api_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return x_internal_api_key
