from pydantic import BaseModel, Field
from typing import Optional

class CNASVerifyRequest(BaseModel):
    attestation_number: str = Field(..., pattern=r"^\d{2}/\d{7}$", examples=["25/1234567"])
    employer_number: str = Field(..., pattern=r"^\d{2}/\d{7}$", examples=["16/0001234"])

class CNASVerifyResponse(BaseModel):
    valid: Optional[bool]
    status: str
    employer_name: Optional[str] = None
    attestation_status: Optional[str] = None
    raw_response: Optional[str] = None
    attempts: int
    processing_time_ms: int
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
