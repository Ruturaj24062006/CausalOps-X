import subprocess
import time
import json
import os
import datetime

eval_data = []
known_timestamps = set()

def fetch_logs():
    pod = subprocess.check_output('kubectl get pods -n causalops -l app=stream-processing --sort-by=.metadata.creationTimestamp -o name', shell=True).decode().strip().split('\n')[-1]
    return subprocess.check_output(f'kubectl logs -n causalops {pod} --tail=10000', shell=True).decode()

def extract_all_predictions(logs):
    preds = []
    for line in logs.split('\n'):
        if 'Model1 Output Validated >>' in line:
            str_data = line.split('Model1 Output Validated >> ')[1].replace("'", '"')
            try:
                pred = json.loads(str_data)
                preds.append(pred)
            except Exception as e:
                pass
    return preds

print('Starting Expanded Evaluation Data Collection...')

logs_pre = fetch_logs()
preds_pre = extract_all_predictions(logs_pre)
known_timestamps = set(p['timestamp'] + p['pod'] for p in preds_pre)

def run_fault(fault_id, cmd_fault, cmd_recover, baseline_wait=200, fault_wait=200):
    print(f'\\n--- FAULT SCENARIO: {fault_id} ---')
    print(f'Collecting baseline healthy windows ({baseline_wait}s)...')
    time.sleep(baseline_wait)
    
    logs_base = fetch_logs()
    preds = extract_all_predictions(logs_base)
    for p in preds:
        uid = p['timestamp'] + p['pod']
        if uid not in known_timestamps:
            eval_data.append({'ground_truth_label': 0, 'fault_id': 'baseline', **p})
            known_timestamps.add(uid)
            
    print(f'Injecting fault: {cmd_fault}')
    subprocess.check_call(cmd_fault, shell=True)
    print(f'Collecting fault windows ({fault_wait}s)...')
    time.sleep(fault_wait)
    
    logs_fault = fetch_logs()
    preds = extract_all_predictions(logs_fault)
    for p in preds:
        uid = p['timestamp'] + p['pod']
        if uid not in known_timestamps:
            # We label any window explicitly during this timeframe as fault
            eval_data.append({'ground_truth_label': 1, 'fault_id': fault_id, **p})
            known_timestamps.add(uid)
            
    if cmd_recover:
        print(f'Recovering from fault: {cmd_recover}')
        subprocess.check_call(cmd_recover, shell=True)
        time.sleep(60)
        
    # Read the buffer mapping immediately after recovery mapping it temporarily as transitional
    logs_rec = fetch_logs()
    preds = extract_all_predictions(logs_rec)
    for p in preds:
        uid = p['timestamp'] + p['pod']
        if uid not in known_timestamps:
            known_timestamps.add(uid) # skip saving transitional recovery windows

# Scenario 1: Postgres scale to 0
run_fault('postgres_scale', 'kubectl scale deployment postgres -n causalops --replicas=0', 'kubectl scale deployment postgres -n causalops --replicas=1', 180, 180)

# Scenario 2: Neo4j scale to 0
run_fault('neo4j_scale', 'kubectl scale deployment neo4j -n causalops --replicas=0', 'kubectl scale deployment neo4j -n causalops --replicas=1', 180, 180)

# Scenario 3: Data-ingestion restart
run_fault('data_ingest_restart', 'kubectl delete pod -n causalops -l app=data-ingestion', '', 180, 180)


os.makedirs('artifacts/feature_validation/model1_fault_evaluation_v2', exist_ok=True)
with open('artifacts/feature_validation/model1_fault_evaluation_v2/dataset.json', 'w') as f:
    json.dump(eval_data, f, indent=2)

print('\\nEvaluating Expanded Dataset...')
THRESHOLD = 17.43091926574707

tp = tn = fp = fn = 0
for w in eval_data:
    pred = 1 if w['anomaly_score'] > THRESHOLD else 0
    gt = w['ground_truth_label']
    if gt == 1 and pred == 1: tp += 1
    elif gt == 0 and pred == 0: tn += 1
    elif gt == 0 and pred == 1: fp += 1
    elif gt == 1 and pred == 0: fn += 1

healthy = sum(1 for w in eval_data if w['ground_truth_label'] == 0)
faulty = sum(1 for w in eval_data if w['ground_truth_label'] == 1)

print(f"Total evaluation windows: {len(eval_data)}")
print(f"Healthy windows: {healthy}")
print(f"Fault windows: {faulty}")

print(f"TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")

accuracy = (tp + tn) / len(eval_data) if len(eval_data) > 0 else 0.0
precision = tp / (tp + fp) if tp + fp > 0 else 0.0
recall = tp / (tp + fn) if tp + fn > 0 else 0.0
f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0.0
fpr = fp / (fp + tn) if fp + tn > 0 else 0.0
tpr = tp / (tp + fn) if tp + fn > 0 else 0.0

print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1: {f1:.4f}")
print(f"FPR: {fpr:.4f}")
print(f"TPR: {tpr:.4f}")

try:
    from sklearn.metrics import roc_auc_score, average_precision_score
    y_true = [w['ground_truth_label'] for w in eval_data]
    y_score = [w['anomaly_score'] for w in eval_data]
    roc = roc_auc_score(y_true, y_score)
    pr = average_precision_score(y_true, y_score)
    print(f"ROC-AUC: {roc:.4f}")
    print(f"PR-AUC: {pr:.4f}")
except Exception as e:
    print("ROC-AUC/PR-AUC: UNAVAILABLE (sklearn not accessible or insufficient diverse samples)")

print('\\nThreshold sweep (Research Only):')
best_f1 = -1
best_t = -1
for t_val in [50.0, 30.0, 20.0, 17.43, 10.0, 5.0, 2.0, 0.5, 0.1]:
    _tp = _tn = _fp = _fn = 0
    for w in eval_data:
        p_val = 1 if w['anomaly_score'] > t_val else 0
        g_val = w['ground_truth_label']
        if g_val == 1 and p_val == 1: _tp += 1
        elif g_val == 0 and p_val == 0: _tn += 1
        elif g_val == 0 and p_val == 1: _fp += 1
        elif g_val == 1 and p_val == 0: _fn += 1
    
    _rec = _tp / (_tp + _fn) if _tp + _fn > 0 else 0.0
    _pre = _tp / (_tp + _fp) if _tp + _fp > 0 else 0.0
    _fpr = _fp / (_fp + _tn) if _fp + _tn > 0 else 0.0
    _f1 = 2 * (_pre * _rec) / (_pre + _rec) if _pre + _rec > 0 else 0.0
    print(f'T={t_val:5.2f} -> Prec: {_pre:.2f}, Rec: {_rec:.2f}, F1: {_f1:.2f}, FPR: {_fpr:.2f}')
    if _f1 > best_f1:
        best_f1 = _f1
        best_t = t_val

print(f"\\nBest observed research threshold: T={best_t} (F1={best_f1:.2f})")
