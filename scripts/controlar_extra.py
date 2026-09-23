"""Inicia, consulta o desasigna las VM de plantilla y Windows."""
from extra_common import *
import argparse
import shlex

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('parte', choices=PARTS)
parser.add_argument('accion', choices=['iniciar', 'detener', 'estado'])
args = parser.parse_args()
cfg = PARTS[args.parte]
vm = vm_info(args.parte)
assert vm.get('tags', {}).get('practica') == 'iaas'
if args.accion == 'detener':
    stop(args.parte)
elif args.accion == 'estado':
    print(json.dumps({'vm': vm['name'], 'region': vm['location'], 'estado': vm['powerState']}, ensure_ascii=False, indent=2))
else:
    print('Iniciando VM. Al terminar usa la opción detener para desasignarla.', flush=True)
    try:
        az(['vm', 'start', '-g', cfg['group'], '-n', cfg['vm']], timeout=360)
        update_access(args.parte)
        vm = vm_info(args.parte)
        ip = str(ipaddress.IPv4Address(vm['publicIps']))
        folder = private_dir(args.parte)
        if args.parte == 'plantilla':
            print(shlex.join(['ssh', '-i', str(folder / 'iaas_plantilla_rsa'), '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(folder / 'known_hosts'), 'azureuser@' + ip]))
        else:
            rdp = folder / 'Windows-IaaS.rdp'
            if not rdp.exists():
                raise RuntimeError('Falta el archivo RDP local. Ejecuta preparar_windows_rdp.py.')
            lines = rdp.read_text().splitlines()
            rdp.write_text('\n'.join('full address:s:' + ip + ':3389' if line.startswith('full address:') else line for line in lines) + '\n')
            print('Abre Windows App con este comando:')
            print(shlex.join(['open', '-b', 'com.microsoft.rdc.macos', str(rdp)]))
            print('Usuario: ' + cfg['vm'] + '\\azureuser')
            print('La contraseña está en el archivo local privado/windows/credenciales.json.')
    except BaseException:
        stop(args.parte)
        raise
