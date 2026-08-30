import json
import os

OUT_FILE = r"d:\Projects\CausalOps X\datasets\raw\historical_telemetry_dump.jsonl"

def verify():
    total = 0
    metrics_count = 0
    logs_count = 0
    events_count = 0
    
    unique_services = set()
    unique_namespaces = set()
    unique_pods = set()
    malformed = 0
    
    earliest = None
    latest = None
    
    try:
        with open(OUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                total += 1
                try:
                    record = json.loads(line)
                    topic = record.get("_kafka_topic", "")
                    
                    if topic == "raw.metrics": metrics_count += 1
                    elif topic == "raw.logs": logs_count += 1
                    elif topic == "raw.events": events_count += 1
                    
                    sid = record.get("service_id")
                    ns = record.get("namespace")
                    pod = record.get("pod")
                    ts = record.get("timestamp")
                    
                    if sid: unique_services.add(sid)
                    if ns: unique_namespaces.add(ns)
                    if pod: unique_pods.add(pod)
                    
                    if ts:
                        if earliest is None or ts < earliest:
                            earliest = ts
                        if latest is None or ts > latest:
                            latest = ts
                            
                except Exception:
                    malformed += 1
    except FileNotFoundError:
        print("Archive file not found. Ensure the consumer has captured data.")
        return

    size = os.path.getsize(OUT_FILE)
    
    print("============================================================")
    print("TELEMETRY DUMP VERIFICATION")
    print("============================================================")
    print(f"total records: {total}")
    print(f"raw.metrics count: {metrics_count}")
    print(f"raw.logs count: {logs_count}")
    print(f"raw.events count: {events_count}")
    print(f"earliest timestamp: {earliest}")
    print(f"latest timestamp: {latest}")
    print(f"unique services: {len(unique_services)}")
    print(f"unique namespaces: {len(unique_namespaces)}")
    print(f"unique pods: {len(unique_pods)}")
    print(f"malformed records: {malformed}")
    print(f"file size: {size / 1024:.2f} KB")
    print("============================================================")

if __name__ == "__main__":
    verify()
