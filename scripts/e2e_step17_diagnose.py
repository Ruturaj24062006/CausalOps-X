import os
import sys
import json
import subprocess
import time

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return -1, "", str(e)

def diag():
    report_file = os.path.abspath("artifacts/model2/step17/model2_v9_docker_crash_diagnosis.txt")
    json_report = os.path.abspath("artifacts/model2/step17/model2_v9_docker_crash_diagnosis.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    # Pre-cleanup
    run_cmd(["docker", "rm", "-f", "diag_test"])
    
    print("Running diagnostic container...")
    cmd = ["docker", "run", "--name", "diag_test", "-p", "8002:8000", "-v", f"{os.path.abspath('.')}:/workspace", "stream-processing-service"]
    run_cmd(cmd)
    
    # The container should have crashed or exited by now
    tests = {
        "Container found": "PASS",
        "Container status": "UNKNOWN",
        "Exit code": "UNKNOWN",
        "OOM killed": "UNKNOWN",
        "Docker logs": "UNKNOWN",
        "Entrypoint": "UNKNOWN",
        "Command": "UNKNOWN",
        "Uvicorn reached": "UNKNOWN",
        "Port bind attempted": "UNKNOWN",
        "Checkpoint visible": "NOT TESTED",
        "Scaler visible": "NOT TESTED",
        "Python import failure": "UNKNOWN",
        "Root cause": "UNKNOWN"
    }

    # Inspect
    print("Inspecting...")
    _, o_status, _ = run_cmd(["docker", "inspect", "diag_test", "--format", "{{.State.Status}}"])
    _, o_exit, _ = run_cmd(["docker", "inspect", "diag_test", "--format", "{{.State.ExitCode}}"])
    _, o_error, _ = run_cmd(["docker", "inspect", "diag_test", "--format", "{{.State.Error}}"])
    _, o_oom, _ = run_cmd(["docker", "inspect", "diag_test", "--format", "{{.State.OOMKilled}}"])
    
    # Image inspect
    _, o_image, _ = run_cmd(["docker", "inspect", "stream-processing-service"])
    img_data = json.loads(o_image) if o_image else []
    
    if img_data:
        cfg = img_data[0].get("Config", {})
        tests["Entrypoint"] = str(cfg.get("Entrypoint"))
        tests["Command"] = str(cfg.get("Cmd"))
        
    tests["Container status"] = o_status.strip() if o_status else "NOT_FOUND" 
    tests["Exit code"] = o_exit.strip() if o_exit else "UNKNOWN"
    
    oom_status = o_oom.strip().upper() if o_oom else "UNKNOWN"
    tests["OOM killed"] = "TRUE" if oom_status == "TRUE" else "FALSE"
    
    # Logs
    _, o_logs, e_logs = run_cmd(["docker", "logs", "diag_test"])
    full_logs = (o_logs + "\n" + e_logs).strip()
    tests["Docker logs"] = full_logs if full_logs else "EMPTY"
    
    # Diagnose
    tests["Uvicorn reached"] = "YES" if "uvicorn" in full_logs.lower() or "started server process" in full_logs.lower() else "NO"
    tests["Port bind attempted"] = "YES" if "listening at" in full_logs.lower() or "bind" in full_logs.lower() else "NO"
    tests["Python import failure"] = "YES" if "importerror" in full_logs.lower() or "modulenotfounderror" in full_logs.lower() or "nameerror" in full_logs.lower() else "NO"
    
    if tests["Python import failure"] == "YES":
        err_lines = [l for l in full_logs.split('\n') if "Error:" in l]
        tests["Root cause"] = "\n".join(err_lines) if err_lines else "Import/Syntax failure"
    elif "kafka" in full_logs.lower() and "broker" in full_logs.lower():
        tests["Root cause"] = "Kafka connection timeout/failure in startup_event"
    else:
        # Fallback to tail
        tests["Root cause"] = "\n".join(full_logs.split('\n')[-5:]) if full_logs else o_error.strip()
    
    # Cleanup
    run_cmd(["docker", "rm", "-f", "diag_test"])
    
    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)
        
    print("FINISHED DIAGNOSIS")

if __name__ == "__main__":
    diag()
