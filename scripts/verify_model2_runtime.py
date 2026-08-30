import os
import sys
import json
import torch
import numpy as np

sys.path.append(os.path.abspath(r"d:\Projects\CausalOps X\services\stream-processing-service"))
from app.model2_v9_engine import Model2V9Engine

def run_tests():
    engine = Model2V9Engine()
    
    # 1. Model & Scaler load
    assert engine.model is not None, "Model failed to load natively"
    assert engine.scaler is not None, "Scaler failed to load natively"
    assert not engine.model.training, "Model is not in eval boundary"
    
    # 2. Check systems
    assert engine.system_node_contracts["Online Boutique"]["node_count"] == 17
    assert engine.system_node_contracts["Sock Shop"]["node_count"] == 16
    assert engine.system_node_contracts["Train Ticket"]["node_count"] == 69
    
    # 3. Create mock telemetry correctly mimicking 32 features
    mock_telemetry = {}
    for node in engine.system_node_contracts["Online Boutique"]["ordered_services"]:
        mock_telemetry[node] = {f: 1.0 for f in engine.expected_features}
        
    mock_edges = [
        {"source_service": "frontend", "target_service": "adservice"},
        {"source_service": "frontend", "target_service": "cartservice"}
    ]
    mock_edge_metrics = {
        ("frontend", "adservice"): {f: 2.0 for f in engine.expected_edges},
        ("frontend", "cartservice"): {f: 3.0 for f in engine.expected_edges}
    }
    
    res = engine.predict("Online Boutique", mock_telemetry, mock_edges, mock_edge_metrics)
    assert res["status"] == "SUCCESS", f"Failed: {res}"
    assert "predicted_root_cause_service" in res
    assert 0 <= res["node_index"] < 17
    
    print("Runtime evaluation test sequence entirely passed!")
    
if __name__ == "__main__":
    run_tests()
