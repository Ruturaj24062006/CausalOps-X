import subprocess
import json

pod = 'telemetry-collector-6859495b88-bx6q8'
file = '/data/historical_telemetry_dump.jsonl'
try:
    head1 = subprocess.check_output(f'kubectl exec -n causalops {pod} -- head -n 1 {file}', shell=True).decode()
    tail1 = subprocess.check_output(f'kubectl exec -n causalops {pod} -- tail -n 1 {file}', shell=True).decode()
    
    start = json.loads(head1).get('time', json.loads(head1).get('@timestamp'))
    end = json.loads(tail1).get('time', json.loads(tail1).get('@timestamp'))
    
    print('Earliest:', start)
    print('Latest:', end)
    
except Exception as e:
    print('Error:', e)
