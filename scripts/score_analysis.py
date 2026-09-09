import json
import numpy as np

with open('artifacts/feature_validation/model1_fault_evaluation_v2/dataset.json', 'r') as f:
    eval_data = json.load(f)

healthy_scores = [w['anomaly_score'] for w in eval_data if w['ground_truth_label'] == 0]
fault_scores = [w['anomaly_score'] for w in eval_data if w['ground_truth_label'] == 1]

def get_stats(scores):
    s = np.array(scores)
    return {
        'count': len(s),
        'min': s.min(),
        'max': s.max(),
        'mean': s.mean(),
        'median': np.median(s),
        'std': s.std(),
        'P50': np.percentile(s, 50),
        'P75': np.percentile(s, 75),
        'P90': np.percentile(s, 90),
        'P95': np.percentile(s, 95),
        'P99': np.percentile(s, 99),
    }

h_stats = get_stats(healthy_scores)
f_stats = get_stats(fault_scores)

print("--- Healthy Distribution ---")
for k,v in h_stats.items(): print(f"{k}: {v}")

print("\n--- Fault Distribution ---")
for k,v in f_stats.items(): print(f"{k}: {v}")

THRESHOLD = 17.43091926574707

f_below = sum(1 for s in fault_scores if s <= THRESHOLD) / len(fault_scores) * 100
h_below = sum(1 for s in healthy_scores if s <= THRESHOLD) / len(healthy_scores) * 100
f_above = sum(1 for s in fault_scores if s > THRESHOLD) / len(fault_scores) * 100
h_above = sum(1 for s in healthy_scores if s > THRESHOLD) / len(healthy_scores) * 100

print("\n--- Overlap Analysis ---")
print(f"Faults below threshold: {f_below:.2f}%")
print(f"Healthy below threshold: {h_below:.2f}%")
print(f"Faults above threshold (TPR): {f_above:.2f}%")
print(f"Healthy above threshold (FPR): {h_above:.2f}%")
print(f"Healthy/Fault median ratio: {h_stats['median'] / f_stats['median']:.4f}")
print(f"Healthy/Fault mean ratio: {h_stats['mean'] / f_stats['mean']:.4f}")

if f_stats['mean'] < h_stats['mean'] or f_stats['median'] < h_stats['median']:
    print("MODEL SCORE DIRECTION MAY BE INCONSISTENT WITH FAULT DATA")
else:
    print("SCORE DIRECTION: HIGHER MSE = MORE ANOMALOUS")

print("\n--- Threshold Analysis (RESEARCH ONLY) ---")
thresholds = [0.01, 0.05, 0.10, 0.25, 0.50, 1.0, 2.0, 5.0, 10.0, 17.43091926574707]
for t in thresholds:
    tp = sum(1 for s in fault_scores if s > t)
    fn = len(fault_scores) - tp
    fp = sum(1 for s in healthy_scores if s > t)
    tn = len(healthy_scores) - fp
    
    tpr = tp / (tp + fn) if (tp+fn)>0 else 0
    fpr = fp / (fp + tn) if (fp+tn)>0 else 0
    prec = tp / (tp + fp) if (tp+fp)>0 else 0
    rec = tpr
    f1 = 2 * prec * rec / (prec + rec) if (prec+rec)>0 else 0
    print(f"T={t:<5} | TPR: {tpr:.2f}, FPR: {fpr:.2f}, Prec: {prec:.2f}, Rec: {rec:.2f}, F1: {f1:.2f}")

try:
    from sklearn.metrics import roc_auc_score, average_precision_score
    y_true = [w['ground_truth_label'] for w in eval_data]
    y_score = [w['anomaly_score'] for w in eval_data]
    roc = roc_auc_score(y_true, y_score)
    pr = average_precision_score(y_true, y_score)
    print(f"\nROC-AUC: {roc:.4f}")
    print(f"PR-AUC: {pr:.4f}")
except Exception as e:
    pass

scenario_faults = {}
scenario_healthy = {}

# We categorize by fault_id
for w in eval_data:
    fid = w['fault_id']
    score = w['anomaly_score']
    
    # We will identify generic pod base if it's healthy, but fault scenario includes specific pods.
    if fid == 'baseline' or fid == 'recovery':
        continue
    
    if fid not in scenario_faults:
        scenario_faults[fid] = []
    
    scenario_faults[fid].append(score)

print("\n--- Scenario Breakdown ---")
for fid, scores in scenario_faults.items():
    s = np.array(scores)
    
    h_s = [w['anomaly_score'] for w in eval_data if w['ground_truth_label']==0]
    
    detected = sum(1 for sc in scores if sc > THRESHOLD)
    rate = detected / len(scores) * 100
    
    print(f"Scenario: {fid} | Healthy W: {len(h_s)} | Fault W: {len(scores)} | Mean: {s.mean():.4f} | Median: {np.median(s):.4f} | P95: {np.percentile(s, 95):.4f} | Detection: {rate:.2f}%")
