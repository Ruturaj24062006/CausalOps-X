import pytest
from app.models import NormalizedEvent

def test_normalized_event_schema_creation():
    event = NormalizedEvent(
        source="kubernetes",
        event_type="event",
        payload={"msg": "test"}
    )
    assert event.source == "kubernetes"
    assert event.event_type == "event"
    assert event.event_id is not None
    assert event.timestamp is not None

def test_kubernetes_event_custom_fields():
    event = NormalizedEvent(
        event_id="uid-123",
        source="kubernetes",
        event_type="event",
        reason="Started",
        message="Started container",
        event_action="action",
        event_type_kubernetes="Normal",
        count=1,
        payload={}
    )
    assert event.event_id == "uid-123"
    assert event.reason == "Started"
    assert event.count == 1
