import logging
import asyncio
import threading
from kubernetes import client, config, watch
from .config import KAFKA_EVENTS_TOPIC
from .kafka_client import publisher
from .models import NormalizedEvent

logger = logging.getLogger(__name__)

def watch_events_blocking():
    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception as e:
            logger.error(f"K8s config error: {e}")
            return

    v1 = client.CoreV1Api()
    w = watch.Watch()
    
    last_resource_version = None

    while True:
        try:
            stream = w.stream(
                v1.list_event_for_all_namespaces,
                resource_version=last_resource_version,
                timeout_seconds=60
            )
            for event in stream:
                obj = event['object']
                
                last_resource_version = obj.metadata.resource_version
                
                event_id = f"{obj.metadata.uid}-{obj.count}" if getattr(obj, "count", None) else obj.metadata.uid

                # Use last_timestamp or creation_timestamp as string
                if getattr(obj, "last_timestamp", None):
                    ts = obj.last_timestamp.isoformat()
                else:
                    ts = obj.metadata.creation_timestamp.isoformat()

                norm_event = NormalizedEvent(
                    event_id=event_id,
                    timestamp=ts,
                    source="kubernetes",
                    event_type="event",
                    namespace=obj.metadata.namespace,
                    pod=obj.involved_object.name if obj.involved_object.kind == 'Pod' else None,
                    resource=obj.involved_object.kind,
                    resource_name=obj.involved_object.name,
                    reason=obj.reason,
                    message=obj.message,
                    event_action=getattr(obj, "action", None),
                    event_type_kubernetes=obj.type,
                    first_timestamp=obj.first_timestamp.isoformat() if getattr(obj, "first_timestamp", None) else None,
                    last_timestamp=obj.last_timestamp.isoformat() if getattr(obj, "last_timestamp", None) else None,
                    count=getattr(obj, "count", None),
                    payload={
                        "resource": obj.involved_object.kind,
                        "resource_name": obj.involved_object.name,
                        "reason": obj.reason,
                        "message": obj.message,
                        "type": obj.type,
                        "action": getattr(obj, "action", None)
                    }
                )
                published = publisher.publish(KAFKA_EVENTS_TOPIC, norm_event.model_dump())
                if published:
                    logger.info(f"Published K8s Event: {event_id} - {obj.reason}")
        except Exception as e:
            logger.warning(f"Event watch error/timeout (restarting stream): {e}")
            import time
            time.sleep(5)

def start_event_watcher():
    t = threading.Thread(target=watch_events_blocking, daemon=True)
    t.start()
