def extract_log_features(events: list) -> dict:
    features = {
        "log_count": len(events),
        "error_count": 0,
        "warning_count": 0,
        "info_count": 0,
        "unique_error_count": 0,
        "unique_message_count": 0
    }
    
    messages = set()
    errors = set()
    
    for e in events:
        payload = e.get("payload", {})
        msg = ""
        if isinstance(payload, dict):
            for k in ["log", "message", "msg", "Log", "Message"]:
                if k in payload and payload[k]:
                    msg = str(payload[k]).strip()
                    break
            if not msg and "kubernetes" not in payload:
                msg = str(payload).strip()
        else:
            msg = str(payload).strip()
            
        stream = payload.get("stream", "") if isinstance(payload, dict) else ""
        level = str(payload.get("level", payload.get("severity", ""))).lower() if isinstance(payload, dict) else ""
        
        if msg:
            messages.add(msg)
            
        is_error = "error" in level or stream == "stderr"
        is_warn = "warn" in level
        
        if is_error:
            features["error_count"] += 1
            if msg:
                errors.add(msg)
        elif is_warn:
            features["warning_count"] += 1
        else:
            features["info_count"] += 1
            
    features["unique_error_count"] = len(errors)
    features["unique_message_count"] = len(messages)
    return features
