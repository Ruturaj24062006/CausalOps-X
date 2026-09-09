import subprocess
import re
import json

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode('utf-8')
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8') if e.output else str(e)

print("--- TASK 4: VERIFY PROMETHEUS ---")
# Get Prometheus pod
out = run_cmd("kubectl get pods -n monitoring -l app=prometheus -o jsonpath='{.items[0].metadata.name}'")
prom_pod = out.strip().strip("'")
print(f"Prometheus Pod: {prom_pod}")

if prom_pod:
    # Query Prometheus for targets
    active_targets = run_cmd(f"kubectl exec -n monitoring {prom_pod} -- wget -qO- http://localhost:9090/api/v1/targets")
    print(f"Targets response length: {len(active_targets)}")
    
    # Query for some metrics
    metrics_query = run_cmd(f"kubectl exec -n monitoring {prom_pod} -- wget -qO- \"http://localhost:9090/api/v1/query?query=up\"")
    print(f"Metrics response length: {len(metrics_query)}")
    try:
        data = json.loads(metrics_query)
        res = data.get('data', {}).get('result', [])
        print(f"Metric 'up' results count: {len(res)}")
    except:
        print("Could not parse Prometheus metrics JSON.")

print("\n--- TASK 5: VERIFY APPLICATION LOGS ---")
# Get a causalops workload pod
out = run_cmd("kubectl get pods -n causalops -o jsonpath='{.items[0].metadata.name}'")
app_pod = out.strip().strip("'")
print(f"App Pod: {app_pod}")

if app_pod:
    logs = run_cmd(f"kubectl logs -n causalops {app_pod} --tail=10")
    print(f"Logs length: {len(logs)}")
    print(logs[:200])

print("\n--- TASK 6: VERIFY KUBERNETES EVENTS ---")
events = run_cmd("kubectl get events -n causalops")
lines = events.strip().split('\n')
print(f"Live events count: {len(lines)}")

print("\n--- TASK 7: VERIFY KAFKA ---")
out = run_cmd("kubectl get pods -n kafka -l app=kafka -o jsonpath='{.items[0].metadata.name}'")
kafka_pod = out.strip().strip("'")
print(f"Kafka Pod: {kafka_pod}")

if kafka_pod:
    # Check topics
    topics = run_cmd(f"kubectl exec -n kafka {kafka_pod} -- kafka-topics.sh --list --bootstrap-server localhost:9092")
    t_lines = topics.strip().split()
    print(f"Kafka Topics: {t_lines}")
    
    # Check if there are messages in raw.events or enriched.features
    print("Checking raw.metrics...")
    out_metrics = run_cmd(f"kubectl exec -n kafka {kafka_pod} -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw.metrics --from-beginning --max-messages 1 --timeout-ms 2000")
    print(f"raw.metrics output length: {len(out_metrics)}")

print("\n--- TASK 9: CHECK DATA SUFFICIENCY ---")
# Check if enriched.features has sequences
out_features = run_cmd(f"kubectl exec -n kafka {kafka_pod} -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic enriched.features --from-beginning --max-messages 100 --timeout-ms 5000")
f_lines = [l for l in out_features.strip().split('\n') if l and not l.startswith('Processed')]
print(f"enriched.features message count: {len(f_lines)}")
    
