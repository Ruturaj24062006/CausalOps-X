from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import datetime
import uuid

class NormalizedEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    source: str
    service_id: Optional[str] = None
    namespace: Optional[str] = None
    pod: Optional[str] = None
    container: Optional[str] = None
    event_type: str
    resource: Optional[str] = None
    resource_name: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None
    event_action: Optional[str] = None
    event_type_kubernetes: Optional[str] = None
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    count: Optional[int] = None
    payload: Dict[str, Any]
