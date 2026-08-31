import os
import sys
import subprocess
import json
import time

def run_cmd(cmd, timeout_secs=600):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, timeout=timeout_secs)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -2, "", "Block/Timeout Exception"
    except Exception as e:
        return -1, "", str(e)

def diag():
    report_file = os.path.abspath("artifacts/model2/step28/model2_v9_docker_recovery.txt")
    json_report = os.path.abspath("artifacts/model2/step28/model2_v9_docker_recovery.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    tests = {
        "Docker Desktop": "FAIL",
        "Docker Server": "FAIL",
        "Docker Engine": "FAIL",
        "WSL docker-desktop": "STOPPED",
        "Port 8002": "FREE",
        "Source fix retained": "FAIL",
        "Docker build": "FAIL",
        "New image": "FAIL",
        "Image ID": "None",
        "First build error": "None"
    }

    # Verify Source
    print("Verifying Source Integrity...")
    c_s, o_s, _ = run_cmd("type \"services\\stream-processing-service\\app\\main.py\"")
    if "asyncio.create_task" in o_s:
        tests["Source fix retained"] = "PASS"

    # Daemon availability checks
    print("Checking Docker status natively...")
    c_i, o_i, _ = run_cmd("docker info", timeout_secs=30)
    
    # Try recovering WSL Docker Engine dynamically if it's dead
    if c_i != 0:
        print("Docker Daemon offline. Sending WSL restart signals...")
        run_cmd("wsl -t docker-desktop")
        run_cmd("wsl -t docker-desktop-data")
        time.sleep(20)
        c_i, o_i, _ = run_cmd("docker info", timeout_secs=30)
        
    if c_i == 0 and "Server Version" in o_i:
        tests["Docker Desktop"] = "PASS"
        tests["Docker Server"] = "PASS"
        tests["Docker Engine"] = "PASS"
    else:
        # Final desperate check
        print("Waiting extended 30s for Docker socket response...")
        time.sleep(30)
        c_i2, o_i2, _ = run_cmd("docker info", timeout_secs=30)
        if c_i2 == 0:
            tests["Docker Desktop"] = "PASS"
            tests["Docker Server"] = "PASS" 
            tests["Docker Engine"] = "PASS"
            
    # WSL Status Parse
    _, o_wsl, _ = run_cmd("wsl -l -v")
    if "docker-desktop" in o_wsl and "Running" in o_wsl:
        tests["WSL docker-desktop"] = "RUNNING"
        
    # Check port 8002
    print("Verifying structural binding on port 8002...")
    c_net, o_net, _ = run_cmd("netstat -ano | findstr :8002")
    if "LISTENING" in o_net:
        tests["Port 8002"] = "OCCUPIED"
        
    # Stop build sequence if engine is utterly broken 
    if tests["Docker Server"] == "FAIL":
        tests["First build error"] = "Engine Offline Context Drop: Docker Desktop could not be structurally engaged before container pipeline."
    else:
        print("Executing exact Docker image rebuild...")
        build_cmd = (
            "docker build --no-cache --progress=plain "
            "-t stream-processing-service "
            "-f services/stream-processing-service/Dockerfile "
            "services/stream-processing-service"
        )
        c_b, o_b, e_b = run_cmd(build_cmd, timeout_secs=1000)
        
        if c_b == 0:
            tests["Docker build"] = "PASS"
            tests["New image"] = "PASS"
            # Get Image ID specially
            _, o_id, _ = run_cmd("docker images stream-processing-service --format \"{{.ID}}\"")
            if o_id:
                tests["Image ID"] = o_id.strip().split('\n')[0]
        else:
            full_logs = o_b + "\n" + e_b
            errors = [line for line in full_logs.split('\n') if any(keyword in line.lower() for keyword in ["error", "failed", "timeout", "returned non-zero"])]
            if errors:
                tests["First build error"] = errors[0].strip()
            else:
                tests["First build error"] = full_logs[-500:] if len(full_logs) > 500 else full_logs
                
            if e_b == "Block/Timeout Exception":
                tests["First build error"] = "Build timed out massively after 1000s native limit."

    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)
        
    print("FINISHED DOCKER WORKFLOW RECOVERY")

if __name__ == "__main__":
    diag()
