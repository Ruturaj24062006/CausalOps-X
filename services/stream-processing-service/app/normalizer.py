import datetime
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def normalize_event(topic: str, raw_data: dict) -> Optional[dict]:
    try:
        if not isinstance(raw_data, dict):
            raise ValueError(f"Payload not JSON dict: {type(raw_data)}")
        
        source = raw_data.get("source")
        if not source:
            if topic == "raw.metrics":
                source = "prometheus"
            elif topic == "raw.logs":
                source = "fluent-bit"
            elif topic == "raw.events":
                source = "kubernetes"
            else:
                source = "unknown"

        normalized = {
            "event_id": raw_data.get("event_id") or str(uuid.uuid4()),
            "timestamp": raw_data.get("timestamp") or (datetime.datetime.utcnow().isoformat() + "Z"),
            "processing_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source": source,
            "service_id": raw_data.get("service_id"),
            "namespace": raw_data.get("namespace"),
            "pod": raw_data.get("pod"),
            "container": raw_data.get("container"),
            "event_type": raw_data.get("event_type") or "telemetry",
            "payload": raw_data.get("payload") or raw_data
        }
        
        # specifically normalize deeply isolated fluent-bit native metadata safely
        if source == "fluent-bit" and "kubernetes" in raw_data:
            k8s_meta = raw_data["kubernetes"]
            if isinstance(k8s_meta, dict):
                normalized["namespace"] = normalized.get("namespace") or k8s_meta.get("namespace_name")
                normalized["pod"] = normalized.get("pod") or k8s_meta.get("pod_name")
                normalized["container"] = normalized.get("container") or k8s_meta.get("container_name")

        return normalized
    except Exception as e:
        logger.error(f"Failed to normalize payload from {topic}: {e} -> Payload: {str(raw_data)[:200]}")
        return None
