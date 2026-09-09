import subprocess

out = subprocess.check_output('kubectl get pods -n causalops -l app=postgres -o name', shell=True).decode().strip()
print('Postgres pod:', out)
try:
    cmd_count = f'kubectl exec -n causalops {out} -- psql -U causalops_user -d causalops_db -c "\\d telemetry_event"'
    res2 = subprocess.check_output(cmd_count, shell=True, stderr=subprocess.STDOUT)
    print('Schema:\n', res2.decode())
except subprocess.CalledProcessError as e:
    print('Exec psql failed:\n', e.output.decode() if e.output else str(e))
