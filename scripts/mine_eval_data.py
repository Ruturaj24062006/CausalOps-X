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
    seen = set()
    for line in logs.split('\n'):
        if 'Model1 Output Validated >>' in line:
            str_data = line.split('Model1 Output Validated >> ')[1].replace("'", '"')
            try:
                pred = json.loads(str_data)
                uid = pred['timestamp'] + pred['pod']
                if uid not in seen:
                    preds.append(pred)
                    seen.add(uid)
            except Exception as e:
                pass
    return preds
    
logs = fetch_logs()
preds = extract_all_predictions(logs)

# Our known fault intervals in UTC
# Postgres Fault: ~ 2026-09-08 20:16
# Step 23 Fault 1 (neo4j): ~ 2026-09-08 20:53 - 20:55
# Step 23 Fault 2 (metrics): ~ 2026-09-08 20:56 - 20:57
# Step 23 Fault 3 (redis): ~ 2026-09-08 20:58 - 20:59
# Step 25 Fault 1 (neo4j): ~ 2026-09-08 21:12 - 21:13
# Step 25 Fault 2 (metrics): ~ 2026-09-08 21:14 - 21:15
# Step 25 Fault 3 (redis): ~ 2026-09-08 21:16 - 21:17

fault_intervals = [
    ("2026-09-08T20:15:00", "2026-09-08T20:18:00", "postgres"),
    ("2026-09-08T20:53:00", "2026-09-08T20:55:00", "neo4j"),
    ("2026-09-08T20:56:00", "2026-09-08T20:58:00", "data-ingestion"),
    ("2026-09-08T20:59:00", "2026-09-08T21:01:00", "redis"),
    ("2026-09-08T21:12:00", "2026-09-08T21:14:00", "neo4j"),
    ("2026-09-08T21:15:00", "2026-09-08T21:16:00", "data-ingestion"),
    ("2026-09-08T21:17:00", "2026-09-08T21:19:00", "redis")
]

# We also skip recovery transition minutes just to be safe
skip_intervals = [
    ("2026-09-08T20:18:00", "2026-09-08T20:25:00"),
    ("2026-09-08T20:55:00", "2026-09-08T20:56:00"),
    ("2026-09-08T20:58:00", "2026-09-08T20:59:00"),
    ("2026-09-08T21:01:00", "2026-09-08T21:12:00"),
    ("2026-09-08T21:14:00", "2026-09-08T21:15:00"),
    ("2026-09-08T21:16:00", "2026-09-08T21:17:00")
]

def in_interval(ts, start, end):
    return start <= ts <= end

for p in preds:
    ts = p['timestamp'][:19] # truncate offset
    
    is_fault = False
    fault_name = ""
    for start, end, name in fault_intervals:
        if in_interval(ts, start, end):
            is_fault = True
            fault_name = name
            break
            
    is_skip = False
    for start, end in skip_intervals:
        if in_interval(ts, start, end):
            is_skip = True
            break
            
    if is_skip and not is_fault:
        continue
        
    eval_data.append({
        'ground_truth_label': 1 if is_fault else 0,
        'fault_id': fault_name if is_fault else 'baseline',
        **p
    })

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
for t_val in [50.0, 30.0, 20.0, 17.43, 15.0, 10.0, 5.0, 2.0, 0.5, 0.1]:
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
