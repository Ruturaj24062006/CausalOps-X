from fastapi import FastAPI, Response, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from .kafka_consumer import consumer_worker
from .kafka_producer import producer_client
import logging
from .model2_v9_engine import Model2V9Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stream Processing Service", version="1.0")

# Global engine instance mapping exactly to system startup
model2_engine = None

class RCARequest(BaseModel):
    system: str
    telemetry: Dict[str, Dict[str, float]]
    topology_edges: List[Dict[str, str]]
    edge_metrics: Dict[str, Dict[str, float]]

class RCAResponse(BaseModel):
    status: str
    predicted_root_cause_service: Optional[str] = None
    node_index: Optional[int] = None
    score: Optional[float] = None
    reason: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    global model2_engine
    consumer_worker.start()
    
    try:
        model2_engine = Model2V9Engine()
        logger.info("Model 2 V9 Engine securely initialized on startup.")
    except Exception as e:
        logger.error(f"Failed to initialize Model 2 V9 cleanly: {e}")
        model2_engine = None
        
    logger.info("Stream Processing Service started and consumer dispatched")

@app.on_event("shutdown")
async def shutdown_event():
    consumer_worker.stop()
    logger.info("Stream Processing Service gracefully shuttered")

@app.get("/health")
def health():
    m2_status = "ok" if model2_engine is not None else "failed"
    return {"status": "ok", "model2_engine": m2_status}

@app.get("/ready")
def ready():
    prod = producer_client.get_producer()
    if prod:
        return {"status": "ready", "kafka": "connected"}
    return Response(content='{"status": "not ready"}', status_code=503)

@app.post("/api/v1/rca/predict", response_model=RCAResponse)
def rca_predict(request: RCARequest):
    if not model2_engine:
        raise HTTPException(status_code=503, detail="Model 2 V9 Engine securely bypassed due to offline loading contexts")
        
    if not request.telemetry:
        return RCAResponse(status="FAILURE", reason="missing telemetry")
        
    if request.system not in ["Online Boutique", "Sock Shop", "Train Ticket"]:
        # Safe failure
        return RCAResponse(status="FAILURE", reason=f"unsupported application: {request.system}")
        
    try:
        # Tuple-convert edge metrics keys from string-based representations if needed
        # Format assumed: "(src, tgt)": { metrics... }
        parsed_edge_metrics = {}
        for edge_str, metrics in request.edge_metrics.items():
            if edge_str.startswith("(") and edge_str.endswith(")"):
                # Basic mock parsing for testing tuple key representation safely
                parts = edge_str.strip("()").replace("'", "").replace('"', "").replace(" ", "").split(",")
                if len(parts) == 2:
                    parsed_edge_metrics[(parts[0], parts[1])] = metrics
                    
        res = model2_engine.predict(
            system=request.system,
            raw_node_telemetry=request.telemetry,
            topology_edges=request.topology_edges,
            raw_edge_metrics=parsed_edge_metrics
        )
        
        if res.get("status") == "SUCCESS":
            return RCAResponse(
                status="SUCCESS",
                predicted_root_cause_service=res["predicted_root_cause_service"],
                node_index=res["node_index"],
                score=res["score"]
            )
        else:
            return RCAResponse(status="FAILURE", reason=res.get("reason", "inference failure"))
            
    except Exception as e:
        logger.error(f"Inference resolution explicitly failed: {e}")
        return RCAResponse(status="FAILURE", reason=str(e))
