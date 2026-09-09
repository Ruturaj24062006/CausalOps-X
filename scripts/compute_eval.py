import json

with open('artifacts/feature_validation/model1_fault_evaluation/dataset.json', 'r') as f:
    eval_data = json.load(f)

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

print(f"TP: {tp}")
print(f"TN: {tn}")
print(f"FP: {fp}")
print(f"FN: {fn}")

precision = tp / (tp + fp) if tp + fp > 0 else 0.0
recall = tp / (tp + fn) if tp + fn > 0 else 0.0
f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0.0
fpr = fp / (fp + tn) if fp + tn > 0 else 0.0
tpr = tp / (tp + fn) if tp + fn > 0 else 0.0

print(f"Precision: {precision}")
print(f"Recall: {recall}")
print(f"F1: {f1}")
print(f"FPR: {fpr}")
print(f"TPR: {tpr}")
