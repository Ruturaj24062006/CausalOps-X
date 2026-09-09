import subprocess
import time
import json
import os
import datetime

eval_data = []
known_timestamps = set()

def fetch_logs():
    pod = subprocess.check_output('kubectl get pods -n causalops -l app=stream-processing --sort-by=.metadata.creationTimestamp -o name', shell=True).decode().strip().split('\n')[-1]
    return subprocess.check_output(f'kubectl logs -n causalops {pod} --tail=3000', shell=True).decode()

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

print('Starting evaluation tests...')
logs_pre = fetch_logs()
preds_pre = extract_all_predictions(logs_pre)
known_timestamps = set(p['timestamp'] for p in preds_pre)

def run_fault(fault_id, cmd_fault, cmd_recover, sleep_duration=75):
    print(f'\\n--- FAULT {fault_id} ---')
    print('Starting baseline (30s)...')
    time.sleep(30)
    
    logs_base = fetch_logs()
    preds = extract_all_predictions(logs_base)
    for p in preds:
        if p['timestamp'] not in known_timestamps:
            eval_data.append({'ground_truth_label': 0, 'fault_id': 'baseline', **p})
            known_timestamps.add(p['timestamp'])
            
    print(f'Injecting fault: {cmd_fault}')
    subprocess.check_call(cmd_fault, shell=True)
    time.sleep(sleep_duration)
    
    logs_fault = fetch_logs()
    preds = extract_all_predictions(logs_fault)
    for p in preds:
        if p['timestamp'] not in known_timestamps:
            eval_data.append({'ground_truth_label': 1, 'fault_id': fault_id, **p})
            known_timestamps.add(p['timestamp'])
            
    if cmd_recover:
        print(f'Recovering: {cmd_recover}')
        subprocess.check_call(cmd_recover, shell=True)
        time.sleep(30)
    
    logs_rec = fetch_logs()
    preds = extract_all_predictions(logs_rec)
    for p in preds:
        if p['timestamp'] not in known_timestamps:
            eval_data.append({'ground_truth_label': 0, 'fault_id': 'recovery', **p})
            known_timestamps.add(p['timestamp'])

run_fault('neo4j', 'kubectl scale deployment neo4j -n causalops --replicas=0', 'kubectl scale deployment neo4j -n causalops --replicas=1', 75)
run_fault('metrics', 'kubectl delete pod -n causalops -l app=data-ingestion', '', 75)
run_fault('redis', 'kubectl scale deployment redis -n causalops --replicas=0', 'kubectl scale deployment redis -n causalops --replicas=1', 75)

os.makedirs('artifacts/feature_validation/model1_fault_evaluation', exist_ok=True)
with open('artifacts/feature_validation/model1_fault_evaluation/dataset.json', 'w') as f:
    json.dump(eval_data, f, indent=2)

print('\\nEvaluating Threshold Performance...')
THRESHOLD = 17.43091926574707

tp = tn = fp = fn = 0
for w in eval_data:
    pred = 1 if w['anomaly_score'] > THRESHOLD else 0
    gt = w['ground_truth_label']
    if gt == 1 and pred == 1: tp += 1
    elif gt == 0 and pred == 0: tn += 1
    elif gt == 0 and pred == 1: fp += 1
    elif gt == 1 and pred == 0: fn += 1

print(f'Total: {len(eval_data)}')
print(f'TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}')

precision = tp / (tp + fp) if tp + fp > 0 else 0.0
recall = tp / (tp + fn) if tp + fn > 0 else 0.0
f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0.0
fpr = fp / (fp + tn) if fp + tn > 0 else 0.0
tpr = tp / (tp + fn) if tp + fn > 0 else 0.0

print(f'Precision: {precision}')
print(f'Recall: {recall}')
print(f'F1: {f1}')
print(f'FPR: {fpr}')
print(f'TPR: {tpr}')

print('\\nThreshold sweep (simulate lowering from 20.0 to 0.1):')
for t_val in [20.0, 17.43, 10.0, 5.0, 2.0, 0.5, 0.1]:
    _tp = _tn = _fp = _fn = 0
    for w in eval_data:
        p_val = 1 if w['anomaly_score'] > t_val else 0
        g_val = w['ground_truth_label']
        if g_val == 1 and p_val == 1: _tp += 1
        elif g_val == 0 and p_val == 0: _tn += 1
        elif g_val == 0 and p_val == 1: _fp += 1
        elif g_val == 1 and p_val == 0: _fn += 1
    
    _rec = _tp / (_tp + _fn) if _tp + _fn > 0 else 0.0
    _fpr = _fp / (_fp + _tn) if _fp + _tn > 0 else 0.0
    print(f'T={t_val:.2f} -> TPR: {_rec:.2f}, FPR: {_fpr:.2f}')

