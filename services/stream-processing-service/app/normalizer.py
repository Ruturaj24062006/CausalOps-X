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

        ts_val = raw_data.get("timestamp") or raw_data.get("time")
        if not ts_val and raw_data.get("@timestamp"):
            try:
                ts_val = datetime.datetime.utcfromtimestamp(raw_data["@timestamp"]).isoformat() + "Z"
            except Exception:
                pass
        if not ts_val:
            ts_val = datetime.datetime.utcnow().isoformat() + "Z"
            
        payload_dict = raw_data.get("payload", {})
        if not isinstance(payload_dict, dict): payload_dict = {}

        # Default mapping using dynamic robust extraction natively resolving nesting
        namespace_val = raw_data.get("namespace")
        pod_val = raw_data.get("pod")
        
        if source == "prometheus":
            m_dict = payload_dict.get("metric", {})
            namespace_val = namespace_val or m_dict.get("kubernetes_namespace") or m_dict.get("namespace")
            pod_val = pod_val or m_dict.get("kubernetes_pod_name") or m_dict.get("pod")

        normalized = {
            "event_id": raw_data.get("event_id") or str(uuid.uuid4()),
            "timestamp": ts_val,
            "processing_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source": source,
            "service_id": raw_data.get("service_id"),
            "namespace": namespace_val,
            "pod": pod_val,
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

        if source == "kubernetes":
            io = payload_dict.get("involvedObject", raw_data.get("involvedObject", {}))
            if isinstance(io, dict) and io.get("kind") == "Pod":
                normalized["pod"] = normalized.get("pod") or io.get("name")
                normalized["namespace"] = normalized.get("namespace") or io.get("namespace")

        # Explicitly diagnose loss securely organically natively locally securely tracking observability
        if not normalized["pod"]:
            logger.debug(f"Missing pod identity for {source}")

        return normalized
    except Exception as e:
        logger.error(f"Failed to normalize payload from {topic}: {e} -> Payload: {str(raw_data)[:200]}")
        return None
