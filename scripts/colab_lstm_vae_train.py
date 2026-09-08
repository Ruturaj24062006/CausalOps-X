"""
Google Colab Training Package for CausalOps Model 1 (20-Feature LSTM-VAE)
Execute this script natively inside your Google Colab workspace containing GPUs.
Ensure you upload `train_seqs.npy` and `val_seqs.npy` to the Colab runtime environment before execution.
"""

import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import random

# Core Configuration
CONFIG = {
    "input_dim": 20,
    "hidden_dim": 64,
    "latent_dim": 16,
    "sequence_length": 20,
    "batch_size": 256,
    "epochs": 100,
    "learning_rate": 0.001,
    "patience": 10,
    "seed": 42
}

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class LSTM_VAE(nn.Module):
    def __init__(self, input_dim, hidden_dim, latent_dim, seq_len):
        super(LSTM_VAE, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.seq_len = seq_len
        
        # Encoder Mapping
        self.encoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc_mean = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        
        # Decoder Mapping
        self.fc_decode = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def encode(self, x):
        _, (h_n, _) = self.encoder_lstm(x)
        h_n = h_n.squeeze(0)
        mean = self.fc_mean(h_n)
        logvar = self.fc_logvar(h_n)
        return mean, logvar
        
    def reparameterize(self, mean, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mean + eps * std
        
    def decode(self, z, x):
        h_0 = self.fc_decode(z).unsqueeze(0)
        c_0 = torch.zeros_like(h_0)
        dummy_input = torch.zeros((x.size(0), self.seq_len, self.input_dim)).to(x.device)
        out, _ = self.decoder_lstm(dummy_input, (h_0, c_0))
        reconstruction = self.output_layer(out)
        return reconstruction
        
    def forward(self, x):
        mean, logvar = self.encode(x)
        z = self.reparameterize(mean, logvar)
        reconstruction = self.decode(z, x)
        return reconstruction, mean, logvar

def criterion(recon_x, x, mean, logvar):
    mse = nn.MSELoss(reduction='sum')(recon_x, x)
    kl_divergence = -0.5 * torch.sum(1 + logvar - mean.pow(2) - logvar.exp())
    return mse + kl_divergence, mse, kl_divergence

def train_model():
    set_seed(CONFIG["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Targeting compute device: {device}")
    
    # Load Numpy Artifacts
    train_data = np.load("train_seqs.npy")
    val_data = np.load("val_seqs.npy")
    
    train_tensor = torch.tensor(train_data, dtype=torch.float32)
    val_tensor = torch.tensor(val_data, dtype=torch.float32)
    
    train_loader = torch.utils.data.DataLoader(train_tensor, batch_size=CONFIG["batch_size"], shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_tensor, batch_size=CONFIG["batch_size"], shuffle=False)
    
    model = LSTM_VAE(
        CONFIG["input_dim"], 
        CONFIG["hidden_dim"], 
        CONFIG["latent_dim"], 
        CONFIG["sequence_length"]
    ).to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=CONFIG["learning_rate"])
    
    best_val_loss = float('inf')
    early_stop_counter = 0
    history = []
    
    for epoch in range(1, CONFIG["epochs"] + 1):
        model.train()
        train_loss, train_recon, train_kl = 0, 0, 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            recon, mean, logvar = model(batch)
            loss, recon_loss, kl_loss = criterion(recon, batch, mean, logvar)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            train_recon += recon_loss.item()
            train_kl += kl_loss.item()
            
        train_loss /= len(train_loader.dataset)
        train_recon /= len(train_loader.dataset)
        train_kl /= len(train_loader.dataset)
        
        model.eval()
        val_loss, val_recon, val_kl = 0, 0, 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                recon, mean, logvar = model(batch)
                loss, recon_loss, kl_loss = criterion(recon, batch, mean, logvar)
                val_loss += loss.item()
                val_recon += recon_loss.item()
                val_kl += kl_loss.item()
                
        val_loss /= len(val_loader.dataset)
        val_recon /= len(val_loader.dataset)
        val_kl /= len(val_loader.dataset)
        
        history.append({
            "epoch": epoch,
            "train_loss": train_loss, "train_recon": train_recon, "train_kl": train_kl,
            "val_loss": val_loss, "val_recon": val_recon, "val_kl": val_kl
        })
        
        print(f"Epoch {epoch:03d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | " 
              f"Val Recon: {val_recon:.4f} | Val KL: {val_kl:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            early_stop_counter = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "input_dim": CONFIG["input_dim"],
                "hidden_dim": CONFIG["hidden_dim"],
                "latent_dim": CONFIG["latent_dim"],
                "sequence_length": CONFIG["sequence_length"],
                "epoch": epoch,
                "best_validation_loss": best_val_loss
            }, "best_vae_model1_20f.pth")
            print("  --> Saved primary VAE checkpoint targeting minimal validation loss")
        else:
            early_stop_counter += 1
            if early_stop_counter >= CONFIG["patience"]:
                print(f"Early stopping triggered at epoch {epoch}")
                break
                
    # Unconditionally dump final epoch termination state
    torch.save({
        "model_state_dict": model.state_dict(),
        "input_dim": CONFIG["input_dim"],
        "hidden_dim": CONFIG["hidden_dim"],
        "latent_dim": CONFIG["latent_dim"],
        "sequence_length": CONFIG["sequence_length"],
        "epoch": epoch,
        "validation_loss": val_loss
    }, "final_vae_model1_20f.pth")
    
    pd.DataFrame(history).to_csv("training_history_model1_20f.csv", index=False)
    with open("model_config_model1_20f.json", "w") as f:
        json.dump(CONFIG, f, indent=4)

    # BUG 3 FIX: Compute and save REAL validation reconstruction errors from the
    # best checkpoint. These are used by threshold_selection.py to derive the
    # real 98th-percentile anomaly threshold.
    # NO synthetic/random values. NO simulate_checkpoint_verification.py.
    print("Computing real validation reconstruction errors from best checkpoint...")
    best_ckpt = torch.load(
        "best_vae_model1_20f.pth", map_location="cpu", weights_only=False
    )
    best_model_eval = LSTM_VAE(
        best_ckpt["input_dim"],
        best_ckpt["hidden_dim"],
        best_ckpt["latent_dim"],
        best_ckpt["sequence_length"]
    )
    best_model_eval.load_state_dict(best_ckpt["model_state_dict"])
    best_model_eval.eval()

    val_errors_list = []
    with torch.no_grad():
        for batch in val_loader:
            batch = batch.to("cpu")
            recon, _, _ = best_model_eval(batch)
            # Per-sequence MSE averaged over (seq_len, features) dimensions
            per_seq_mse = torch.mean((batch - recon) ** 2, dim=(1, 2))
            val_errors_list.append(per_seq_mse.numpy())

    val_errors_arr = np.concatenate(val_errors_list).astype(np.float32)
    np.save("model1_validation_errors.npy", val_errors_arr)
    print(f"Saved model1_validation_errors.npy: shape={val_errors_arr.shape}")
    print(f"  min={val_errors_arr.min():.4f}  max={val_errors_arr.max():.4f}  mean={val_errors_arr.mean():.4f}")
    print(f"  p98 (preview threshold): {np.percentile(val_errors_arr, 98):.4f}")
    print()
    print("Training sequence complete. Generated 6 expected artifacts.")

if __name__ == "__main__":
    train_model()
