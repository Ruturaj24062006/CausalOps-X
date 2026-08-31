import os
import json

def report_step20():
    report_file = os.path.abspath("artifacts/model2/step20/model2_v9_container_lifecycle_report.txt")
    json_report = os.path.abspath("artifacts/model2/step20/model2_v9_container_lifecycle_report.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    tests = {
        "Container started": "FAIL",
        "Container remained running": "FAIL",
        "Exit code": "128",
        "OOMKilled": "FALSE",
        "Restarting": "FALSE",
        "Uvicorn": "FAIL",
        "Health": "FAIL",
        "API route": "FAIL",
        "Container logs": "EMPTY / NOT REACHED",
        "Root cause": "docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint: Bind for 0.0.0.0:8002 failed: port is already allocated"
    }

    report = "FINAL VALIDATION REPORT\n=======================\n\n"
    for k, v in tests.items():
        report += f"{k}:\n{v}\n\n"
        
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
        
    with open(json_report, "w", encoding='utf-8') as f:
        json.dump(tests, f, indent=2)

if __name__ == "__main__":
    report_step20()
