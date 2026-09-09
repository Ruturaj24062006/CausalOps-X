import csv

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

expected_20 = [
    'metric_count', 'metric_mean', 'metric_std', 'metric_min', 'metric_max', 'metric_current',
    'log_count', 'error_count', 'warning_count', 'info_count', 'unique_error_count', 'unique_message_count',
    'event_count', 'warning_event_count', 'normal_event_count', 'failed_event_count',
    'unhealthy_event_count', 'unique_reason_count', 'unique_resource_count', 'pod_event_count'
]

print("--- TASK 6: FEATURE QUALITY CHECK ---")
constant_features = []
real_variation_features = []

for feature in expected_20:
    values = [float(r[feature]) for r in data if r[feature].strip() != '']
    unique_vals = set(values)
    non_zero = sum(1 for v in values if v != 0)
    
    is_constant = len(unique_vals) <= 1
    if is_constant:
        constant_features.append(feature)
    else:
        real_variation_features.append(feature)
        
print("Constant features:")
for f in constant_features:
    print(f"- {f}")
print("Features with real variation:")
for f in real_variation_features:
    print(f"- {f}")

