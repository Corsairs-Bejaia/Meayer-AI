from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TemplateField(BaseModel):
    field_name: str
    field_type: str = "text"
    is_required: bool = False
    description: Optional[str] = None
    validation_regex: Optional[str] = None
    position_hint: Optional[Dict[str, float]] = None  


class Template(BaseModel):
    slug: str
    doc_type: str
    name: str
    fields: List[TemplateField] = []
    sample_image_url: Optional[str] = None


class DocumentInput(BaseModel):
    file_url: str
    doc_type_hint: Optional[str] = None
    template_slug: Optional[str] = None


class PipelineRequest(BaseModel):
    documents: List[DocumentInput]
    templates: List[Template] = []
    stream: bool = False
    kyc_result: Optional[Dict[str, Any]] = None
    cnas_result: Optional[Dict[str, Any]] = None
    required_docs: List[str] = []


class AgentTraceEntry(BaseModel):
    timestamp: float
    agent: str
    tool: str
    confidence: float
    note: str


class PipelineResponse(BaseModel):
    verification_id: str
    results: Dict[str, Any]
    trace: List[AgentTraceEntry]
    processing_time_ms: float


class ClassifyRequest(BaseModel):
    file_url: str
    available_templates: List[Template] = []


class ClassifyResponse(BaseModel):
    doc_type: Optional[str]
    matched_template_slug: Optional[str]
    confidence: float
    language: Optional[str]
    reasoning: Optional[str]
    tool_used: str
    trace: List[Dict[str, Any]] = []


class ExtractRequest(BaseModel):
    file_url: str
    doc_type: str = "document"
    template: Template


class ExtractResponse(BaseModel):
    extracted_fields: Dict[str, Any]
    raw_text: Optional[str]
    language_detected: Optional[str]
    extraction_method: str
    missing_required: List[str] = []
    processing_time_ms: float
    trace: List[Dict[str, Any]] = []


class AuthenticityRequest(BaseModel):
    file_url: str
    doc_type: Optional[str] = None


class AuthenticityCheck(BaseModel):
    check: str
    passed: bool
    score: float
    details: Optional[Any]


class AuthenticityResponse(BaseModel):
    authenticity_score: float
    is_suspicious: bool
    checks: List[AuthenticityCheck]
    processing_time_ms: float
    trace: List[Dict[str, Any]] = []


class ConsistencyRequest(BaseModel):
    documents: Dict[str, Dict[str, Any]]  


class ConsistencyFlag(BaseModel):
    type: str  
    check: str
    message: str


class ConsistencyResponse(BaseModel):
    overall_consistent: bool
    consistency_score: float
    checks: List[Dict[str, Any]]
    flags: List[ConsistencyFlag]
    processing_time_ms: float
    trace: List[Dict[str, Any]] = []


class ScoreRequest(BaseModel):
    kyc_result: Optional[Dict[str, Any]] = None
    cnas_result: Optional[Dict[str, Any]] = None
    documents_submitted: List[str] = []
    required_docs: List[str] = []
    authenticity_results: Optional[Dict[str, Any]] = None
    consistency_result: Optional[Dict[str, Any]] = None


class TierScore(BaseModel):
    score: float
    weight: float
    details: Any


class ScoreResponse(BaseModel):
    score: float
    tier_scores: Dict[str, TierScore]
    blockers: List[str]
    flags: List[Dict[str, Any]]
    documents_coverage: Dict[str, Any]
    decision: str
    trace: List[Dict[str, Any]] = []
