import os
import sys
import subprocess
import json

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, timeout=60)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return -1, "", str(e)

def diag():
    report_file = os.path.abspath("artifacts/model2/step21/model2_v9_port8002_cleanup.txt")
    json_report = os.path.abspath("artifacts/model2/step21/model2_v9_port8002_cleanup.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    tests = {
        "Port 8002 owner": "UNKNOWN",
        "PID": "UNKNOWN",
        "Owner identified": "FAIL",
        "Stale CausalOps container": "NO",
        "Cleanup performed": "NOT REQUIRED",
        "Port 8002 available": "FAIL",
        "Docker daemon": "PASS"
    }

    print("Checking Docker for port 8002...")
    c_ps, o_ps, e_ps = run_cmd("docker ps -a --format \"{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}\"")
    
    stale_container_name = None
    if c_ps != 0:
        tests["Docker daemon"] = "FAIL"
    else:
        for line in o_ps.strip().split("\n"):
            if "8002" in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    c_id, c_name = parts[0], parts[1]
                    tests["Port 8002 owner"] = f"Docker Container ({c_name})"
                    tests["Owner identified"] = "PASS"
                    if "stream" in c_name.lower() or "test" in c_name.lower():
                        tests["Stale CausalOps container"] = "YES"
                        stale_container_name = c_name
                    else:
                        tests["Stale CausalOps container"] = "NO"

    print("Checking netstat for 8002...")
    c_net, o_net, e_net = run_cmd("netstat -ano | findstr :8002")
    if o_net and "Owner identified" not in tests.values():
        lines = o_net.strip().split('\n')
        if lines:
            parts = lines[0].strip().split()
            if len(parts) >= 5:
                pid = parts[-1]
                tests["PID"] = pid
                c_task, o_task, _ = run_cmd(f"tasklist /FI \"PID eq {pid}\"")
                tests["Port 8002 owner"] = o_task.strip()
                tests["Owner identified"] = "PASS"
                tests["Stale CausalOps container"] = "NO"

    # Process cleanup
    if tests["Stale CausalOps container"] == "YES" and stale_container_name:
        print(f"Stopping and removing stale container: {stale_container_name}...")
        run_cmd(f"docker rm -f {stale_container_name}")
        tests["Cleanup performed"] = "PASS"
        
    print("Re-checking port 8002 availability...")
    # Re-verify
    c_net2, o_net2, e_net2 = run_cmd("netstat -ano | findstr :8002")
    c_ps2, o_ps2, e_ps2 = run_cmd("docker ps -a --format \"{{.Ports}}\"")
    
    port_free = True
    if o_net2 and "LISTENING" in o_net2:
        port_free = False
    if o_ps2 and "8002->" in o_ps2:
        port_free = False
        
    if port_free:
        tests["Port 8002 available"] = "PASS"

    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)
        
    print("FINISHED PORT DIAGNOSIS")

if __name__ == "__main__":
    diag()
