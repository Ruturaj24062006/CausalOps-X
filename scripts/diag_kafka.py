import subprocess
import copy
import sys

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()

kafka_pod = run("kubectl get pods -n causalops -l app=kafka -o name").strip()
if not kafka_pod:
    print("Kafka not found")
    sys.exit()

topic_stats = run(f"kubectl exec -n causalops {kafka_pod} -- kafka-topics.sh --describe --topic enriched.features --bootstrap-server localhost:9092")
print("Kafka Topic Config:")
print(topic_stats)

# Get the latest offset from python kafka-run-class.sh using correct path
path = "/opt/bitnami/kafka/bin/kafka-run-class.sh"
earliest = run(f"kubectl exec -n causalops {kafka_pod} -- {path} kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic enriched.features --time -2")
latest = run(f"kubectl exec -n causalops {kafka_pod} -- {path} kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic enriched.features --time -1")

print("Earliest offset:")
print(earliest)
print("Latest offset:")
print(latest)
