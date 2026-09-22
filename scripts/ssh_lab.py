from azure_lab import *
import ipaddress
import tempfile
import time

private = BASE / 'privado'
private.mkdir(mode=0o700, exist_ok=True)
control_file = private / 'ssh-control-path.txt'
if control_file.exists() and Path(control_file.read_text().strip()).parent.is_dir():
    control_path = control_file.read_text().strip()
else:
    control_path = str(Path(tempfile.mkdtemp(prefix='iaas-ssh-')) / 'control')
    control_file.write_text(control_path)

SSH_OPTIONS = ['-i', str(private / 'iaas_ubuntu_rsa'), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', f'UserKnownHostsFile={private / "known_hosts"}',
               '-o', 'ConnectTimeout=5', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=600',
               '-o', f'ControlPath={control_path}']


def ensure_connection(public_ip):
    candidates = []
    for number in range(8):
        url = 'https://api.ipify.org' if number % 2 == 0 else 'https://checkip.amazonaws.com'
        p = subprocess.run(['curl', '-4', '--fail', '--silent', '--show-error', '--max-time', '10', url],
                           text=True, capture_output=True, timeout=12)
        if p.returncode == 0:
            value = str(ipaddress.IPv4Address(p.stdout.strip()))
            if value not in candidates:
                candidates.append(value)
    assert candidates, 'No se pudo determinar la IP de salida actual.'
    last_rule = EVIDENCES / '13-regla-ssh-validada.json'
    if last_rule.exists():
        previous = json.loads(last_rule.read_text()).get('sourceAddressPrefix', '').split('/')[0]
        if previous and (previous in candidates or time.time() - last_rule.stat().st_mtime < 3600):
            if previous in candidates:
                candidates.remove(previous)
            candidates.insert(0, previous)
    print(f'Probando {len(candidates)} IP de salida observadas, manteniendo una sola /32 en cada intento...', flush=True)
    for source in candidates:
        print(f'Probando conexión con regla restringida a {source}/32...', flush=True)
        az(['network', 'nsg', 'rule', 'update', '--resource-group', RG, '--nsg-name', 'nsg-ubuntu-iaas',
            '--name', 'SSH-desde-mi-conexion', '--source-address-prefixes', source + '/32'])
        for attempt in range(3):
            p = subprocess.run(['ssh', *SSH_OPTIONS, f'azureuser@{public_ip}', 'printf CONEXION_SSH_CONFIRMADA'],
                               capture_output=True, text=True, timeout=15)
            if p.returncode == 0 and 'CONEXION_SSH_CONFIRMADA' in p.stdout:
                print('Conexión SSH autenticada y persistente establecida.', flush=True)
                save('13-regla-ssh-validada.json', {'sourceAddressPrefix': source + '/32', 'destinationPortRange': '22',
                                                 'conexion': 'SSH autenticada', 'direccionesObservadas': candidates})
                return
            time.sleep(2)
    raise RuntimeError('No fue posible conectar SSH usando las IP públicas observadas de esta conexión.')
