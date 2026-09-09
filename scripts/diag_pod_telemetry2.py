import subprocess

pod = 'telemetry-collector-6859495b88-bx6q8'
file = '/data/historical_telemetry_dump.jsonl'
head1 = subprocess.check_output(f'kubectl exec -n causalops {pod} -- head -n 1 {file}', shell=True).decode()
print("First row:", head1)
