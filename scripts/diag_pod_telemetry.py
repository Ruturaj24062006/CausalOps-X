import subprocess
import json

pod = 'telemetry-collector-6859495b88-bx6q8'
file = '/data/historical_telemetry_dump.jsonl'
def fetch(cmd):
    return subprocess.check_output(f'kubectl exec -n causalops {pod} -- {cmd}', shell=True).decode()

head1 = fetch(f'head -n 1 {file}').strip()
tail1 = fetch(f'tail -n 1 {file}').strip()

d_head = json.loads(head1)
d_tail = json.loads(tail1)

print("First timestamp:", d_head.get('window_start'), "to", d_head.get('window_end'))
print("Last timestamp:", d_tail.get('window_start'), "to", d_tail.get('window_end'))

f1 = d_head.get('features', {})
print("Sample features keys:", len(f1.keys()))
print("20-feature contract:", list(f1.keys()))

print("Namespace / Pod:", d_head.get('namespace'), d_head.get('pod'))
