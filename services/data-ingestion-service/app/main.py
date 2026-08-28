from fastapi import FastAPI, Response
import asyncio
from .metrics_ingestion import ingest_prometheus_metrics
from .events_ingestion import start_event_watcher
from .kafka_client import publisher

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Start background tasks
    asyncio.create_task(ingest_prometheus_metrics())
    start_event_watcher()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    producer = publisher.get_producer()
    if producer:
        return {"status": "ready", "kafka": "connected"}
    return Response(content='{"status": "not ready"}', status_code=503)
