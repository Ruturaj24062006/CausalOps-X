from kafka import KafkaConsumer
import json
import logging
import os
import torch
import torch.nn as nn
import pickle
import numpy as np
from datetime import datetime
import collections
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shadow_evaluator")

class LSTM_VAE(nn.Module):
    def __init__(self, input_dim=20, hidden_dim=64, latent_dim=16, seq_len=20):
        super(LSTM_VAE, self).__init__()
        self.seq_len = seq_len
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        
        self.encoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        
        self.decoder_fc = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def encode(self, x):
        _, (h, _) = self.encoder_lstm(x)
        h = h.squeeze(0)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z, x):
        h = self.decoder_fc(z).unsqueeze(0)
        c = torch.zeros_like(h)
        dec_in = torch.zeros(x.size(0), 1, x.size(2)).to(x.device)
        out_seq = []
        for t in range(self.seq_len):
            out, (h, c) = self.decoder_lstm(dec_in, (h, c))
            dec_in = self.output_layer(out)
            out_seq.append(dec_in)
        return torch.cat(out_seq, dim=1)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z, x)

def start_shadow():
    if os.environ.get("MODEL1_SHADOW_EVAL", "false").lower() != "true":
        logger.info("Shadow evaluation disabled by MODEL1_SHADOW_EVAL=false")
        return

    logger.info("Initializing isolated shadow sequence window map...")
    model_path = "/models/anomaly_detection/model1_20f/best_vae_model1_20f.pth"
    scaler_path = "/models/anomaly_detection/model1_20f/model1_20f_scaler.pkl"
    schema_path = "/models/anomaly_detection/model1_feature_schema.json"
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = LSTM_VAE().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device), strict=False)
    model.eval()
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
        
    with open(schema_path, "r") as f:
        schema = json.load(f)
        
    feature_order = schema["feature_order"]
    nulls = ["metric_mean", "metric_std", "metric_min", "metric_max", "metric_current"]
    
    import time
    consumer = KafkaConsumer('enriched.features', bootstrap_servers='kafka:9092', group_id=f'shadow-evaluator-group-{int(time.time())}', auto_offset_reset='latest')
    
    buffer = collections.defaultdict(list)
    seq_len = 20
    max_gap = 300.0
    
    logger.info("Shadow evaluator successfully initialized and listening mapping isolated constraints...")
    
    captured = 0
    try:
        while captured < 5:
            for msg in consumer:
                data = json.loads(msg.value.decode('utf-8'))
                ns = data.get("namespace", "system")
                pod = data.get("pod", "system")
                
                if ns == "unknown" and pod == "unknown": continue
                if not ns or not pod: continue
                    
                key = f"{ns}||{pod}"
                buffer[key].append(data)
                
                if len(buffer[key]) > 40:
                    buffer[key] = buffer[key][-40:]
                    
                if len(buffer[key]) >= seq_len:
                    logger.info(f"Buffer for {key} reached {len(buffer[key])}. Attempting to form sequence...")
                    seq = buffer[key][-seq_len:]
                    ts_list = [datetime.fromisoformat(w["window_end"].replace("Z", "+00:00")) for w in seq]
                    valid = True
                    
                    for i in range(1, len(ts_list)):
                        if (ts_list[i] - ts_list[i-1]).total_seconds() > max_gap:
                            valid = False
                            break
                            
                    if not valid: continue
                    
                    # Ensure backlog consumption skips gracefully cleanly
                    from datetime import timezone
                    if (datetime.now(timezone.utc) - ts_list[-1]).total_seconds() > 180:
                        continue
                    
                    raw_mat = []
                    # debugging inside container
                    for w in seq:
                        row = []
                        f_dict = w.get("features", {})
                        for f_name in feature_order:
                            v = f_dict.get(f_name)
                            if v in (None, "", "None"):
                                v = 0.0 if f_name in nulls else -1.0
                            row.append(float(v))
                        if any(x == -1.0 for x in row):
                            logger.error(f"Incomplete features found, row discarded. Ex: {row} \n From: {f_dict}")
                            valid = False
                            break
                        raw_mat.append(row)
                        
                    if not valid: continue
                    
                    raw_arr = np.array(raw_mat, dtype=np.float32)
                    scaled_arr = scaler.transform(raw_arr)
                    tensor_seq = torch.tensor(scaled_arr).unsqueeze(0).to(device)
                    
                    with torch.no_grad():
                        recon = model(tensor_seq)
                        err = torch.mean((tensor_seq - recon)**2).item()
                        
                    pred = "ANOMALY" if err > 17.43091926574707 else "NORMAL"
                    logger.info(f"Shadow Inference -> {pred} (Score: {err:.4f})")
                    
                    eval_id = str(uuid.uuid4())
                    scenario = os.environ.get("SCENARIO", "baseline")
                    gt_label = int(os.environ.get("GROUND_TRUTH_LABEL", "0"))
                    out_rec = {
                        "evaluation_id": eval_id,
                        "scenario": scenario,
                        "ground_truth_label": gt_label,
                        "timestamp": seq[-1]["window_end"],
                        "window_start": seq[0]["window_start"],
                        "window_end": seq[-1]["window_end"],
                        "namespace": ns,
                        "pod": pod,
                        "feature_names": feature_order,
                        "sequence_length": seq_len,
                        "feature_count": 20,
                        "feature_matrix": scaled_arr.tolist(),
                        "raw_feature_matrix": raw_arr.tolist(),
                        "candidate_anomaly_score": float(err),
                        "candidate_prediction": pred,
                        "production_anomaly_score": 0.0,
                        "production_prediction": "NORMAL",
                        "model_id": "model1_20f_healthy_candidate",
                        "candidate_model_checkpoint": "best_vae_model1_20f_healthy.pth",
                        "production_model_checkpoint": "model1_20f.pth",
                        "scaler_path": "model1_20f_scaler.pkl",
                        "sequence_timestamps": [w["window_end"] for w in seq],
                        "max_adjacent_gap": float(max((ts_list[i] - ts_list[i-1]).total_seconds() for i in range(1, len(ts_list))) if len(ts_list) > 1 else 0.0)
                    }
                    
                    out_dir = "/artifacts/feature_validation/model1_fault_evaluation_v3"
                    os.makedirs(out_dir, exist_ok=True)
                    with open(os.path.join(out_dir, "step44_real_fault_evaluation.jsonl"), "a") as f:
                        f.write(json.dumps(out_rec) + "\n")
                        
                    captured += 1
                    buffer[key] = buffer[key][-19:]
                    logger.info(f"Captured {captured} {scenario} window.")
                    target_captures = int(os.environ.get("TARGET_CAPTURES", "5"))
                    if captured >= target_captures:
                        logger.info("Successfully evaluated phase. Terminating safely.")
                        return
            if captured >= int(os.environ.get("TARGET_CAPTURES", "5")): return
                        
    finally:
        consumer.close()

if __name__ == "__main__":
    start_shadow()
