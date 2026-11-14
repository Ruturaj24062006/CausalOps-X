from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import uuid

class EnrichedFeatureEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    processing_timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    source: str
    service_id: Optional[str] = None
    namespace: Optional[str] = None
    pod: Optional[str] = None
    container: Optional[str] = None
    event_type: str
    payload: Dict[str, Any]

class RecommendationAction(BaseModel):
    action: str
    score: float
    rank: int
    model4_score: Optional[float] = None
    model4_rank: Optional[int] = None
    model5_class: Optional[int] = None
    model5_label: Optional[str] = None
    model5_confidence: Optional[float] = None
    model5_probabilities: Optional[Dict[str, float]] = None
    expected_relevance: Optional[float] = None
    composite_score: Optional[float] = None
    composite_rank: Optional[int] = None
    explanation: Optional[str] = None

class RecommendationResponse(BaseModel):
    status: str
    reason: Optional[str] = None
    model: Optional[str] = None
    incident_id: Optional[str] = None
    root_cause_service: Optional[str] = None
    severity: Optional[float] = None
    timestamp: Optional[str] = None
    model5_status: Optional[str] = None
    formula_explanation: Optional[str] = None
    recommendations: Optional[List[RecommendationAction]] = None

class RecommendationRequest(BaseModel):
    root_cause_service: str
    severity: float
    telemetry: Optional[Dict[str, float]] = None

class Model4TestRequest(BaseModel):
    root_cause_service: str
    incident_severity: float
    features: Dict[str, float]

class Model5EvaluateRequest(BaseModel):
    incident_id: Optional[str] = "INC-TEST"
    root_cause_service: str
    incident_severity: float = 3.0
    candidate_actions: Optional[List[str]] = None
    telemetry: Optional[Dict[str, float]] = None
    model4_scores: Optional[Dict[str, float]] = None

class Model5ActionEvaluation(BaseModel):
    action: str
    model4_score: Optional[float] = None
    model5_class: int
    model5_label: str
    model5_confidence: float
    model5_probabilities: Dict[str, float]
    expected_relevance: float
    composite_score: float
    composite_rank: int
    explanation: str

class Model5EvaluateResponse(BaseModel):
    status: str
    incident_id: str
    root_cause_service: str
    incident_severity: float
    model5_status: str
    model_version: Optional[str] = None
    algorithm: Optional[str] = None
    evaluations: List[Model5ActionEvaluation]
    evaluation_timestamp: str
    execution_time_ms: float
    formula_explanation: str

class ActionApprovalRequest(BaseModel):
    incident_id: str
    action: str
    operator_id: Optional[str] = "operator-on-duty"
    notes: Optional[str] = None

class ActionApprovalResponse(BaseModel):
    status: str
    incident_id: str
    action: str
    operator_id: str
    approval_timestamp: str
    message: str
    requires_human_approval: bool = True
