import os
import json
import logging
import pickle
import numpy as np
import torch
import torch.nn as nn
from typing import Any
logger = logging.getLogger(__name__)

# Try purely dynamic PyG import to prevent hard crash if pyg is absent locally
try:
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False
    logger.warning("torch_geometric not available locally. Inference offline mode ONLY.")


class Model2V9Corrected(nn.Module):
    def __init__(
        self,
        node_input_dim=32,
        edge_input_dim=5,
        hidden_dim=128,
        dropout=0.2
    ):
        super().__init__()
        if not PYG_AVAILABLE:
            raise ImportError("torch_geometric required for Model2V9Corrected")
            
        self.conv1 = GCNConv(node_input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.score_head = nn.Linear(hidden_dim, 1)

    def forward(self, data):
        x = data.x
        edge_index = data.edge_index
        
        # GCNConv -> ReLU
        x = self.conv1(x, edge_index)
        x = torch.relu(x)
        
        # GCNConv -> ReLU
        x = self.conv2(x, edge_index)
        x = torch.relu(x)
        
        # GCNConv -> score
        x = self.conv3(x, edge_index)
        
        # Score header
        scores = self.score_head(x)
        return scores


class Model2V9Engine:
    def __init__(
        self, 
        model_dir=r"d:\Projects\CausalOps X\models\root_cause_analysis",
        contract_dir=r"d:\Projects\CausalOps X\artifacts\model2\v9_source_recovery"
    ):
        self.model_dir = model_dir
        self.contract_dir = contract_dir
        self.scaler = None
        self.model = None
        
        self.node_mapping_path = os.path.join(self.contract_dir, "v9_exact_node_mapping.json")
        self.scaler_path = os.path.join(self.model_dir, "model2_v9_step35_training_only_scaler.pkl")
        self.ckpt_path = os.path.join(self.model_dir, "model2_v9_best_per_node_model.pt")
        
        self.system_node_contracts = {}
        self.expected_features = [
            "cpu__mean", "cpu__std", "cpu__min", "cpu__max",
            "mem__mean", "mem__std", "mem__min", "mem__max",
            "diskio__mean", "diskio__std", "diskio__min", "diskio__max",
            "socket__mean", "socket__std", "socket__min", "socket__max",
            "workload__mean", "workload__std", "workload__min", "workload__max",
            "error__mean", "error__std", "error__min", "error__max",
            "latency-50__mean", "latency-50__std", "latency-50__min", "latency-50__max",
            "latency-90__mean", "latency-90__std", "latency-90__min", "latency-90__max"
        ]
        
        self.expected_edges = [
            "call_count", "mean_duration", "std_duration", "error_rate", "p90_duration"
        ]
        
        self._load_artifacts()

    def _load_artifacts(self):
        # 1. Load Node Contract
        if os.path.exists(self.node_mapping_path):
            with open(self.node_mapping_path, "r") as f:
                contract = json.load(f)
                if "mappings" in contract:
                    self.system_node_contracts = contract["mappings"]
        
        # 2. Load Scaler
        if os.path.exists(self.scaler_path):
            with open(self.scaler_path, "rb") as f:
                self.scaler = pickle.load(f)
                
        # 3. Load Checkpoint
        if os.path.exists(self.ckpt_path) and PYG_AVAILABLE:
            ckpt = torch.load(self.ckpt_path, map_location="cpu")
            self.model = Model2V9Corrected()
            self.model.load_state_dict(ckpt)
            self.model.eval()
            
    def _validate_telemetry(self, telemetry_data: list):
        if not telemetry_data:
            raise ValueError("Empty telemetry array")
            
    def build_node_features(self, system: str, telemetry_dict: dict) -> np.ndarray:
        if system not in self.system_node_contracts:
            raise ValueError(f"System completely unsupported by trained mappings: {system}")
            
        contract = self.system_node_contracts[system]
        n_nodes = contract["node_count"]
        
        # Explicit Array matching the fixed dimension (Nx32)
        node_features = np.zeros((n_nodes, 32), dtype=np.float32)
        
        ordered_services = contract["ordered_services"]
        
        for i, service in enumerate(ordered_services):
            # Enforce mapping lookup safely
            if service in telemetry_dict:
                service_telemetry = telemetry_dict[service]
                for f_idx, feature_name in enumerate(self.expected_features):
                    if feature_name in service_telemetry:
                        val = service_telemetry[feature_name]
                        if val is None or not np.isfinite(val):
                            raise ValueError(f"Non-finite missing value for feature {feature_name}")
                        node_features[i, f_idx] = float(val)
                    else:
                        raise ValueError(f"Missing required metric tracking field {feature_name} for service {service}")
            else:
                raise ValueError(f"Missing total telemetry context for known service {service}")
                
        return node_features
        
    def build_graph(self, system: str, node_features: np.ndarray, topology_edges: list, edge_metrics: dict) -> Any:
        if not PYG_AVAILABLE:
            return None
            
        contract = self.system_node_contracts[system]
        service_to_node = contract["service_to_node"]
        
        # 1. Edge indexing
        edge_pairs = []
        edge_attr_list = []
        
        for edge in topology_edges:
            src_str = edge.get("source_service")
            target_str = edge.get("target_service")
            
            if src_str not in service_to_node or target_str not in service_to_node:
                continue
                
            src_idx = service_to_node[src_str]
            tgt_idx = service_to_node[target_str]
            pair_key = (src_str, target_str)
            
            if pair_key in edge_metrics:
                metrics = edge_metrics[pair_key]
                row = []
                for e_feat in self.expected_edges:
                    val = metrics.get(e_feat, 0.0)
                    row.append(float(val))
                    
                edge_pairs.append([src_idx, tgt_idx])
                edge_attr_list.append(row)
                
        # Tensor conversion strictly identical to Kaggle
        x = torch.tensor(node_features, dtype=torch.float32)
        
        if len(edge_pairs) == 0:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 5), dtype=torch.float32)
        else:
            edge_index = torch.tensor(np.asarray(edge_pairs, dtype=np.int64).T, dtype=torch.long)
            edge_attr = torch.tensor(np.asarray(edge_attr_list, dtype=np.float32), dtype=torch.float32)
            
        # Data representation
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
        return data

    def predict(self, system: str, raw_node_telemetry: dict, topology_edges: list, raw_edge_metrics: dict):
        if not PYG_AVAILABLE or self.model is None or self.scaler is None:
            return {"status": "INFERENCE_FAILURE", "reason": "Missing PyTorch Geometric or Critical Artifacts"}
            
        try:
            # 1. Feature construction
            node_features = self.build_node_features(system, raw_node_telemetry)
            
            # 2. Scaler execution (TRANSFORM ONLY)
            x_scaled = self.scaler.transform(node_features)
            
            # 3. Graph generation
            graph_data = self.build_graph(system, x_scaled, topology_edges, raw_edge_metrics)
            
            # 4. Inference execution natively
            with torch.no_grad():
                scores = self.model(graph_data)
                
            # 5. Argmax prediction mapped backward to strings
            scores = scores.flatten().numpy()
            predicted_idx = int(np.argmax(scores))
            
            ordered_services = self.system_node_contracts[system]["ordered_services"]
            predicted_service = ordered_services[predicted_idx]
            
            return {
                "status": "SUCCESS",
                "predicted_root_cause_service": predicted_service,
                "node_index": predicted_idx,
                "score": float(scores[predicted_idx]),
                "all_scores": scores.tolist()
            }
            
        except Exception as e:
            return {"status": "FAILURE", "reason": str(e)}

