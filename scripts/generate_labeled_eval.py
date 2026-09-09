import subprocess
import time
import json
import sys
import os
import threading

sys.path.append(os.path.abspath('services/stream-processing-service'))
from app.inference import Model1Engine
from app.features.schema import FeatureVector

eval_data = []
current_fault_id = "baseline"
ground_truth_label = 0
stop_flag = False

def run_collector():
    engine = Model1Engine()
    cmd = "kubectl exec -n causalops kafka-0 -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic enriched.features"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    
    while not stop_flag:
        line = process.stdout.readline()
        if not line:
            continue
        try:
            val = json.loads(line)
            vec = FeatureVector(**val)
            pred = engine.ingest_vector(vec)
            if pred.get("status") not in ("INSUFFICIENT_SEQUENCE_DATA", "INVALID_FEATURE_COUNT", "REJECT_INVALID_MATHEMATICS", "INFERENCE_FAILURE"):
                eval_data.append({
                    "timestamp": pred.get("timestamp"),
                    "service": vec.service_id or "system",
                    "pod": vec.pod or "system",
                    "features": vec.features,
                    "mse": pred.get("anomaly_score"),
                    "threshold": pred.get("threshold"),
                    "prediction": pred.get("prediction"),
                    "ground_truth_label": ground_truth_label,
                    "fault_id": current_fault_id
                })
        except Exception as e:
            pass
            
    process.terminate()

def run_scenario():
    global current_fault_id, ground_truth_label, stop_flag
    
    t = threading.Thread(target=run_collector, daemon=True)
    t.start()
    
    print("Collecting baseline for 120s...")
    current_fault_id = "baseline"
    ground_truth_label = 0
    time.sleep(120)
    
    # -- FAULT 1 --
    print("Injecting Fault 1 (neo4j scale down)...")
    current_fault_id = 1
    ground_truth_label = 1
    subprocess.check_call("kubectl scale deployment neo4j -n causalops --replicas=0", shell=True)
    print("Waiting 120s during fault 1...")
    time.sleep(120)
    
    print("Recovering Fault 1...")
    current_fault_id = "recovery"
    ground_truth_label = 0
    subprocess.check_call("kubectl scale deployment neo4j -n causalops --replicas=1", shell=True)
    time.sleep(120)
    
    # -- FAULT 2 --
    print("Injecting Fault 2 (data-ingestion pod restart)...")
    current_fault_id = 2
    ground_truth_label = 1
    subprocess.check_call("kubectl delete pod -n causalops -l app=data-ingestion", shell=True)
    print("Waiting 120s during fault 2...")
    time.sleep(120)
    
    print("Recovering Fault 2 (automatic)...")
    current_fault_id = "recovery"
    ground_truth_label = 0
    time.sleep(120)
    
    # -- FAULT 3 --
    print("Injecting Fault 3 (redis scale down)...")
    current_fault_id = 3
    ground_truth_label = 1
    subprocess.check_call("kubectl scale deployment redis -n causalops --replicas=0", shell=True)
    print("Waiting 120s during fault 3...")
    time.sleep(120)
    
    print("Recovering Fault 3...")
    current_fault_id = "recovery"
    ground_truth_label = 0
    subprocess.check_call("kubectl scale deployment redis -n causalops --replicas=1", shell=True)
    time.sleep(120)
    
    stop_flag = True
    
    # Save the dataset
    os.makedirs('artifacts/feature_validation/model1_fault_evaluation', exist_ok=True)
    with open('artifacts/feature_validation/model1_fault_evaluation/dataset.json', 'w') as f:
        json.dump(eval_data, f, indent=2)
    print(f"Collected total windows: {len(eval_data)}")

if __name__ == "__main__":
    run_scenario()
