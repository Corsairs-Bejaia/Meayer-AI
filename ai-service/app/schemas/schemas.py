from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TemplateField(BaseModel):
    field_name: str
    field_type: str = "text"
    is_required: bool = True
    description: Optional[str] = None
    validation_regex: Optional[str] = None
    position_hint: Optional[Dict[str, float]] = None


class Template(BaseModel):
    slug: str
    doc_type: str
    name: str
    layer: str = "L1"
    fields: List[TemplateField]


class PipelineDoc(BaseModel):
    file_url: Optional[str] = None
    image_base64: Optional[str] = None
    doc_type_hint: Optional[str] = None


class PipelineRequest(BaseModel):
    documents: List[PipelineDoc]
    templates: List[Template] = []
    kyc_result: Optional[Dict[str, Any]] = None
    cnas_result: Optional[Dict[str, Any]] = None
    casnos_result: Optional[Dict[str, Any]] = None
    required_docs: List[str] = []
    stream: bool = False
    trust_threshold: float = 80.0


class AgentTraceEntry(BaseModel):
    timestamp: float
    agent: str
    tool: str
    confidence: float
    note: Optional[str] = None


class PipelineResponse(BaseModel):
    verification_id: str
    results: Dict[str, Any]
    trace: List[AgentTraceEntry]
    processing_time_ms: float


class ExtractionResult(BaseModel):
    fields: Dict[str, Any]
    confidence: float


class AuthenticityCheck(BaseModel):
    tool: str
    passed: bool
    score: float
    details: Any


class AuthenticityResult(BaseModel):
    authenticity_score: float
    is_suspicious: bool
    checks: List[AuthenticityCheck]


class ConsistencyFlag(BaseModel):
    type: str
    check: str
    message: str


class ConsistencyResult(BaseModel):
    overall_consistent: bool
    consistency_score: float
    checks: List[Dict[str, Any]]
    flags: List[ConsistencyFlag]
    processing_time_ms: float
    trace: List[Dict[str, Any]] = []


class ScoreRequest(BaseModel):
    kyc_result: Optional[Dict[str, Any]] = None
    cnas_result: Optional[Dict[str, Any]] = None
    casnos_result: Optional[Dict[str, Any]] = None
    documents_submitted: List[str] = []
    required_docs: List[str] = []
    authenticity_results: Optional[Dict[str, Any]] = None
    consistency_result: Optional[Dict[str, Any]] = None
    trust_threshold: float = 80.0


class LayerScore(BaseModel):
    layer: str
    name: str
    score: float
    weight: float
    documents_submitted: List[str] = []
    documents_required: int = 1
    is_satisfied: bool
    details: Optional[str] = None


class ScoreResponse(BaseModel):
    score: float
    layer_scores: Dict[str, LayerScore]
    blockers: List[str]
    flags: List[Dict[str, Any]]
    documents_coverage: Dict[str, Any]
    decision: str
    threshold_used: float = 80.0
    trace: List[Dict[str, Any]] = []
