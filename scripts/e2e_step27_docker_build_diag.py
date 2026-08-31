import os
import sys
import subprocess
import json

def run_cmd(cmd):
    try:
        # Avoid charmap Unicode decoding crashes on Windows natively
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return res.returncode, res.stdout.decode('utf-8', errors='replace').strip(), res.stderr.decode('utf-8', errors='replace').strip()
    except Exception as e:
        return -1, "", str(e)

def diag():
    report_file = os.path.abspath("artifacts/model2/step27/model2_v9_docker_build_diagnosis.txt")
    json_report = os.path.abspath("artifacts/model2/step27/model2_v9_docker_build_diagnosis.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    tests = {
        "Docker daemon": "FAIL",
        "Source fix present": "FAIL",
        "Build command": "docker build --no-cache --progress=plain -t stream-processing-service -f services/stream-processing-service/Dockerfile services/stream-processing-service",
        "Build": "FAIL",
        "First build error": "UNKNOWN",
        "Failure category": "UNKNOWN",
        "Existing image": "UNKNOWN",
        "New image created": "NO"
    }

    # Verify daemon
    c_i, o_i, _ = run_cmd("docker info")
    if c_i == 0: tests["Docker daemon"] = "PASS"
    
    # Verify Source
    c_s, o_s, _ = run_cmd("type \"services\\stream-processing-service\\app\\main.py\"")
    if "asyncio.create_task" in o_s:
        tests["Source fix present"] = "PASS"

    # Run build
    print("Initiating direct Docker build diagnosing with plain progress tracking...")
    c_b, o_b, e_b = run_cmd(tests["Build command"])
    
    if c_b == 0:
        tests["Build"] = "PASS"
        tests["New image created"] = "YES"
    else:
        # Isolate First failure
        full_logs = o_b + "\n" + e_b
        errors = [line for line in full_logs.split('\n') if any(keyword in line.lower() for keyword in ["error", "failed", "timeout", "returned non-zero"])]
        if errors:
            tests["First build error"] = errors[0].strip()
        else:
            tests["First build error"] = full_logs[-500:] if len(full_logs) > 500 else full_logs
            
        err_lower = tests["First build error"].lower()
        if "syntax" in err_lower or "dockerfile" in err_lower: tests["Failure category"] = "A. Dockerfile syntax error"
        elif "pip" in err_lower or "python" in err_lower: tests["Failure category"] = "B. Python/package installation failure"
        elif "torch" in err_lower: tests["Failure category"] = "C. PyTorch installation failure"
        elif "network" in err_lower or "download" in err_lower: tests["Failure category"] = "E. network/package download failure"
        elif "daemon" in err_lower or "pipe" in err_lower: tests["Failure category"] = "G. Docker daemon/resource failure"
        else: tests["Failure category"] = "I. another exact cause"
        
    print("Checking specific image cache mappings...")
    _, o_im, _ = run_cmd("docker images stream-processing-service --format \"{{.ID}} | {{.CreatedAt}}\"")
    tests["Existing image"] = o_im.strip() if o_im else "None"

    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)
        
    print("FINISHED DOCKER BUILD DIAGNOSIS")

if __name__ == "__main__":
    diag()
