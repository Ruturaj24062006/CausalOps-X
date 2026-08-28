import pytest
from app.normalizer import normalize_event

def test_normalize_valid_event():
    raw = {"event_id": "1", "source": "fluent-bit", "payload": {"foo": "bar"}}
    norm = normalize_event("raw.logs", raw)
    assert norm["event_id"] == "1"
    assert norm["source"] == "fluent-bit"
    assert norm["payload"]["foo"] == "bar"
    assert "processing_timestamp" in norm

def test_normalize_malformed():
    assert normalize_event("raw.metrics", ["invalid", "list"]) is None

def test_normalize_source_inference():
    raw = {"event_id": "2", "payload": {}}
    norm = normalize_event("raw.events", raw)
    assert norm["source"] == "kubernetes"
