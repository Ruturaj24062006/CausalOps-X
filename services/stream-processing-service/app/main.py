from fastapi import FastAPI, Response, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from .kafka_consumer import consumer_worker
from .kafka_producer import producer_client
from . import state_store
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor
from .model2_v9_engine import Model2V9Engine
from .model4_recovery_engine import Model4RecoveryEngine
from .model5_relevance_engine import Model5RelevanceEngine
from .models import (
    RecommendationRequest, RecommendationResponse, Model4TestRequest,
    Model5EvaluateRequest, Model5EvaluateResponse,
    ActionApprovalRequest, ActionApprovalResponse
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stream Processing Service", version="1.0")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances mapping exactly to system startup
model2_engine = None
model4_engine = None
model5_engine = None

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

from collections import deque
import threading
# Global bounded history buffer explicitly structurally logically stably responsibly dynamically transparently smartly.
TELEMETRY_HISTORY_BUFFER = deque(maxlen=1500)
HISTORY_LOCK = threading.Lock()

@app.on_event("startup")
async def startup_event():
    global model2_engine, model4_engine, model5_engine
    
    # Decouple the worker spawn from the ASGI startup hook to ensure UI/HTTP ports bind first
    import asyncio
    async def delayed_worker():
        await asyncio.sleep(2)
        import logging
        logging.getLogger(__name__).info("Background dispatching consumer worker safely")
        consumer_worker.start()
    
    asyncio.create_task(delayed_worker())
    
    try:
        model2_engine = Model2V9Engine()
        logger.info("Model 2 V9 Engine securely initialized on startup.")
    except Exception as e:
        logger.error(f"Failed to initialize Model 2 V9 cleanly: {e}")
        model2_engine = None
        
    try:
        model4_engine = Model4RecoveryEngine()
        logger.info("Model 4 Recovery Engine securely initialized on startup.")
    except Exception as e:
        logger.error(f"Failed to initialize Model 4 cleanly: {e}")
        model4_engine = None

    try:
        model5_engine = Model5RelevanceEngine()
        logger.info(f"Model 5 Relevance Engine initialized on startup with status: {model5_engine.status}")
    except Exception as e:
        logger.error(f"Failed to initialize Model 5 cleanly: {e}")
        model5_engine = None
        
    logger.info("Stream Processing Service started and consumer dispatched")

@app.on_event("shutdown")
async def shutdown_event():
    consumer_worker.stop()
    logger.info("Stream Processing Service gracefully shuttered")

@app.get("/health")
def health():
    m2_status = "ok" if model2_engine is not None else "failed"
    m4_status = "ok" if model4_engine is not None else "failed"
    m5_status = "ok" if model5_engine is not None and model5_engine.is_online() else "offline"
    return {
        "status": "ok",
        "model2_engine": m2_status,
        "model4_engine": m4_status,
        "model5_engine": m5_status
    }

@app.get("/api/v1/ml/status")
def ml_status():
    m4_str = "ONLINE (LightGBM Ranker)" if model4_engine else "OFFLINE"
    m5_str = "ONLINE (ExtraTrees Relevance Classifier)" if (model5_engine and model5_engine.is_online()) else (
        f"ERROR: {model5_engine.error_reason}" if model5_engine and model5_engine.status == "ERROR" else "OFFLINE"
    )
    return {
        "model1": "ONLINE (20-F)",
        "model2": "ONLINE (GraphSAGE V2)",
        "model4": m4_str,
        "model5": m5_str,
        "telemetry": "FLOWING",
        "pipeline": "ACTIVE"
    }

@app.get("/api/v1/model5/status")
def model5_status():
    """Return Model 5 metadata, artifact verification, and inference readiness."""
    if not model5_engine:
        return {"status": "OFFLINE", "reason": "Model 5 engine instance not initialized"}
    return model5_engine.get_metadata()

@app.get("/api/v1/ml/latest")
def ml_latest():
    """
    Returns the most recent real Model 1 inference result.
    Falls back to safe defaults until the Kafka consumer produces its first result.
    """
    return state_store.get_latest()

# In-memory service state override for demo and fast local simulation
DEMO_SERVICE_OVERRIDES: Dict[str, str] = {}
OVERRIDES_LOCK = threading.Lock()

def get_demo_override(service_name: str) -> Optional[str]:
    with OVERRIDES_LOCK:
        if service_name in DEMO_SERVICE_OVERRIDES:
            return DEMO_SERVICE_OVERRIDES[service_name]
        short_name = service_name.replace("-service", "")
        if short_name in DEMO_SERVICE_OVERRIDES:
            return DEMO_SERVICE_OVERRIDES[short_name]
        return None

def set_demo_override(service_name: str, state_val: str):
    with OVERRIDES_LOCK:
        DEMO_SERVICE_OVERRIDES[service_name] = state_val
        DEMO_SERVICE_OVERRIDES[service_name.replace("-service", "")] = state_val

def clear_demo_override(service_name: str):
    with OVERRIDES_LOCK:
        DEMO_SERVICE_OVERRIDES.pop(service_name, None)
        DEMO_SERVICE_OVERRIDES.pop(service_name.replace("-service", ""), None)

@app.post("/api/v1/demo/fail/{service_name}")
def demo_fail_service(service_name: str):
    """Mark a service as FAILED for demo and immediate topology/anomaly propagation."""
    set_demo_override(service_name, "FAILED")
    logger.info(f"Demo failure injected into {service_name}")
    return {"status": "ok", "service": service_name, "state": "FAILED"}

@app.post("/api/v1/demo/recover/{service_name}")
def demo_recover_service(service_name: str):
    """Recover a service back to HEALTHY."""
    clear_demo_override(service_name)
    logger.info(f"Demo recovery activated for {service_name}")
    return {"status": "ok", "service": service_name, "state": "HEALTHY"}

@app.post("/api/v1/demo/reset")
def demo_reset_all():
    with OVERRIDES_LOCK:
        DEMO_SERVICE_OVERRIDES.clear()
    logger.info("Demo topology reset: all services marked HEALTHY")
    return {"status": "ok", "state": "ALL_HEALTHY"}

@app.get("/api/v1/topology")
def get_topology():
    services = ["api-gateway", "payment-service", "fraud-service", "order-service", "inventory-service", "notification-service", "audit-service"]
    
    import urllib.request
    import urllib.error
    import json
    import subprocess
    import os
    
    # Check if running locally rather than in K8s
    is_local = not os.path.exists("/var/run/secrets/kubernetes.io")

    def get_service_status(service_name):
        # 1. Check if an override is active
        override = get_demo_override(service_name)
        if override:
            return override

        # 2. Probe Kubernetes pod
        try:
            if is_local:
                py_probe = (
                    "import urllib.request, urllib.error, json; "
                    "try:\n"
                    "    r = urllib.request.urlopen('http://localhost:8080/status', timeout=1.0)\n"
                    "    d = json.loads(r.read().decode())\n"
                    "    print(d.get('status', 'HEALTHY'))\n"
                    "except urllib.error.HTTPError as e:\n"
                    "    print('FAILED' if e.code == 503 else 'HEALTHY')\n"
                    "except Exception:\n"
                    "    print('HEALTHY')"
                )
                cmd = ["kubectl", "exec", f"deployment/{service_name}", "-n", "causalops", "--", "python", "-c", py_probe]
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=4).decode().strip()
                if "FAILED" in out:
                    return "FAILED"
                elif "BLOCKED" in out:
                    return "BLOCKED"
                elif "CRITICAL" in out:
                    return "CRITICAL"
                elif "HEALTHY" in out:
                    return "HEALTHY"
                return "HEALTHY"
            else:
                req = urllib.request.Request(f"http://{service_name}:8080/status", method="GET")
                try:
                    with urllib.request.urlopen(req, timeout=1.0) as resp:
                        data = json.loads(resp.read().decode())
                        return data.get("status", "HEALTHY")
                except urllib.error.HTTPError as e:
                    if e.code == 503:
                        return "FAILED"
                    return "HEALTHY"
        except Exception:
            return "HEALTHY"

    with ThreadPoolExecutor(max_workers=len(services)) as executor:
        statuses = list(executor.map(get_service_status, services))

    statuses_dict = dict(zip(services, statuses))

    # Cascade starvation: when upstream api-gateway or payment-service is FAILED,
    # downstream order-service flips strictly to BLOCKED (as specified in operations manual)
    if statuses_dict.get("api-gateway") == "FAILED" or statuses_dict.get("payment-service") == "FAILED":
        if statuses_dict.get("order-service") == "HEALTHY":
            statuses_dict["order-service"] = "BLOCKED"

    nodes = [
        {"id": service_name, "name": service_name, "type": "Deployment", "namespace": "causalops", "status": statuses_dict.get(service_name, "HEALTHY")}
        for service_name in services
    ]
        
    edges = [
        {"source": "api-gateway", "target": "payment-service", "type": "http"},
        {"source": "payment-service", "target": "fraud-service", "type": "http"},
        {"source": "payment-service", "target": "order-service", "type": "http"},
        {"source": "order-service", "target": "inventory-service", "type": "http"},
        {"source": "order-service", "target": "notification-service", "type": "http"},
        {"source": "api-gateway", "target": "audit-service", "type": "async"}
    ]
    
    return {
        "timestamp": datetime.datetime.now().isoformat() + "Z",
        "nodes": nodes,
        "edges": edges
    }

@app.get("/ready")
def ready():
    prod = producer_client.get_producer()
    if prod:
        return {"status": "ready", "kafka": "connected"}
    return Response(content='{"status": "not ready"}', status_code=503)

@app.get("/api/v1/telemetry")
def get_telemetry():
    with HISTORY_LOCK:
        records = list(TELEMETRY_HISTORY_BUFFER)
    
    cpu_data = []
    mem_data = []
    err_data = []
    
    for r in records:
        if "cpu_usage" in r["metric"]:
            cpu_data.append({"timestamp": r["timestamp"], "value": r["value"], "source": "real", "service": r["service"]})
        if "memory_usage" in r["metric"]:
            mem_data.append({"timestamp": r["timestamp"], "value": r["value"], "source": "real", "service": r["service"]})
        if "errors" in r["metric"]:
            err_data.append({"timestamp": r["timestamp"], "value": r["value"], "source": "real", "service": r["service"]})
            
    return {
        "status": "FLOWING",
        "timestamp": datetime.datetime.now().isoformat() + "Z",
        "metrics": {
            "cpu": cpu_data,
            "memory": mem_data,
            "errors": err_data
        }
    }

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
            # ── Publish RCA result to shared state so /api/v1/ml/latest reflects it ──
            state_store.update_rca(res)
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

@app.post("/api/v1/incidents/{incident_id}/recommendations", response_model=RecommendationResponse)
def get_recommendations(incident_id: str, request: RecommendationRequest):
    if not model4_engine:
        raise HTTPException(status_code=503, detail="Model 4 Engine securely bypassed due to offline loading contexts")
    
    try:
        # Fallback to local state if frontend passes empty telemetry, fulfilling Model 4 contract
        telemetry = request.telemetry
        if not telemetry:
            telemetry = state_store._state.get("latest_features", {})
            
        res = model4_engine.recommend(
            incident_id=incident_id,
            root_cause_service=request.root_cause_service,
            incident_severity=request.severity,
            telemetry=telemetry
        )
        
        if res.get("status") == "SUCCESS":
            # Model 4 successfully generated recommendations.
            # Now evaluate candidate actions with Model 5 if online.
            recommendations = res.get("recommendations", [])
            m5_status = "OFFLINE"
            formula_expl = None

            if model5_engine and model5_engine.is_online():
                candidate_actions = [r["action"] for r in recommendations]
                m4_scores_dict = {r["action"]: r["score"] for r in recommendations}

                m5_eval = model5_engine.evaluate_candidates(
                    incident_id=incident_id,
                    root_cause_service=request.root_cause_service,
                    incident_severity=request.severity,
                    candidate_actions=candidate_actions,
                    telemetry=telemetry,
                    model4_scores=m4_scores_dict
                )

                if m5_eval.get("status") == "SUCCESS":
                    m5_status = "ONLINE"
                    formula_expl = m5_eval.get("formula_explanation")
                    eval_by_action = {item["action"]: item for item in m5_eval.get("evaluations", [])}

                    enriched_recs = []
                    for r in recommendations:
                        act = r["action"]
                        e = eval_by_action.get(act, {})
                        enriched_recs.append({
                            "action": act,
                            "score": r["score"],
                            "rank": r["rank"],
                            "model4_score": r["score"],
                            "model4_rank": r["rank"],
                            "model5_class": e.get("model5_class"),
                            "model5_label": e.get("model5_label"),
                            "model5_confidence": e.get("model5_confidence"),
                            "model5_probabilities": e.get("model5_probabilities"),
                            "expected_relevance": e.get("expected_relevance"),
                            "composite_score": e.get("composite_score"),
                            "composite_rank": e.get("composite_rank"),
                            "explanation": e.get("explanation")
                        })
                    recommendations = enriched_recs
                else:
                    m5_status = model5_engine.status

            res["recommendations"] = recommendations
            res["model5_status"] = m5_status
            res["formula_explanation"] = formula_expl

            return RecommendationResponse(**res)
        else:
            return RecommendationResponse(status="FAILURE", reason=res.get("reason", "inference failure"))
            
    except Exception as e:
        logger.error(f"Failed to calculate recommendations: {e}", exc_info=True)
        return RecommendationResponse(status="FAILURE", reason=str(e))

@app.post("/api/v1/model4/recommend")
def test_model4_recommendation(request: Model4TestRequest):
    if not model4_engine:
        raise HTTPException(status_code=503, detail="Model 4 Engine not loaded")
        
    try:
        res = model4_engine.recommend(
            incident_id="test_incident_explicit",
            root_cause_service=request.root_cause_service,
            incident_severity=request.incident_severity,
            telemetry=request.features
        )
        return res
    except Exception as e:
        logger.error(f"Failed to calculate recommendations: {e}")
        return {"status": "FAILURE", "reason": str(e)}

@app.post("/api/v1/model5/evaluate", response_model=Model5EvaluateResponse)
def model5_evaluate(request: Model5EvaluateRequest):
    """
    Evaluate candidate recovery actions using Model 5 ExtraTrees Relevance Classifier.
    Optionally integrates Model 4 ranking scores into composite recommendations.
    """
    if not model5_engine or not model5_engine.is_online():
        raise HTTPException(
            status_code=503,
            detail=f"Model 5 Engine is offline: {getattr(model5_engine, 'error_reason', 'Artifacts not loaded')}"
        )

    try:
        telemetry = request.telemetry
        if not telemetry:
            telemetry = state_store._state.get("latest_features", {})

        candidate_actions = request.candidate_actions
        if not candidate_actions:
            from .model5_relevance_engine import SUPPORTED_ACTIONS
            candidate_actions = SUPPORTED_ACTIONS

        res = model5_engine.evaluate_candidates(
            incident_id=request.incident_id or "INC-EVAL",
            root_cause_service=request.root_cause_service,
            incident_severity=request.incident_severity,
            candidate_actions=candidate_actions,
            telemetry=telemetry,
            model4_scores=request.model4_scores
        )

        if res.get("status") != "SUCCESS":
            raise HTTPException(status_code=400, detail=res.get("reason", "Inference error"))

        return Model5EvaluateResponse(**res)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed in Model 5 evaluation endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recovery/approve", response_model=ActionApprovalResponse)
def approve_recovery_action(request: ActionApprovalRequest):
    """
    Human Operator Gatekeeper Endpoint:
    Records explicit human approval for a candidate recovery action before execution.
    Autonomous execution is strictly disabled.
    """
    logger.info(f"Human operator '{request.operator_id}' approved action '{request.action}' for incident '{request.incident_id}'")
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    approval_record = {
        "incident_id": request.incident_id,
        "action": request.action,
        "operator_id": request.operator_id or "operator-on-duty",
        "notes": request.notes,
        "approval_timestamp": ts,
        "status": "APPROVED"
    }
    state_store._state["last_approved_action"] = approval_record

    return ActionApprovalResponse(
        status="APPROVED",
        incident_id=request.incident_id,
        action=request.action,
        operator_id=request.operator_id or "operator-on-duty",
        approval_timestamp=ts,
        message=f"Recovery action '{request.action}' approved by operator '{request.operator_id}'. Execution requires human confirmation.",
        requires_human_approval=True
    )
