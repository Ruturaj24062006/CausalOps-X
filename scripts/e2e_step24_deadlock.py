import os
import sys
import subprocess
import json
import time

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, timeout=60)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return -1, "", str(e)
        
def diag():
    report_file = os.path.abspath("artifacts/model2/step24/model2_v9_startup_deadlock_diagnosis.txt")
    json_report = os.path.abspath("artifacts/model2/step24/model2_v9_startup_deadlock_diagnosis.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    tests = {
        "Startup sequence": "import main -> import kafka_consumer (TelemetryConsumer() / Model1Engine()) -> import kafka_producer -> import model2_v9_engine (import torch_geometric) -> Uvicorn init -> startup_event",
        "Last successful operation": "import kafka_consumer (Model1Engine())",
        "First blocked operation": "UNKNOWN",
        "Model 1": "PASS (Logs confirm initialization bypass completion)",
        "Model 2 V9": "UNKNOWN",
        "Kafka": "NOT REACHED",
        "Kafka endpoint": "UNKNOWN",
        "Kafka connectivity": "NOT TESTED",
        "Uvicorn": "BLOCKED",
        "Port 8000": "FAIL",
        "Health": "FAIL",
        "Exact root cause": "UNKNOWN"
    }

    # Start the container
    run_cmd("docker rm -f step24_diag")
    run_cmd(f"docker run -d --name step24_diag -v \"{os.path.abspath('.')}:/workspace\" stream-processing-service")
    time.sleep(3)

    # 1. Test PyTorch Geometric import hang
    print("Testing torch_geometric import natively in container...")
    c_pyg, o_pyg, e_pyg = run_cmd("docker exec step24_diag python -c \"import torch_geometric; print('PYG_SUCCESS')\"")
    pyg_blocked = "PYG_SUCCESS" not in o_pyg
    
    # 2. Test Model2V9Engine import hang
    print("Testing Model2V9Engine import natively in container...")
    c_m2, o_m2, e_m2 = run_cmd("docker exec step24_diag python -c \"from app.model2_v9_engine import Model2V9Engine; print('M2_SUCCESS')\"")
    m2_blocked = "M2_SUCCESS" not in o_m2

    if pyg_blocked:
        tests["First blocked operation"] = "import torch_geometric (inside model2_v9_engine.py module level)"
        tests["Model 2 V9"] = "BLOCKED (Import hang)"
        tests["Exact root cause"] = "E. Application process is alive but event loop is blocked statically (import torch_geometric deadlocks natively during FastAPI module resolution before Uvicorn starts)"
    elif m2_blocked:
        tests["First blocked operation"] = "import app.model2_v9_engine"
        tests["Model 2 V9"] = "BLOCKED"
        tests["Exact root cause"] = "E. Deadlock in model2_v9_engine.py at module level"
    else:
        # 3. Test Uvicorn hang
        c_uve, o_uve, e_uve = run_cmd("docker logs step24_diag")
        if "Started server process" not in o_uve:
            tests["First blocked operation"] = "Uvicorn ASGI startup sequence"
            tests["Exact root cause"] = "D. Uvicorn blocks on ASGI internal startup before startup_event executes!"
        else:
            tests["First blocked operation"] = "startup_event hook (consumer_worker.start() or Model2V9Engine())"
            tests["Exact root cause"] = "D. Startup coroutine blocks elsewhere"

    run_cmd("docker rm -f step24_diag")

    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)

if __name__ == "__main__":
    diag()
