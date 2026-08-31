import os
import sys
import subprocess
import json
import time

def run_cmd(cmd, timeout=30):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -2, "", "Block/Timeout Exception"
    except Exception as e:
        return -1, "", str(e)

def diag():
    report_file = os.path.abspath("artifacts/model2/step25/model2_v9_uvicorn_boundary_report.txt")
    json_report = os.path.abspath("artifacts/model2/step25/model2_v9_uvicorn_boundary_report.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    tests = {
        "app.main import": "FAIL",
        "FastAPI object": "FAIL",
        "Uvicorn import": "FAIL",
        "Uvicorn startup": "FAIL",
        "ASGI resolution": "FAIL",
        "Port 8000": "NOT LISTENING",
        "Internal health": "FAIL",
        "External health": "FAIL",
        "Startup hook reached": "UNKNOWN",
        "CPU/process state": "UNKNOWN",
        "Exact blocking boundary": "UNKNOWN"
    }

    print("Pre-staging isolated environment...")
    run_cmd("docker rm -f step25_diag")
    
    # 1. Start specifically isolated debug container
    run_cmd(f"docker run -d --name step25_diag -p 8002:8000 -v \"{os.path.abspath('.')}:/workspace\" --entrypoint sleep stream-processing-service 3600")
    
    time.sleep(3)
    
    # 2. Uvicorn import test
    c_u, o_u, e_u = run_cmd("docker exec step25_diag python -c \"import uvicorn; print(uvicorn.__version__); print('UVICORN_IMPORT_COMPLETE')\"")
    if "UVICORN_IMPORT_COMPLETE" in o_u:
        tests["Uvicorn import"] = "PASS"
        
    # 3. Main import test
    print("Testing app.main import natively...")
    c_i, o_i, e_i = run_cmd("docker exec step25_diag python -c \"import app.main; print('IMPORT_MAIN_COMPLETE')\"", timeout=15)
    if "IMPORT_MAIN_COMPLETE" in o_i:
        tests["app.main import"] = "PASS"
    elif e_i == "Block/Timeout Exception":
        tests["app.main import"] = "FAIL (Import hangs natively!)"

    # 4. FastAPI object test
    c_f, o_f, e_f = run_cmd("docker exec step25_diag python -c \"from app.main import app; print(type(app)); print('APP_OBJECT_COMPLETE')\"", timeout=15)
    if "APP_OBJECT_COMPLETE" in o_f:
        tests["FastAPI object"] = "PASS"
        tests["ASGI resolution"] = "PASS"
        
    # 5. Uvicorn Foreground process
    print("Starting Uvicorn directly natively...")
    run_cmd("docker exec -d step25_diag sh -c \"uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug > /uvicorn_out.log 2>&1\"")
    
    time.sleep(10)
    
    # Process state checks
    c_ps, o_ps, _ = run_cmd("docker exec step25_diag ps aux")
    
    if "uvicorn" in o_ps.lower():
        tests["CPU/process state"] = "Running (Active/Idle CPU)"
        tests["Uvicorn startup"] = "PASS"
    else:
        tests["CPU/process state"] = "Exited/Dropped"
        
    # Check Logs
    _, o_logs, _ = run_cmd("docker exec step25_diag cat /uvicorn_out.log")
    
    if "Application startup" in o_logs or "Started server process" in o_logs:
        tests["Startup hook reached"] = "YES"
        
    # 6. Socket test
    c_ss, o_ss, _ = run_cmd("docker exec step25_diag ss -lntp")
    if "8000" in o_ss:
        tests["Port 8000"] = "LISTENING"
        
    # Determine exact boundary
    if tests["app.main import"] == "FAIL (Import hangs natively!)":
        tests["Exact blocking boundary"] = "A. app.main import hangs (Module level isolation fail)"
    elif "Started server process" not in o_logs and tests["FastAPI object"] == "PASS":
        tests["Exact blocking boundary"] = "C. Uvicorn import/startup hangs"
    elif "Started server process" in o_logs and "Application startup" not in o_logs:
        tests["Exact blocking boundary"] = "D. ASGI lifespan/startup hangs"
    elif tests["Port 8000"] == "NOT LISTENING":
        tests["Exact blocking boundary"] = "E. Uvicorn process is alive but socket never opens"
    else:
        tests["Exact blocking boundary"] = f"Logged Trace: {o_logs[-1500:]}"
        
    run_cmd("docker rm -f step25_diag")

    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)

if __name__ == "__main__":
    diag()
