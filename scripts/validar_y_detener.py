from azure_lab import *
import hashlib
import ipaddress
import re
import time
from datetime import datetime, timezone
from ssh_lab import SSH_OPTIONS, ensure_connection

EVIDENCES.mkdir(parents=True, exist_ok=True)
private = BASE / 'privado'
key = private / 'iaas_ubuntu_rsa'
known_hosts = private / 'known_hosts'
verification = {'fechaUtc': datetime.now(timezone.utc).isoformat(), 'vm': VM, 'grupo': RG, 'region': LOCATION}


def ssh(command, *, input=None, timeout=120, attempts=1):
    for attempt in range(attempts):
        p = subprocess.run(['ssh', *SSH_OPTIONS, f'azureuser@{public_ip}', command],
                           text=True, input=input, capture_output=True, timeout=timeout)
        if p.returncode == 0:
            return p.stdout
        if p.returncode != 255 or attempt == attempts - 1:
            raise RuntimeError(p.stderr + '\n' + p.stdout)
        time.sleep(5)


try:
    vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
    assert vm['powerState'] == 'VM running'
    assert vm['hardwareProfile']['vmSize'] == 'Standard_B2als_v2'
    disks = vm['storageProfile']['dataDisks']
    assert len(disks) == 1 and disks[0]['lun'] == 0 and disks[0]['name'] == 'disco-datos-iaas'
    public_ip = str(ipaddress.IPv4Address(vm['publicIps']))
    verification['ipPublica'] = public_ip
    if not known_hosts.exists():
        print('Obteniendo la clave pública del servidor por el canal autenticado de Azure...', flush=True)
        bootstrap = az(['vm', 'run-command', 'invoke', '--resource-group', RG, '--name', VM,
                    '--command-id', 'RunShellScript', '--scripts',
                    'set -eu\ncat /etc/ssh/ssh_host_ed25519_key.pub\nlsblk -o NAME,HCTL,SIZE,FSTYPE,MOUNTPOINTS\nreadlink -f /dev/disk/azure/scsi1/lun0'], timeout=300)
        save('05-identidad-servidor-y-discos.json', bootstrap)
        message = '\n'.join(v.get('message', '') for v in bootstrap.get('value', []))
        match = re.search(r'^ssh-ed25519\s+([A-Za-z0-9+/=]+)(?:\s.*)?$', message, flags=re.MULTILINE)
        assert match, 'Azure no devolvió la clave pública SSH del servidor.'
        known_hosts.write_text(f'{public_ip} ssh-ed25519 {match.group(1)}\n')
        known_hosts.chmod(0o600)

    print('Comprobando conexión SSH y Ubuntu...', flush=True)
    ensure_connection(public_ip)
    initial = ssh('set -e; whoami; hostname; lsb_release -ds; uname -m; free -h; lsblk -o NAME,HCTL,SIZE,FSTYPE,MOUNTPOINTS; command -v parted; sudo -n true', attempts=6)
    (EVIDENCES / '06-conexion-ssh.txt').write_text(initial)
    print(initial, flush=True)
    verification['ssh'] = 'correcto'
    print('Preparando el disco nuevo y configurando montaje persistente en /datos...', flush=True)
    mounted = ssh('sudo bash -s', input=(BASE / 'scripts' / 'preparar_disco.sh').read_text(), timeout=180)
    (EVIDENCES / '07-montaje-disco.txt').write_text(mounted)
    print(mounted, flush=True)
    verification['montaje'] = '/datos'
    verification['sistemaArchivos'] = 'ext4'
    boot_before = ssh('cat /proc/sys/kernel/random/boot_id').strip()
    print('Reiniciando Ubuntu para probar que el montaje y los archivos persisten...', flush=True)
    az(['vm', 'restart', '--resource-group', RG, '--name', VM], timeout=300)
    ensure_connection(public_ip)
    after = ssh('set -e; test "$(findmnt -n -o TARGET --mountpoint /datos)" = /datos; test "$(findmnt -n -o FSTYPE --mountpoint /datos)" = ext4; cd /datos; sha256sum --check SHA256SUMS; findmnt /datos; df -hT /datos; cat prueba-iaas.txt', attempts=12)
    boot_after = ssh('cat /proc/sys/kernel/random/boot_id').strip()
    assert boot_after and boot_before != boot_after, 'No se confirmó un nuevo arranque.'
    (EVIDENCES / '08-persistencia-tras-reinicio.txt').write_text(f'Arranque anterior: {boot_before}\nArranque nuevo: {boot_after}\n\n{after}')
    verification['persistenciaTrasReinicio'] = 'correcta: montaje automático y ambos SHA256 intactos'
    print(after, flush=True)

    print('Guardando respaldo local de los archivos de prueba y verificando integridad...', flush=True)
    backup = private / 'respaldo-datos'
    backup.mkdir(mode=0o700, exist_ok=True)
    files = ['prueba-iaas.txt', 'prueba-persistencia.bin', 'SHA256SUMS']
    scp = ['scp', *SSH_OPTIONS]
    scp.extend(f'azureuser@{public_ip}:/datos/{name}' for name in files)
    subprocess.run([*scp, str(backup)], check=True, capture_output=True, text=True, timeout=90)
    hashes = {}
    for line in (backup / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        actual = hashlib.sha256((backup / name).read_bytes()).hexdigest()
        assert actual == expected, f'Fallo de integridad de {name}'
        hashes[name] = actual
    save('09-integridad-respaldo.json', {'estado': 'correcto', 'sha256': hashes})
    verification['respaldoLocal'] = 'correcto; SHA256 verificados'
    verification['pruebas'] = 'completadas'
finally:
    print('Deteniendo y desasignando la VM; se conservan los discos...', flush=True)
    az(['vm', 'deallocate', '--resource-group', RG, '--name', VM], timeout=360)
    final_vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
    assert final_vm.get('powerState') == 'VM deallocated', final_vm.get('powerState')
    final_disks = az(['disk', 'list', '--resource-group', RG, '--query', '[].{name:name,sizeGB:diskSizeGB,sku:sku.name,state:diskState,managedBy:managedBy,provisioningState:provisioningState}'])
    save('10-estado-final-vm.json', final_vm)
    save('11-discos-conservados.json', final_disks)
    verification['estadoFinal'] = final_vm['powerState']
    verification['discosConservados'] = [d['name'] for d in final_disks]
    save('12-resumen-validacion.json', verification)
    print(json.dumps(verification, ensure_ascii=False), flush=True)
