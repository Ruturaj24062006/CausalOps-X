import re
import datetime

def parse_events(filepath):
    events = []
    base_time = datetime.datetime(2026, 8, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    
    with open(filepath, 'r', encoding='utf-16-le', errors='replace') as f:
        lines = f.readlines()
        
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
            
        # Regex to capture based on columns
        # LAST SEEN (e.g., 5m52s, 12s, 3m)
        # TYPE (e.g., Normal, Warning)
        # REASON (e.g., Scheduled, Failed)
        # OBJECT (e.g., pod/kafka-0)
        # MESSAGE (the rest)
        match = re.match(r'^([\w]+)\s+([\w]+)\s+([\w]+)\s+([\w/-]+)\s+(.+)$', line)
        if match:
            last_seen_str, e_type, reason, obj, message = match.groups()
            
            # parse last_seen_str (e.g. 5m22s, 12s, 3m)
            seconds_ago = 0
            m_match = re.search(r'(\d+)m', last_seen_str)
            s_match = re.search(r'(\d+)s', last_seen_str)
            if m_match:
                seconds_ago += int(m_match.group(1)) * 60
            if s_match:
                seconds_ago += int(s_match.group(1))
                
            ts = base_time - datetime.timedelta(seconds=seconds_ago)
            
            # extract resource and pod from OBJECT
            resource = "Unknown"
            pod_name = "unknown"
            if '/' in obj:
                resource_raw, pod_name = obj.split('/', 1)
                resource = resource_raw.capitalize() # "pod" -> "Pod"
            else:
                resource = obj.capitalize()
                
            # service id derived from pod (e.g., kafka-0 -> kafka)
            service_id = pod_name.split('-')[0] if '-' in pod_name else pod_name
            
            event = {
                "service_id": service_id,
                "namespace": "causalops",
                "pod": pod_name,
                "timestamp": ts.isoformat(),
                "source": "kubernetes",
                "payload": {
                    "type": e_type,
                    "reason": reason,
                    "resource": resource,
                    "message": message
                }
            }
            events.append(event)
            
    # sort historically (oldest first)
    events.sort(key=lambda x: x["timestamp"])
    return events

if __name__ == "__main__":
    evts = parse_events("events.txt")
    print(f"Parsed {len(evts)} events")
    for e in evts[:3]:
        print(e)
