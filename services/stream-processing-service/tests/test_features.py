import pytest
from app.features.metrics import extract_metric_features
from app.features.logs import extract_log_features
from app.features.events import extract_event_features
from app.features.windows import WindowManager
import time

def test_extract_metric_features():
    events = [
        {"payload": {"value": [1, "10.0"]}},
        {"payload": {"value": [2, "20.0"]}},
    ]
    feats = extract_metric_features(events)
    assert feats["metric_count"] == 2
    assert feats["metric_mean"] == 15.0
    assert feats["metric_min"] == 10.0

def test_extract_log_features():
    events = [
        {"payload": {"level": "error", "log": "db timeout"}},
        {"payload": {"level": "info", "log": "started"}},
    ]
    feats = extract_log_features(events)
    assert feats["log_count"] == 2
    assert feats["error_count"] == 1
    assert feats["unique_message_count"] == 2

def test_extract_event_features():
    events = [
        {"payload": {"type": "Warning", "reason": "FailedScheduling"}}
    ]
    feats = extract_event_features(events)
    assert feats["event_count"] == 1
    assert feats["warning_event_count"] == 1

def test_window_manager_determinism():
    mgr = WindowManager()
    e1 = {
        "service_id": "test-svc",
        "timestamp": "2026-08-23T00:00:01Z",
        "source": "kubernetes",
        "payload": {"type": "Warning"}
    }
    
    mgr.add_event(e1)
    
    # Force flush dynamically by mocking time manually bypassing time module bounds
    res = mgr.flush_expired(current_ts=int(time.time()) + 9000)
    assert len(res) == 3 # 1m, 5m, 15m windows
    for v in res:
        assert v.service_id == "test-svc"
        assert v.features["event_count"] == 1
