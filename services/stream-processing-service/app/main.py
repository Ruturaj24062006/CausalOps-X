from fastapi import FastAPI, Response
from .kafka_consumer import consumer_worker
from .kafka_producer import producer_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    consumer_worker.start()
    logger.info("Stream Processing Service started and consumer dispatched")

@app.on_event("shutdown")
async def shutdown_event():
    consumer_worker.stop()
    logger.info("Stream Processing Service gracefully shuttered")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    prod = producer_client.get_producer()
    if prod:
        return {"status": "ready", "kafka": "connected"}
    return Response(content='{"status": "not ready"}', status_code=503)
