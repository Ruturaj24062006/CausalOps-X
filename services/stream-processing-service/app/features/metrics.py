import statistics

def extract_metric_features(events: list) -> dict:
    if not events:
        return {
            "metric_count": 0,
            "metric_mean": None,
            "metric_std": None,
            "metric_min": None,
            "metric_max": None,
            "metric_current": None
        }
    
    values = []
    for e in events:
        payload = e.get("payload", {})
        val = payload.get("value")
        # Handle Prometheus format
        if val and isinstance(val, list) and len(val) == 2:
            try:
                values.append(float(val[1]))
            except (ValueError, TypeError):
                pass
                
    if not values:
        return {
            "metric_count": len(events),
            "metric_mean": None, "metric_std": None,
            "metric_min": None, "metric_max": None,
            "metric_current": None
        }
        
    std_val = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "metric_count": len(events),
        "metric_mean": sum(values) / len(values),
        "metric_std": std_val,
        "metric_min": min(values),
        "metric_max": max(values),
        "metric_current": values[-1]
    }
