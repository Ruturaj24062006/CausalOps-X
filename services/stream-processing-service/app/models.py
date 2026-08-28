from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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
