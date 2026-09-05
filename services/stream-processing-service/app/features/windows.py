import time
import uuid
import datetime
from typing import Dict, List, Any
import logging
from .schema import FeatureVector
from .metrics import extract_metric_features
from .logs import extract_log_features
from .events import extract_event_features

logger = logging.getLogger(__name__)

class WindowManager:
    def __init__(self):
        # group_by_key -> { window_size -> { window_start_time -> [events] } }
        self.state = {}
        self.window_sizes = {"1m": 60, "5m": 300, "15m": 900}
        
        for k, v in self.window_sizes.items():
            if not isinstance(v, (int, float)):
                raise TypeError(f"Invalid window configuration for {k}: Expected numeric seconds, got {type(v)}")
                
        self.lock = __import__('threading').Lock()
        
    def add_event(self, event: dict):
        service_id = event.get("service_id") or "default"
        namespace = event.get("namespace") or "unknown"
        pod = event.get("pod") or "unknown"
        key = f"{service_id}|{namespace}|{pod}"
        
        try:
            dt = datetime.datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            ts = int(dt.timestamp())
        except Exception:
            ts = int(time.time())
            
        with self.lock:
            if key not in self.state:
                self.state[key] = {ws: {} for ws in self.window_sizes}
                
            for ws_name, ws_sec in self.window_sizes.items():
                window_start = (ts // ws_sec) * ws_sec
                if window_start not in self.state[key][ws_name]:
                    self.state[key][ws_name][window_start] = []
                self.state[key][ws_name][window_start].append(event)
                
    def flush_expired(self, current_ts: int = None) -> List[FeatureVector]:
        if current_ts is None:
            current_ts = int(time.time())
            
        vectors = []
        with self.lock:
            for key, windows in list(self.state.items()):
                service_id, namespace, pod = key.split("|")
                for ws_name, window_dict in list(windows.items()):
                    ws_sec = self.window_sizes.get(ws_name, 0)
                    buffer = 5
                    w_starts = list(window_dict.keys())
                    for w_start in w_starts:
                        if current_ts > w_start + ws_sec + buffer:
                            events = windows[ws_name].pop(w_start)
                            vec = self._build_feature_vector(
                                events, ws_name, w_start, w_start + ws_sec,
                                service_id, namespace, pod
                            )
                            vectors.append(vec)
        return vectors
        
    def _build_feature_vector(self, events, ws_name, w_start, w_end, service_id, namespace, pod):
        metric_events = [e for e in events if e.get("source") == "prometheus"]
        log_events = [e for e in events if e.get("source") == "fluent-bit"]
        k8s_events = [e for e in events if e.get("source") == "kubernetes"]
        
        m_feats = extract_metric_features(metric_events)
        l_feats = extract_log_features(log_events)
        e_feats = extract_event_features(k8s_events)
        
        features = {**m_feats, **l_feats, **e_feats}
        
        return FeatureVector(
            feature_id=str(uuid.uuid4()),
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            window_start=datetime.datetime.fromtimestamp(w_start, tz=datetime.timezone.utc).isoformat(),
            window_end=datetime.datetime.fromtimestamp(w_end, tz=datetime.timezone.utc).isoformat(),
            window_size=ws_name,
            service_id=None if service_id == "default" else service_id,
            namespace=None if namespace == "unknown" else namespace,
            pod=None if pod == "unknown" else pod,
            feature_version="v1",
            features=features
        )
