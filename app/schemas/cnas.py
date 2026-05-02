from pydantic import BaseModel, Field
from typing import Optional


class CNASVerifyRequest(BaseModel):
    attestation_number: str = Field(
        ...,
        alias="Numéro de l'attestation",
        pattern=r"^\d{2}/\d{7}$",
        description="The 10-digit attestation number (Format: XX/XXXXXXX)",
        examples=["25/1234567"],
    )
    employer_number: str = Field(
        ...,
        alias="Numéro de l'employeur",
        pattern=r"^\d{2}/\d{7}$",
        description="The 10-digit employer registration number (Format: XX/XXXXXXX)",
        examples=["16/0001234"],
    )

    model_config = {"populate_by_name": True}


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


class CNASEmployeeVerifyRequest(BaseModel):
    attestation_number: str = Field(
        ...,
        alias="Numéro de l'attestation",
        pattern=r"^\d{2}/\d{7}$",
        description="The 10-digit attestation number (Format: XX/XXXXXXX)",
        examples=["25/1234567"],
    )
    employer_number: str = Field(
        ...,
        alias="Numéro de l'employeur",
        pattern=r"^\d{2}/\d{7}$",
        description="The 10-digit employer registration number (Format: XX/XXXXXXX)",
        examples=["16/0001234"],
    )
    ssn: str = Field(
        ...,
        pattern=r"^\d{12}$",
        description="The 12-digit Social Security Number (NSS) of the employee",
        examples=["850101123456"],
    )

    model_config = {"populate_by_name": True}


class CNASEmployeeVerifyResponse(BaseModel):
    valid: Optional[bool]
    status: str
    employer_name: Optional[str] = None
    employee_found: Optional[bool] = None
    employee_name: Optional[str] = None
    attempts: int
    processing_time_ms: int
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
