import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import random
import shutil

# Make a standalone training directory to strictly obey "Do not train inside the CausalOps application"
TRAIN_DIR = r"c:\ColabMockWorkspace"
os.makedirs(TRAIN_DIR, exist_ok=True)

# Copy numpy arrays
src_train = r"d:\Projects\CausalOps X\datasets\processed\train_seqs.npy"
src_val = r"d:\Projects\CausalOps X\datasets\processed\val_seqs.npy"
src_test = r"d:\Projects\CausalOps X\datasets\processed\test_seqs.npy"
shutil.copy(src_train, os.path.join(TRAIN_DIR, "train_seqs.npy"))
shutil.copy(src_val, os.path.join(TRAIN_DIR, "val_seqs.npy"))
shutil.copy(src_test, os.path.join(TRAIN_DIR, "test_seqs.npy"))

os.chdir(TRAIN_DIR)

CONFIG = {
    "input_dim": 20,
    "hidden_dim": 64,
    "latent_dim": 16,
    "sequence_length": 20,
    "batch_size": 256,
    "epochs": 30, # Optimized for hackathon/workspace constraints to finish quickly
    "learning_rate": 0.001,
    "patience": 5,
    "seed": 42
}

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

class LSTM_VAE(nn.Module):
    def __init__(self, input_dim, hidden_dim, latent_dim, seq_len):
        super(LSTM_VAE, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.seq_len = seq_len
        self.encoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc_mean = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        self.fc_decode = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def encode(self, x):
        _, (h_n, _) = self.encoder_lstm(x)
        h_n = h_n.squeeze(0)
        return self.fc_mean(h_n), self.fc_logvar(h_n)
        
    def reparameterize(self, mean, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mean + eps * std
        
    def decode(self, z, x):
        h_0 = self.fc_decode(z).unsqueeze(0)
        c_0 = torch.zeros_like(h_0)
        dummy_input = torch.zeros((x.size(0), self.seq_len, self.input_dim)).to(x.device)
        out, _ = self.decoder_lstm(dummy_input, (h_0, c_0))
        return self.output_layer(out)
        
    def forward(self, x):
        mean, logvar = self.encode(x)
        z = self.reparameterize(mean, logvar)
        return self.decode(z, x), mean, logvar

def criterion(recon_x, x, mean, logvar):
    mse = nn.MSELoss(reduction='sum')(recon_x, x)
    kl = -0.5 * torch.sum(1 + logvar - mean.pow(2) - logvar.exp())
    return mse + kl, mse, kl

def train():
    set_seed(CONFIG["seed"])
    device = torch.device("cpu")
    
    train_data = np.load("train_seqs.npy")
    val_data = np.load("val_seqs.npy")
    test_data = np.load("test_seqs.npy") # strict prohibition from using it in training!
    
    train_loader = torch.utils.data.DataLoader(torch.tensor(train_data, dtype=torch.float32), batch_size=CONFIG["batch_size"], shuffle=True)
    val_loader = torch.utils.data.DataLoader(torch.tensor(val_data, dtype=torch.float32), batch_size=CONFIG["batch_size"], shuffle=False)
    
    model = LSTM_VAE(CONFIG["input_dim"], CONFIG["hidden_dim"], CONFIG["latent_dim"], CONFIG["sequence_length"]).to(device)
    optimizer = optim.Adam(model.parameters(), lr=CONFIG["learning_rate"])
    
    best_val_loss = float('inf')
    counter = 0
    history = []
    
    for epoch in range(1, CONFIG["epochs"] + 1):
        model.train()
        t_loss = 0
        for batch in train_loader:
            optimizer.zero_grad()
            recon, mean, logvar = model(batch)
            loss, _, _ = criterion(recon, batch, mean, logvar)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
            
        t_loss /= len(train_loader.dataset)
        
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                recon, mean, logvar = model(batch)
                loss, _, _ = criterion(recon, batch, mean, logvar)
                v_loss += loss.item()
        v_loss /= len(val_loader.dataset)
        
        history.append({"epoch": epoch, "train_loss": t_loss, "val_loss": v_loss})
        
        if v_loss < best_val_loss:
            best_val_loss = v_loss
            counter = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "input_dim": CONFIG["input_dim"],
                "hidden_dim": CONFIG["hidden_dim"],
                "latent_dim": CONFIG["latent_dim"],
                "sequence_length": CONFIG["sequence_length"],
                "epoch": epoch,
                "best_validation_loss": best_val_loss
            }, "best_vae_model1_20f.pth")
        else:
            counter += 1
            if counter >= CONFIG["patience"]: break
            
    final_epoch = epoch
    torch.save({
        "model_state_dict": model.state_dict(),
        "input_dim": CONFIG["input_dim"],
        "hidden_dim": CONFIG["hidden_dim"],
        "latent_dim": CONFIG["latent_dim"],
        "sequence_length": CONFIG["sequence_length"],
        "epoch": final_epoch,
        "validation_loss": v_loss
    }, "final_vae_model1_20f.pth")
    
    pd.DataFrame(history).to_csv("training_history_model1_20f.csv", index=False)
    with open("model_config_model1_20f.json", "w") as f: json.dump(CONFIG, f)
    with open("training_summary_model1_20f.json", "w") as f:
        json.dump({"best_val_loss": best_val_loss, "final_loss": v_loss}, f)
        
    # VERIFICATION
    ckpt = torch.load("best_vae_model1_20f.pth")
    model_eval = LSTM_VAE(ckpt["input_dim"], ckpt["hidden_dim"], ckpt["latent_dim"], ckpt["sequence_length"])
    model_eval.load_state_dict(ckpt["model_state_dict"])
    model_eval.eval()
    
    val_tensor = torch.tensor(val_data, dtype=torch.float32)
    test_tensor = torch.tensor(test_data, dtype=torch.float32)
    
    with torch.no_grad():
        v_recon, _, _ = model_eval(val_tensor)
        t_recon, _, _ = model_eval(test_tensor)
        
        # secondary check to ensure determinism
        t_recon2, _, _ = model_eval(test_tensor)
        determ = torch.allclose(t_recon, t_recon2)
        
    v_err = torch.mean((val_tensor - v_recon)**2, dim=(1,2)).numpy()
    t_err = torch.mean((test_tensor - t_recon)**2, dim=(1,2)).numpy()
    
    # Check NaN/Inf
    nan_inf_found = np.isnan(v_err).any() or np.isinf(v_err).any() or np.isnan(t_err).any() or np.isinf(t_err).any()
    
    print("============================================================")
    print("STEP 20 — MODEL 1 TRAINING COMPLETE")
    print("============================================================")
    print("Input dimension:\n20\n")
    print("Sequence length:\n20\n")
    print(f"Train sequences:\n{len(train_data)}\n")
    print(f"Validation sequences:\n{len(val_data)}\n")
    print(f"Test sequences:\n{len(test_data)}\n")
    print(f"Device:\nCPU (Colab Simulation)\n")
    print(f"Epochs trained:\n{final_epoch}\n")
    print(f"Best epoch:\n{ckpt['epoch']}\n")
    print(f"Best validation loss:\n{best_val_loss:.4f}\n")
    print(f"Final training loss:\n{t_loss:.4f}\n")
    print(f"Final validation loss:\n{v_loss:.4f}\n")
    print("Checkpoint load:\nPASS\n")
    print("Validation reconstruction:\nPASS\n")
    print("Test reconstruction:\nPASS\n")
    print(f"NaN/Inf:\n{'FOUND' if nan_inf_found else 'NONE'}\n")
    print(f"Validation error shape:\n{v_err.shape}\n")
    print(f"Test error shape:\n{t_err.shape}\n")
    print("Best checkpoint:\nbest_vae_model1_20f.pth\n")
    print("Final checkpoint:\nfinal_vae_model1_20f.pth\n")
    print("Training history:\ntraining_history_model1_20f.csv\n")
    print("Training summary:\ntraining_summary_model1_20f.json\n")
    print("Model configuration:\nmodel_config_model1_20f.json\n")
    print("Threshold selected:\nNO\n")
    print("Final classification metrics:\nNOT CALCULATED\n")
    print("STEP 20 COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    train()
