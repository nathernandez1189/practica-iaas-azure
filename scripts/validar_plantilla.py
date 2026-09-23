"""Comprueba SSH en la VM del catálogo y la desasigna al terminar."""
from extra_common import *
import time

part = 'plantilla'
cfg = PARTS[part]
private = private_dir(part)
result = {'parte': 3, 'fechaUtc': datetime.now(timezone.utc).isoformat(), 'vm': cfg['vm'], 'grupo': cfg['group'], 'catalogo': 'https://learn.microsoft.com/en-us/samples/azure/azure-quickstart-templates/vm-simple-linux/'}
try:
    vm = vm_info(part)
    assert vm['powerState'] == 'VM running'
    assert vm['tags']['practica'] == 'iaas'
    ip = str(ipaddress.IPv4Address(vm['publicIps']))
    print('Verificando identidad del servidor mediante Azure...', flush=True)
    response = az(['vm', 'run-command', 'invoke', '-g', cfg['group'], '-n', cfg['vm'], '--command-id', 'RunShellScript', '--scripts', 'set -eu\ncat /etc/ssh/ssh_host_ed25519_key.pub\nhostname\nlsb_release -ds'], timeout=360)
    evidence(part, 'identidad-servidor.json', response)
    message = '\n'.join(v.get('message', '') for v in response.get('value', []))
    match = re.search(r'^ssh-ed25519\s+([A-Za-z0-9+/=]+)', message, re.MULTILINE)
    assert match, 'No se obtuvo la clave del servidor.'
    hosts = private / 'known_hosts'
    hosts.write_text(ip + ' ssh-ed25519 ' + match.group(1) + '\n')
    hosts.chmod(0o600)
    print('Restringiendo SSH a las IP observadas de esta conexión...', flush=True)
    update_access(part)
    command = ['ssh', '-i', str(private / 'iaas_plantilla_rsa'), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(hosts), '-o', 'ConnectTimeout=10', 'azureuser@' + ip, 'set -e; printf "PLANTILLA_SSH_OK\\n"; whoami; hostname; lsb_release -ds; nproc; free -h; lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS']
    last_error = ''
    for attempt in range(6):
        p = subprocess.run(command, text=True, capture_output=True, timeout=45)
        if p.returncode == 0 and 'PLANTILLA_SSH_OK' in p.stdout:
            evidence(part, 'conexion-ssh.txt', p.stdout)
            result['ssh'] = 'correcto'
            result['estado'] = 'completado'
            print(p.stdout, flush=True)
            break
        last_error = p.stderr
        if attempt == 2:
            update_access(part)
        time.sleep(3)
    else:
        raise RuntimeError('No se confirmó SSH: ' + last_error)
finally:
    stop(part)
    result['estadoFinal'] = 'VM deallocated'
    evidence(part, 'resumen.json', result)
