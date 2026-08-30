import sys
import os
import hashlib
import traceback

def get_hash(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print(f"PYTHON_VER={sys.version.split()[0]}")
    
    deps = ["torch", "torch_geometric", "numpy", "sklearn", "fastapi", "uvicorn", "pydantic"]
    for dep in deps:
        try:
            mod = __import__(dep)
            ver = getattr(mod, "__version__", "unknown")
            print(f"DEP_{dep}=PASS ({ver})")
        except Exception as e:
            print(f"DEP_{dep}=FAIL ({str(e)})")
            
    # Checkpoint and Scaler via mapped workspace
    ckpt_path = "/workspace/models/root_cause_analysis/model2_v9_best_per_node_model.pt"
    scaler_path = "/workspace/models/root_cause_analysis/model2_v9_step35_training_only_scaler.pkl"
    
    ckpt_hash = get_hash(ckpt_path)
    scaler_hash = get_hash(scaler_path)
    
    if ckpt_hash: 
        print(f"CKPT_EXISTS=PASS")
        print(f"CKPT_HASH={'PASS' if ckpt_hash.startswith('64F745EBFD632F131ECD6A7A') else 'FAIL'}")
    else: 
        print("CKPT_EXISTS=FAIL")
        
    if scaler_hash:
        print(f"SCALER_EXISTS=PASS")
        print(f"SCALER_HASH={'PASS' if scaler_hash.startswith('DF36200BC4924486A6525') else 'FAIL'}")
    else:
        print("SCALER_EXISTS=FAIL")
        
    # Attempt V9 Import
    sys.path.append("/workspace/services/stream-processing-service")
    try:
        from app.model2_v9_engine import Model2V9Engine
        print("V9_IMPORT=PASS")
        
        # Test Engine Instantiation natively assuming it reaches d:\ (it will FAIL here in linux!)
        try:
            eng = Model2V9Engine()
            print("V9_RUNTIME=PASS")
        except Exception as e:
            print(f"V9_RUNTIME=FAIL ({str(e)})")
            # Print full tb
            traceback.print_exc()
            
    except Exception as e:
        print(f"V9_IMPORT=FAIL ({str(e)})")
        traceback.print_exc()

if __name__ == "__main__":
    main()
