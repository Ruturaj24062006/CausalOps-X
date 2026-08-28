from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class FeatureVector(BaseModel):
    feature_id: str
    timestamp: str
    window_start: str
    window_end: str
    window_size: str
    service_id: Optional[str]
    namespace: Optional[str]
    pod: Optional[str]
    feature_version: str = "v1"
    features: Dict[str, Any]
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
