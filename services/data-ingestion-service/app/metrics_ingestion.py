import asyncio
import httpx
import logging
from .config import PROMETHEUS_URL, KAFKA_METRICS_TOPIC
from .kafka_client import publisher
from .models import NormalizedEvent

logger = logging.getLogger(__name__)

async def ingest_prometheus_metrics():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{PROMETHEUS_URL}/api/v1/query?query=up")
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "success":
                    for result in data["data"]["result"]:
                        metric = result["metric"]
                        event = NormalizedEvent(
                            source="prometheus",
                            event_type="metric",
                            namespace=metric.get("namespace") or metric.get("kubernetes_namespace"),
                            pod=metric.get("pod") or metric.get("kubernetes_pod_name"),
                            payload=result
                        )
                        publisher.publish(KAFKA_METRICS_TOPIC, event.model_dump())
        except Exception as e:
            logger.error(f"Metrics ingestion error: {e}")
        
        await asyncio.sleep(15)
