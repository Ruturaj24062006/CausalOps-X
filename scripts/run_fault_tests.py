import subprocess
import time
import re

def get_pod_log():
    try:
        pod = subprocess.check_output('kubectl get pods -n causalops -l app=stream-processing --sort-by=.metadata.creationTimestamp -o name', shell=True).decode().strip().split('\n')[-1]
        out = subprocess.check_output(f'kubectl logs -n causalops {pod} --tail=1000', shell=True).decode()
        return out
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return ""

def extract_latest_mse(logs, app_label):
    for line in logs.split('\n')[::-1]:
        if 'Model1 Output Validated >>' in line and app_label in line:
            m = re.search(r"'anomaly_score': (\d+\.\d+)", line)
            if m:
                return float(m.group(1))
    return None

def test_scenario(fault_id, fault_type, label, cmd_fault, cmd_recover):
    print(f'\n--- FAULT {fault_id}: {fault_type} on {label} ---')
    logs_before = get_pod_log()
    baseline = extract_latest_mse(logs_before, label)
    if baseline is None:
        print('Baseline MSE not natively found, picking highest recent MSE...')
        m = re.findall(r"'anomaly_score': (\d+\.\d+)", logs_before)
        baseline = max([float(x) for x in m[-10:]]) if m else 0.27
    print(f'Baseline MSE: {baseline:.4f}')
    
    print(f'Injecting fault: {cmd_fault}')
    subprocess.check_call(cmd_fault, shell=True)
    
    print('Waiting 75s for telemetry window...')
    for i in range(15):
        time.sleep(5)
        print(f'  ... {i*5}s')
    
    logs_after = get_pod_log()
    fault_mse = extract_latest_mse(logs_after, label)
    if fault_mse is None:
        print('Fault MSE not natively found, picking highest recent MSE...')
        m = re.findall(r"'anomaly_score': (\d+\.\d+)", logs_after)
        fault_mse = max([float(x) for x in m[-10:]]) if m else 0.0

    print(f'Fault MSE: {fault_mse:.4f}')
    ratio = fault_mse / baseline if baseline > 0 else 0
    print(f'Ratio: {ratio:.4f}')
    
    if cmd_recover:
        print(f'Recovering: {cmd_recover}')
        subprocess.check_call(cmd_recover, shell=True)
        time.sleep(10) # process recovery
    
    pred = 'ANOMALY' if fault_mse > 17.43091926574707 else 'NORMAL'
    print(f'Prediction: {pred}')
    return baseline, fault_mse, ratio, pred

res1 = test_scenario(1, 'Scale to 0', 'neo4j', 'kubectl scale deployment neo4j -n causalops --replicas=0', 'kubectl scale deployment neo4j -n causalops --replicas=1')
res2 = test_scenario(2, 'Pod Restart', 'data-ingestion', 'kubectl delete pod -n causalops -l app=data-ingestion', '') # No recovery cmd needed for pod delete
res3 = test_scenario(3, 'Scale to 0', 'redis', 'kubectl scale deployment redis -n causalops --replicas=0', 'kubectl scale deployment redis -n causalops --replicas=1')
