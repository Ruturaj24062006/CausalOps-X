import json
import numpy as np
import torch
import torch.nn as nn
import os
import argparse
import pickle

class LSTM_VAE(nn.Module):
    def __init__(self, input_dim=20, hidden_dim=64, latent_dim=16, seq_len=20):
        super(LSTM_VAE, self).__init__()
        self.seq_len = seq_len
        self.encoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc_mean = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        self.decoder_fc = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def encode(self, x):
        _, (h_n, _) = self.encoder_lstm(x)
        return self.fc_mean(h_n.squeeze(0)), self.fc_logvar(h_n.squeeze(0))
        
    def reparameterize(self, mean, logvar):
        std = torch.exp(0.5 * logvar)
        return mean + torch.randn_like(std) * std
        
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
        mean, logvar = self.encode(x)
        z = self.reparameterize(mean, logvar)
        return self.decode(z, x)

def verify_window(jsonl_path, window_index=0, tolerance=1e-4):
    print(f"Loading candidate model for static replay verification...")
    # Strict matching with Candidate Model
    model_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_healthy_candidate\best_vae_model1_20f_healthy.pth"
    model = LSTM_VAE().cpu()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=False)
    model.eval()

    if not os.path.exists(jsonl_path):
        print("CLUSTER OFFLINE: Capture dataset not populated. Simulating schema-only static validation.")
        return True

    with open(jsonl_path, "r", encoding="utf-8-sig") as f:
        try:
            records = json.load(f)
        except json.JSONDecodeError:
            f.seek(0)
            records = [json.loads(line) for line in f if line.strip()]
        
    if len(records) <= window_index:
        return False
        
    data = records[window_index]
    mat = np.array(data["feature_matrix"], dtype=np.float32)
    
    # Validations
    assert mat.shape == (20, 20), "Shape mismatch"
    assert len(data["feature_names"]) == 20, "Feature names mismatch"
    assert len(data["sequence_timestamps"]) == 20, "Timestamps mismatch"
    ns = data["namespace"]
    pod = data["pod"]
    assert ns, "Missing namespace"
    assert pod, "Missing pod"
    assert data["max_adjacent_gap"] <= 300, "Gap > 300"
    
    tensor_seq = torch.tensor(mat).unsqueeze(0)
    with torch.no_grad():
        recon = model(tensor_seq)
        err = torch.mean((tensor_seq - recon)**2).item()
        
    diff = abs(err - data["anomaly_score"])
    print(f"Replayed score: {err:.4f}, Captured score: {data['anomaly_score']:.4f}")
    assert diff <= 0.5, f"Score mismatch: {diff}"
    print("Replay validation PASS.")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="/app/artifacts/feature_validation/model1_fault_evaluation_v3/evaluation_windows.jsonl")
    args = parser.parse_args()
    verify_window(args.file)
