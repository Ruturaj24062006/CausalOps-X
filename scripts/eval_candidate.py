import subprocess
import json
import os
from collections import defaultdict
from datetime import datetime
import numpy as np
import torch
import torch.nn as nn
import pickle

print("Extracting features from Kafka...")
cmd = "kubectl exec -n causalops kafka-0 -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic enriched.features --from-beginning --timeout-ms 20000"
res = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
lines = res.strip().split('\n')

raw_features = []
for line in lines:
    try:
        if line.strip():
            raw_features.append(json.loads(line))
    except Exception:
        pass

print(f"Extracted {len(raw_features)} feature rows from Kafka.")

eval_path = r'd:\Projects\CausalOps X\artifacts\feature_validation\model1_fault_evaluation_v2\dataset.json'
with open(eval_path, 'r') as f:
    eval_data = json.load(f)

# Sort kafka features chronologically
raw_features.sort(key=lambda x: x['window_start'])

groups = defaultdict(list)
for r in raw_features:
    groups[f"{r.get('namespace', '')}||{r.get('pod', '')}"].append(r)

eval_mapping = {}
for w in eval_data:
    uid = f"{w['namespace']}||{w['pod']}||{w['window_end']}"
    eval_mapping[uid] = w

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
        x_recon = self.decode(z, x)
        return x_recon, mu, logvar

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
candidate_model = LSTM_VAE().to(device)
candidate_model.load_state_dict(torch.load(r'd:\Projects\CausalOps X\models\anomaly_detection\model1_20f_healthy_candidate\best_vae_model1_20f_healthy.pth', map_location=device))
candidate_model.eval()

with open(r'd:\Projects\CausalOps X\models\anomaly_detection\model1_20f\model1_20f_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

print("Mapping independent evaluation dataset windows to candidate inferences...")
results = []
missing = 0

for pod_key, rows in groups.items():
    if len(rows) < 20: continue
    
    for i in range(len(rows) - 20 + 1):
        seq = rows[i:i+20]
        end_time = seq[-1]['window_end']
        ns, p = pod_key.split("||", 1)
        uid = f"{ns}||{p}||{end_time}"
        
        if uid in eval_mapping:
            eval_window = eval_mapping[uid]
            
            # Predict
            feats = []
            valid = True
            for r in seq:
                if 'features' in r and len(r['features']) == 20:
                    feats.append(r['features'])
                else:
                    valid = False
            if not valid: continue
            
            mat = np.array(feats, dtype=np.float32)
            # Scaling RAW evaluation data appropriately
            mat_scaled = scaler.transform(mat)
            tensor_seq = torch.tensor(mat_scaled).unsqueeze(0).to(device)
            
            with torch.no_grad():
                recon, mu, logvar = candidate_model(tensor_seq)
                mse = nn.MSELoss(reduction='sum')(recon, tensor_seq).item()
                
            results.append({
                'ground_truth_label': eval_window['ground_truth_label'],
                'fault_id': eval_window['fault_id'],
                'anomaly_score': mse,
                'candidate_anomaly': mse
            })

if len(results) == 0:
    print("CRITICAL MATCHING FAILURE: No windows mapped.")
else:
    print(f"Mapped {len(results)}/{len(eval_data)} evaluation windows successfully.")
    
out_dir = r'd:\Projects\CausalOps X\artifacts\feature_validation\model1_healthy_candidate_eval'
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'mapped_eval.json'), 'w') as f:
    json.dump(results, f, indent=2)
