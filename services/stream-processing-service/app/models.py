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

class RecommendationResponse(BaseModel):
    status: str
    reason: Optional[str] = None
    model: Optional[str] = None
    incident_id: Optional[str] = None
    root_cause_service: Optional[str] = None
    severity: Optional[float] = None
    timestamp: Optional[str] = None
    recommendations: Optional[List[RecommendationAction]] = None

class RecommendationRequest(BaseModel):
    root_cause_service: str
    severity: float
    telemetry: Dict[str, float]

class Model4TestRequest(BaseModel):
    root_cause_service: str
    incident_severity: float
    features: Dict[str, float]
