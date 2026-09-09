import os
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pickle
import platform

# Device Config
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

class LSTM_VAE(nn.Module):
    def __init__(self, input_dim=20, hidden_dim=64, latent_dim=16, seq_len=20):
        super(LSTM_VAE, self).__init__()
        self.seq_len = seq_len
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        
        # Encoder
        self.encoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        
        # Decoder
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

def vae_loss(recon_x, x, mu, logvar):
    mse = nn.MSELoss(reduction='sum')(recon_x, x)
    kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    # Normalizing per sequence/timestep context dynamically if needed
    # but we simply divide by batch inside training loop later.
    return mse, kl

def scale_data(data, scaler):
    # data shape: (B, seq_len, num_features)
    B, S, F = data.shape
    flattened = data.reshape(-1, F)
    scaled = scaler.transform(flattened)
    return scaled.reshape(B, S, F)

def evaluate_model(model, loader):
    model.eval()
    mse_total = 0.0
    kl_total = 0.0
    mses = []
    with torch.no_grad():
        for batch in loader:
            x = batch[0].to(device)
            recon, mu, logvar = model(x)
            mse_val = nn.MSELoss(reduction='none')(recon, x).sum(dim=(1,2)).cpu().numpy()
            mse, kl = vae_loss(recon, x, mu, logvar)
            mse_total += mse.item()
            kl_total += kl.item()
            mses.extend(mse_val)
            
    B_TOTAL = len(loader.dataset)
    return mse_total / B_TOTAL, kl_total / B_TOTAL, np.array(mses)

def calculate_stats(arr):
    return {
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'P50': float(np.percentile(arr, 50)),
        'P75': float(np.percentile(arr, 75)),
        'P80': float(np.percentile(arr, 80)),
        'P85': float(np.percentile(arr, 85)),
        'P90': float(np.percentile(arr, 90)),
        'P92': float(np.percentile(arr, 92)),
        'P94': float(np.percentile(arr, 94)),
        'P95': float(np.percentile(arr, 95)),
        'P96': float(np.percentile(arr, 96)),
        'P97': float(np.percentile(arr, 97)),
        'P98': float(np.percentile(arr, 98)),
        'P99': float(np.percentile(arr, 99)),
        'P99_5': float(np.percentile(arr, 99.5))
    }

print("Loading curated datasets...")
data_dir = r"d:\Projects\CausalOps X\artifacts\feature_validation\model1_healthy_curation_v2"
train_npy = np.load(os.path.join(data_dir, "healthy_sequences_train.npy"))
val_npy = np.load(os.path.join(data_dir, "healthy_sequences_val.npy"))
test_npy = np.load(os.path.join(data_dir, "healthy_sequences_test.npy"))

print(f"Train Raw Shape: {train_npy.shape}")
print(f"Val Raw Shape: {val_npy.shape}")
print(f"Test Raw Shape: {test_npy.shape}")

# Pre-Scaler Check
if np.max(train_npy) > 5.0 or np.min(train_npy) < -5.0:
    print("Scaling: RAW - Applying existing production scaler.")
    scaler_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f\model1_20f_scaler.pkl"
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
        
    train_npy = scale_data(train_npy, scaler)
    val_npy = scale_data(val_npy, scaler)
    test_npy = scale_data(test_npy, scaler)
else:
    print("Scaling: ALREADY SCALED")

batch_size = 256
train_dataset = TensorDataset(torch.tensor(train_npy, dtype=torch.float32))
val_dataset = TensorDataset(torch.tensor(val_npy, dtype=torch.float32))
test_dataset = TensorDataset(torch.tensor(test_npy, dtype=torch.float32))

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Training Config
epochs = 100
patience = 10
lr = 0.001

model = LSTM_VAE().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=lr)

candidate_dir = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f_healthy_candidate"
os.makedirs(candidate_dir, exist_ok=True)
best_model_path = os.path.join(candidate_dir, "best_vae_model1_20f_healthy.pth")
final_model_path = os.path.join(candidate_dir, "final_vae_model1_20f_healthy.pth")

best_val_loss = float('inf')
patience_counter = 0
best_epoch = -1
best_val_elbo = 0
best_val_mse = 0

print("Training Candidate Model 1...")
# Record baseline validation for Old Model
old_model_path = r"d:\Projects\CausalOps X\models\anomaly_detection\model1_20f\best_vae_model1_20f.pth"
old_model = LSTM_VAE().to(device)
checkpoint = torch.load(old_model_path, map_location=device)
old_model.load_state_dict(checkpoint, strict=False)
old_val_mse, old_val_kl, old_val_scores = evaluate_model(old_model, val_loader)
old_test_mse, old_test_kl, old_test_scores = evaluate_model(old_model, test_loader)
old_val_stats = calculate_stats(old_val_scores)
print(f"Original Model Val MSE base: {old_val_stats['mean']:.4f}")

for epoch in range(1, epochs + 1):
    model.train()
    train_mse = 0.0
    train_kl = 0.0
    
    for batch in train_loader:
        x = batch[0].to(device)
        optimizer.zero_grad()
        recon, mu, logvar = model(x)
        mse, kl = vae_loss(recon, x, mu, logvar)
        loss = mse + kl
        loss.backward()
        optimizer.step()
        
        train_mse += mse.item()
        train_kl += kl.item()
        
    val_mse, val_kl, val_scores = evaluate_model(model, val_loader)
    val_loss = val_mse + val_kl
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_epoch = epoch
        best_val_elbo = val_loss # ELBO approximation
        best_val_mse = val_mse
        patience_counter = 0
        torch.save(model.state_dict(), best_model_path)
    else:
        patience_counter += 1
        
    if patience_counter >= patience:
        print(f"Early stopping at epoch {epoch}")
        break

torch.save(model.state_dict(), final_model_path)

# RELOAD BEST MODEL
model.load_state_dict(torch.load(best_model_path, map_location=device))
print("Best Valid Model reloaded.")

new_val_mse, new_val_kl, new_val_scores = evaluate_model(model, val_loader)
new_test_mse, new_test_kl, new_test_scores = evaluate_model(model, test_loader)

np.save(os.path.join(candidate_dir, "validation_errors.npy"), new_val_scores)

new_val_stats = calculate_stats(new_val_scores)
new_test_stats = calculate_stats(new_test_scores)
old_val_stats = calculate_stats(old_val_scores)
old_test_stats = calculate_stats(old_test_scores)

test_metrics = {
    'new_candidate': {
        'val_ELBO': new_val_mse + new_val_kl,
        'val_MSE': new_val_mse,
        'val_KL': new_val_kl,
        'test_ELBO': new_test_mse + new_test_kl,
        'test_MSE': new_test_mse,
        'test_KL': new_test_kl,
        'val_distribution': new_val_stats,
        'test_distribution': new_test_stats
    },
    'old_production': {
        'val_ELBO': old_val_mse + old_val_kl,
        'val_MSE': old_val_mse,
        'val_KL': old_val_kl,
        'val_distribution': old_val_stats,
        'test_distribution': old_test_stats
    },
    'best_epoch': best_epoch
}
with open(os.path.join(candidate_dir, "test_metrics.json"), 'w') as f:
    json.dump(test_metrics, f, indent=2)

print("Training finished.")
