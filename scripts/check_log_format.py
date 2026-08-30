import json

IN_FILE = r"d:\Projects\CausalOps X\datasets\raw\historical_telemetry_dump.jsonl"

def print_log_samples():
    logs_found = 0
    with open(IN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                rec = json.loads(line)
                if rec.get("_kafka_topic") == "raw.logs" or rec.get("topic") == "raw.logs":
                    # Remove sensitive _kafka_topic to see the exact structure from Fluent Bit
                    topic = rec.pop("_kafka_topic", None)
                    rec.pop("_archive_timestamp", None)
                    print(f"--- LOG {logs_found + 1} ---")
                    print(f"Top-level keys: {list(rec.keys())}")
                    print(f"Content: {json.dumps(rec, indent=2)}")
                    logs_found += 1
                    if logs_found >= 3:
                        break
            except Exception:
                pass

if __name__ == "__main__":
    print_log_samples()
