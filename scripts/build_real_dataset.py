import sys
import os
import json
import csv
import datetime
from collections import defaultdict

# Add the stream-processing-service path so we can import its modules
sys.path.append(r"d:\Projects\CausalOps X\services\stream-processing-service")
from app.normalizer import normalize_event
from app.features.metrics import extract_metric_features
from app.features.logs import extract_log_features
from app.features.events import extract_event_features

# Group by (namespace, pod, service_id, window_start) -> [events]
windows = defaultdict(list)

print("Reading historical dump...")
line_count = 0
m_count = 0
l_count = 0
e_count = 0

with open(r"d:\Projects\CausalOps X\historical_telemetry_dump.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line_count += 1
        try:
            raw = json.loads(line)
        except Exception:
            continue
            
        topic = raw.get("_kafka_topic", "")
        # Remove topic before normalization to mimic raw ingress
        # But wait, normalize_event requires topic as first arg.
        if "_kafka_topic" in raw:
            del raw["_kafka_topic"]
        if "_archive_timestamp" in raw:
            del raw["_archive_timestamp"]
            
        norm = normalize_event(topic, raw)
        if not norm:
            continue
            
        source = norm.get("source")
        if source == "prometheus":
            m_count += 1
        elif source == "fluent-bit":
            l_count += 1
        elif source == "kubernetes":
            e_count += 1
            
        try:
            dt = datetime.datetime.fromisoformat(norm["timestamp"].replace("Z", "+00:00"))
            ts = int(dt.timestamp())
        except Exception:
            continue
            
        window_start = (ts // 60) * 60
        namespace = norm.get("namespace") or "unknown"
        pod = norm.get("pod") or "unknown"
        service_id = norm.get("service_id") or "default"
        
        # We must filter out "unknown" namespace/pods if they are too noisy, but model expects all valid topology items.
        windows[(namespace, pod, service_id, window_start)].append(norm)

print(f"Total lines read: {line_count}")
print(f"Metrics: {m_count}, Logs: {l_count}, Events: {e_count}")
print(f"Total groups (windows): {len(windows)}")
# Sort the keys chronologically
sorted_keys = sorted(windows.keys(), key=lambda x: x[3])

if sorted_keys:
    print(f"Earliest: {datetime.datetime.utcfromtimestamp(sorted_keys[0][3])}")
    print(f"Latest: {datetime.datetime.utcfromtimestamp(sorted_keys[-1][3])}")

feature_cols = [
    'metric_count', 'metric_mean', 'metric_std', 'metric_min', 'metric_max', 'metric_current',
    'log_count', 'error_count', 'warning_count', 'info_count', 'unique_error_count', 'unique_message_count',
    'event_count', 'warning_event_count', 'normal_event_count', 'failed_event_count',
    'unhealthy_event_count', 'unique_reason_count', 'unique_resource_count', 'pod_event_count'
]
headers = ["service_id", "namespace", "pod", "window_start", "window_end"] + feature_cols

out_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

print("Writing features CSV...")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    
    for (ns, pod, sid, w_start) in sorted_keys:
        events = windows[(ns, pod, sid, w_start)]
        
        m_events = [e for e in events if e.get("source") == "prometheus"]
        l_events = [e for e in events if e.get("source") == "fluent-bit"]
        e_events = [e for e in events if e.get("source") == "kubernetes"]
        
        m_feats = extract_metric_features(m_events)
        l_feats = extract_log_features(l_events)
        e_feats = extract_event_features(e_events)
        
        # Combine
        combined = {**m_feats, **l_feats, **e_feats}
        row = [
            sid, ns, pod,
            datetime.datetime.utcfromtimestamp(w_start).isoformat() + "Z",
            datetime.datetime.utcfromtimestamp(w_start + 60).isoformat() + "Z"
        ]
        for c in feature_cols:
            row.append(combined.get(c, 0))
        writer.writerow(row)

print("CSV Build Complete.")
