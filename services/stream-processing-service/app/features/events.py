def extract_event_features(events: list) -> dict:
    features = {
        "event_count": len(events),
        "warning_event_count": 0,
        "normal_event_count": 0,
        "failed_event_count": 0,
        "unhealthy_event_count": 0,
        "unique_reason_count": 0,
        "unique_resource_count": 0,
        "pod_event_count": 0
    }
    
    reasons = set()
    resources = set()
    
    for e in events:
        payload = e.get("payload", {})
        reason = payload.get("reason", "")
        e_type = payload.get("type", "")
        r_type = payload.get("involvedObject", {}).get("kind", "") if isinstance(payload, dict) else ""
        
        if reason:
            reasons.add(reason)
            if "fail" in reason.lower():
                features["failed_event_count"] += 1
            if "unhealthy" in reason.lower():
                features["unhealthy_event_count"] += 1
                
        if r_type:
            resources.add(r_type)
            if r_type == "Pod":
                features["pod_event_count"] += 1
                
        if e_type == "Warning":
            features["warning_event_count"] += 1
        elif e_type == "Normal":
            features["normal_event_count"] += 1
            
    features["unique_reason_count"] = len(reasons)
    features["unique_resource_count"] = len(resources)
    return features
