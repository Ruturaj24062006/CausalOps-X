import subprocess

out = subprocess.check_output('kubectl get pods -n causalops -l app=postgres -o name', shell=True).decode().strip()
print('Postgres pod:', out)
try:
    res = subprocess.check_output(['kubectl', 'exec', '-n', 'causalops', out, '--', 'psql', '-U', 'causalops', '-d', 'causalops', '-c', '\\dt'])
    print('Tables:', res.decode('utf-8', errors='replace'))
except Exception as e:
    print('Exec psql failed:', str(e))
