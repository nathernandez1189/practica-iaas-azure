"""Iniciar o detener únicamente la VM Ubuntu de esta práctica."""
from azure_lab import *
from datetime import datetime, timedelta, timezone
import argparse
import ipaddress
import shlex

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('accion', choices=['iniciar', 'detener'])
args = parser.parse_args()
vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
assert vm.get('tags', {}).get('practica') == 'iaas'

if args.accion == 'iniciar':
    from ssh_lab import SSH_OPTIONS, ensure_connection
    print('Iniciando Ubuntu. Comienza el consumo de cómputo. Al terminar ejecuta este programa con la opción detener; esta región no admite apagado programado.', flush=True)
    az(['vm', 'start', '--resource-group', RG, '--name', VM], timeout=360)
    vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
    public_ip = str(ipaddress.IPv4Address(vm['publicIps']))
    try:
        ensure_connection(public_ip)
    except Exception:
        az(['vm', 'deallocate', '--resource-group', RG, '--name', VM], timeout=360)
        raise
    print('Estado: ' + vm['powerState'])
    command = ['ssh', *SSH_OPTIONS, f'azureuser@{public_ip}']
    print('Para entrar a Ubuntu, ejecuta:\n' + shlex.join(command))
else:
    print('Deteniendo y desasignando Ubuntu, conservando sus discos...', flush=True)
    az(['vm', 'deallocate', '--resource-group', RG, '--name', VM], timeout=360)
    vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
    assert vm['powerState'] == 'VM deallocated'
    print('Confirmado: VM desasignada. Se conserva el almacenamiento.')
