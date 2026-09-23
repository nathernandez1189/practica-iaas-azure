"""Funciones para las partes de plantilla y Windows de la práctica."""
from azure_lab import BASE, ENV, SUBSCRIPTION, az, EVIDENCES
from pathlib import Path
from datetime import datetime, timezone
import ipaddress
import json
import re
import subprocess

LOCATION = 'chilecentral'
SIZE = 'Standard_B2als_v2'
PARTS = {
    'plantilla': {'group': 'rg-iaas-plantilla', 'vm': 'vm-plantilla-iaas', 'nsg': 'nsg-plantilla-iaas', 'rule': 'SSH', 'port': '22', 'location': 'chilecentral'},
    'windows': {'group': 'rg-iaas-windows', 'vm': 'vm-win-iaas', 'nsg': 'nsg-windows-iaas', 'rule': 'RDP-desde-mi-conexion', 'port': '3389', 'location': 'northcentralus'},
}
PRIVATE = BASE / 'privado'

def private_dir(part):
    folder = PRIVATE / part
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    folder.chmod(0o700)
    return folder

def private_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    path.chmod(0o600)

def redact(obj):
    if isinstance(obj, dict):
        hidden = {'keyData', 'adminPassword', 'password', 'macAddresses', 'vmId', 'uniqueId', 'etag'}
        return {k: ('<REDACTED>' if k in hidden and v else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    if not isinstance(obj, str):
        return obj
    text = obj.replace(SUBSCRIPTION, '<SUBSCRIPTION_ID>')
    def replace_ip(match):
        try:
            ip = ipaddress.IPv4Address(match.group())
        except ValueError:
            return match.group()
        return '<PUBLIC_IP>' if ip.is_global else match.group()
    text = re.sub(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])', replace_ip, text)
    text = re.sub(r'ssh-(?:rsa|ed25519) [A-Za-z0-9+/=]{60,}(?: [^\n]*)?', '<SSH_PUBLIC_KEY>', text)
    text = re.sub(r'[A-Za-z0-9.-]+\.cloudapp\.azure\.com', '<VM_FQDN>', text)
    return text

def evidence(part, name, value):
    folder = EVIDENCES / part
    folder.mkdir(parents=True, exist_ok=True)
    private_json(private_dir(part) / name, value)
    public = folder / name
    if isinstance(value, str):
        public.write_text(redact(value))
    else:
        public.write_text(json.dumps(redact(value), indent=2, ensure_ascii=False) + '\n')

def source_ips():
    values = []
    for number in range(8):
        url = 'https://api.ipify.org' if number % 2 == 0 else 'https://checkip.amazonaws.com'
        p = subprocess.run(['curl', '-4', '--fail', '--silent', '--show-error', '--max-time', '10', url], text=True, capture_output=True, timeout=15)
        if p.returncode == 0:
            value = str(ipaddress.IPv4Address(p.stdout.strip()))
            if value not in values:
                values.append(value)
    if not values:
        raise RuntimeError('No se pudo determinar la IP pública actual.')
    return values

def update_access(part):
    cfg = PARTS[part]
    values = source_ips()
    rule = az(['network', 'nsg', 'rule', 'update', '-g', cfg['group'], '--nsg-name', cfg['nsg'], '-n', cfg['rule'], '--source-address-prefixes', *[ip + '/32' for ip in values]])
    evidence(part, 'acceso-restringido.json', rule)
    return values

def vm_info(part):
    cfg = PARTS[part]
    return az(['vm', 'show', '-g', cfg['group'], '-n', cfg['vm'], '--show-details'])

def stop(part):
    cfg = PARTS[part]
    vm = vm_info(part)
    if vm.get('tags', {}).get('practica') != 'iaas':
        raise RuntimeError('La VM no tiene la etiqueta esperada de la práctica.')
    az(['vm', 'deallocate', '-g', cfg['group'], '-n', cfg['vm']], timeout=360)
    vm = vm_info(part)
    if vm.get('powerState') != 'VM deallocated':
        raise RuntimeError('No se confirmó la desasignación.')
    evidence(part, 'estado-final-vm.json', vm)
    evidence(part, 'discos-conservados.json', az(['disk', 'list', '-g', cfg['group'], '--query', '[].{name:name,sizeGB:diskSizeGB,sku:sku.name,state:diskState,managedBy:managedBy,provisioningState:provisioningState}']))
    print(part + ': VM desasignada; disco conservado.', flush=True)
