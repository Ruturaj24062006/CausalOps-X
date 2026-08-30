import csv
import collections
import statistics
import datetime
import json

csv_path = r"d:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv"

expected_order = [
    "metric_count", "metric_mean", "metric_std", "metric_min", "metric_max", "metric_current",
    "log_count", "error_count", "warning_count", "info_count", "unique_error_count", "unique_message_count",
    "event_count", "warning_event_count", "normal_event_count", "failed_event_count",
    "unhealthy_event_count", "unique_reason_count", "unique_resource_count", "pod_event_count"
]

def analyze():
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
        
    print("--- 1. FEATURE NULL ANALYSIS ---")
    total_rows = len(data)
    
    stats = {}
    for feat in expected_order:
        stats[feat] = {"nulls": 0, "zeros": 0, "vals": []}
        
    for row in data:
        for feat in expected_order:
            val = row[feat]
            if val in ('', 'None', None):
                stats[feat]["nulls"] += 1
            else:
                try:
                    fval = float(val)
                    stats[feat]["vals"].append(fval)
                    if fval == 0:
                        stats[feat]["zeros"] += 1
                except ValueError:
                    pass
                    
    for feat in expected_order:
        vals = stats[feat]["vals"]
        if vals:
            stats[feat]["min"] = min(vals)
            stats[feat]["max"] = max(vals)
            stats[feat]["mean"] = statistics.mean(vals)
            stats[feat]["median"] = statistics.median(vals)
            stats[feat]["std"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
        else:
            stats[feat]["min"] = None
            stats[feat]["max"] = None
            stats[feat]["mean"] = None
            stats[feat]["median"] = None
            stats[feat]["std"] = None
            
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['nulls'], reverse=True)
    for feat, s in sorted_stats:
        pct = (s['nulls'] / total_rows) * 100
        z_pct = (s['zeros'] / total_rows) * 100
        print(f"{feat:22} | Nulls: {s['nulls']:4} ({pct:5.1f}%) | Zeros: {s['zeros']:4} | "
              f"Min: {s['min']} | Max: {s['max']} | Mean: {s['mean']} | Std: {s['std']}")
              
    print("\n--- 3. TELEMETRY SOURCE COVERAGE ---")
    w_metrics = sum(1 for row in data if int(row.get('metric_count') or 0) > 0)
    w_no_metrics = total_rows - w_metrics
    w_logs = sum(1 for row in data if int(row.get('log_count') or 0) > 0)
    w_no_logs = total_rows - w_logs
    w_events = sum(1 for row in data if int(row.get('event_count') or 0) > 0)
    w_no_events = total_rows - w_events
    print(f"Windows with metrics: {w_metrics}, Without: {w_no_metrics}")
    print(f"Windows with logs: {w_logs}, Without: {w_no_logs}")
    print(f"Windows with events: {w_events}, Without: {w_no_events}")
    
    print("\n--- 5. GROUPING ANALYSIS ---")
    namespaces = collections.Counter(r['namespace'] for r in data if r.get('namespace'))
    pods = collections.Counter(r['pod'] for r in data if r.get('pod'))
    sid_count = sum(1 for r in data if r.get('service_id'))
    print(f"Service ID availability: missing in {total_rows - sid_count} out of {total_rows} records.")
    print(f"Namespaces ({len(namespaces)}): {namespaces}")
    print(f"Pods ({len(pods)}): {pods.most_common(5)}...")
    
    print("\n--- 6. TEMPORAL ANALYSIS & 7. SEQUENCE ANALYSIS ---")
    sizes = [5, 10, 20, 30]
    total_seqs = {s: 0 for s in sizes}
    valid_seqs = {s: 0 for s in sizes}
    
    groups = collections.defaultdict(list)
    for r in data:
        key = f"{r['namespace']}||{r['pod']}"
        groups[key].append(r)
        
    for k, rows in groups.items():
        rows.sort(key=lambda x: x['window_start'])
        N = len(rows)
        for L in sizes:
            if N >= L:
                for i in range(N - L + 1):
                    total_seqs[L] += 1
                    seq = rows[i:i+L]
                    
                    has_null = False
                    for r in seq:
                        for f in expected_order:
                            if r[f] in ('', 'None', None):
                                has_null = True
                                break
                        if has_null: break
                    if not has_null:
                        valid_seqs[L] += 1
                        
    for L in sizes:
        print(f"Length {L} | Total seqs: {total_seqs[L]} | Fully valid (no nulls): {valid_seqs[L]} | With nulls: {total_seqs[L] - valid_seqs[L]}")

if __name__ == "__main__":
    analyze()
