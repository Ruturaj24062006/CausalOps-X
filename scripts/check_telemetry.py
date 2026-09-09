import subprocess
import json
import os

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

print("--- PROMETHEUS ---")
prom_pod = run_cmd("kubectl get pods -n causalops -l app=prometheus -o name").strip()
if prom_pod:
    print(f"Prometheus pod: {prom_pod}")
    try:
        targets_json = run_cmd(f"kubectl exec -n causalops {prom_pod} -- wget -qO- http://localhost:9090/api/v1/targets")
        print(f"Targets response length: {len(targets_json)}")
        data = json.loads(targets_json)
        active = [t for t in data.get('data', {}).get('activeTargets', [])]
        print(f"Active targets count: {len(active)}")
    except Exception as e:
        print(f"Failed to fetch Prometheus targets: {e}")
        
    try:
        metrics_json = run_cmd(f"kubectl exec -n causalops {prom_pod} -- wget -qO- http://localhost:9090/api/v1/query?query=up")
        print(f"Metrics response length: {len(metrics_json)}")
    except Exception as e:
        print(f"Failed to fetch Prometheus metrics: {e}")
else:
    print("Prometheus pod not found.")

print("\n--- APP LOGS ---")
app_pod = run_cmd("kubectl get pods -n causalops -l app=data-ingestion -o name").strip()
if app_pod:
    logs = run_cmd(f"kubectl logs -n causalops {app_pod} --tail=20")
    print(f"Logs length: {len(logs)}")
    print(f"Logs snippet: {logs[:100].strip()}")
else:
    print("App pod not found.")

print("\n--- KAFKA ---")
kafka_pod = run_cmd("kubectl get pods -n causalops -l app=kafka -o name").strip()
if kafka_pod:
    for topic in ["raw.metrics", "raw.logs", "raw.events", "enriched.features"]:
        print(f"\nChecking Kafka topic: {topic}")
        try:
            cmd = f"kubectl exec -n causalops {kafka_pod} -- timeout 5 kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic {topic} --from-beginning --max-messages 5"
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
            lines = [l for l in out.strip().split('\n') if l and 'Processed a total' not in l]
            print(f"Messages found in {topic}: {len(lines)}")
            if lines:
                print(f"Snippet: {lines[0][:100]}")
        except subprocess.CalledProcessError as e:
            out = e.output.decode('utf-8')
            lines = [l for l in out.strip().split('\n') if l and 'Processed a total' not in l]
            print(f"Messages found in {topic} (timeout/limit): {len(lines)}")
else:
    print("Kafka pod not found.")

print("\n--- K8S EVENTS ---")
events = run_cmd("kubectl get events -n causalops")
print(f"Kubernetes live events count: {len(events.strip().split(chr(10)))}")
