from azure_lab import *
from datetime import datetime, timedelta, timezone
import ipaddress

print('Verificando suscripción y grupo exclusivo de la práctica...', flush=True)
account = az(['account', 'show'])
assert account['id'] == SUBSCRIPTION and account['state'] == 'Enabled'
if az(['group', 'exists', '--name', RG]):
    current_group = az(['group', 'show', '--name', RG])
    assert current_group.get('tags', {}).get('practica') == 'iaas'
    assert current_group.get('tags', {}).get('sesion') == '2026-09-22'
    existing_vms = az(['vm', 'list', '--resource-group', RG])
    assert not existing_vms, 'Ya existe una VM; revisar su estado antes de reanudar.'
policy = az(['policy', 'assignment', 'show', '--name', 'sys.regionrestriction', '--scope', f'/subscriptions/{SUBSCRIPTION}'])
assert LOCATION in policy['parameters']['listOfAllowedLocations']['value']

source_ip = subprocess.check_output(['curl', '-4', '--fail', '--silent', '--show-error', '--max-time', '20', 'https://api.ipify.org'], text=True).strip()
ipaddress.IPv4Address(source_ip)
private = BASE / 'privado'
private.mkdir(mode=0o700, exist_ok=True)
private.chmod(0o700)
key = private / 'iaas_ubuntu_rsa'
if not key.exists():
    subprocess.run(['ssh-keygen', '-q', '-t', 'rsa', '-b', '3072', '-N', '', '-C', 'practica-iaas-ubuntu', '-f', str(key)], check=True)
key.chmod(0o600)
public_key = key.with_suffix('.pub').read_text().strip()
derived_public = subprocess.check_output(['ssh-keygen', '-y', '-f', str(key)], text=True).strip()
assert derived_public.split()[:2] == public_key.split()[:2]
(private / '.gitignore').write_text('*\n')

tags = {'practica': 'iaas', 'sesion': '2026-09-22', 'proposito': 'Ubuntu y disco adicional'}
def rid(kind, name):
    return f'/subscriptions/{SUBSCRIPTION}/resourceGroups/{RG}/providers/{kind}/{name}'

nsg_name, vnet_name, pip_name, nic_name = 'nsg-ubuntu-iaas', 'vnet-practica-iaas', 'ip-ubuntu-iaas', 'nic-ubuntu-iaas'
nsg_id = rid('Microsoft.Network/networkSecurityGroups', nsg_name)
vnet_id = rid('Microsoft.Network/virtualNetworks', vnet_name)
pip_id = rid('Microsoft.Network/publicIPAddresses', pip_name)
nic_id = rid('Microsoft.Network/networkInterfaces', nic_name)
vm_id = rid('Microsoft.Compute/virtualMachines', VM)

resources = [
    {'type': 'Microsoft.Network/networkSecurityGroups', 'apiVersion': '2023-09-01', 'name': nsg_name, 'location': LOCATION, 'tags': tags,
     'properties': {'securityRules': [{'name': 'SSH-desde-mi-conexion', 'properties': {'priority': 1000, 'protocol': 'Tcp', 'access': 'Allow', 'direction': 'Inbound', 'sourceAddressPrefix': source_ip + '/32', 'sourcePortRange': '*', 'destinationAddressPrefix': '*', 'destinationPortRange': '22'}}]}},
    {'type': 'Microsoft.Network/virtualNetworks', 'apiVersion': '2023-09-01', 'name': vnet_name, 'location': LOCATION, 'tags': tags,
     'properties': {'addressSpace': {'addressPrefixes': ['10.42.0.0/16']}, 'subnets': [{'name': 'subnet-iaas', 'properties': {'addressPrefix': '10.42.1.0/24'}}]}},
    {'type': 'Microsoft.Network/publicIPAddresses', 'apiVersion': '2023-09-01', 'name': pip_name, 'location': LOCATION, 'tags': tags,
     'sku': {'name': 'Standard', 'tier': 'Regional'}, 'properties': {'publicIPAllocationMethod': 'Static', 'publicIPAddressVersion': 'IPv4'}},
    {'type': 'Microsoft.Network/networkInterfaces', 'apiVersion': '2023-09-01', 'name': nic_name, 'location': LOCATION, 'tags': tags,
     'dependsOn': [nsg_id, vnet_id, pip_id], 'properties': {'networkSecurityGroup': {'id': nsg_id}, 'ipConfigurations': [{'name': 'ipconfig1', 'properties': {'privateIPAllocationMethod': 'Dynamic', 'subnet': {'id': vnet_id + '/subnets/subnet-iaas'}, 'publicIPAddress': {'id': pip_id}}}]}},
    {'type': 'Microsoft.Compute/virtualMachines', 'apiVersion': '2024-07-01', 'name': VM, 'location': LOCATION, 'tags': tags,
     'dependsOn': [nic_id], 'properties': {
         'hardwareProfile': {'vmSize': 'Standard_B2als_v2'},
         'storageProfile': {'imageReference': {'publisher': 'Canonical', 'offer': '0001-com-ubuntu-server-jammy', 'sku': '22_04-lts-gen2', 'version': '22.04.202608060'}, 'osDisk': {'name': 'disco-so-ubuntu-iaas', 'createOption': 'FromImage', 'diskSizeGB': 32, 'caching': 'ReadWrite', 'managedDisk': {'storageAccountType': 'Standard_LRS'}, 'deleteOption': 'Detach'}},
         'osProfile': {'computerName': VM, 'adminUsername': 'azureuser', 'linuxConfiguration': {'disablePasswordAuthentication': True, 'provisionVMAgent': True, 'ssh': {'publicKeys': [{'path': '/home/azureuser/.ssh/authorized_keys', 'keyData': public_key}]}}},
         'securityProfile': {'securityType': 'TrustedLaunch', 'uefiSettings': {'secureBootEnabled': True, 'vTpmEnabled': True}},
         'networkProfile': {'networkInterfaces': [{'id': nic_id, 'properties': {'primary': True, 'deleteOption': 'Detach'}}]},
         'diagnosticsProfile': {'bootDiagnostics': {'enabled': True}}
     }}
]
template = {'$schema': 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#', 'contentVersion': '1.0.0.0', 'resources': resources}
template_path = private / 'despliegue-ubuntu.json'
template_path.write_text(json.dumps(template, indent=2))
template_path.chmod(0o600)

print('Creando grupo y desplegando Ubuntu con SSH limitado a tu IP...', flush=True)
az(['group', 'create', '--name', RG, '--location', LOCATION, '--tags', 'practica=iaas', 'sesion=2026-09-22'])
try:
    deployment = az(['deployment', 'group', 'create', '--resource-group', RG, '--name', 'ubuntu-iaas-inicial', '--template-file', str(template_path)], timeout=1200)
    save('01-despliegue-ubuntu.json', {'name': deployment['name'], 'provisioningState': deployment['properties']['provisioningState'], 'timestamp': deployment['properties'].get('timestamp')})
    vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
    save('02-configuracion-ubuntu.json', vm)
    print(json.dumps({'fase': 'Ubuntu creada', 'estado': vm.get('powerState'), 'ipPublica': vm.get('publicIps'), 'tamano': vm['hardwareProfile']['vmSize']}), flush=True)
    print('El apagado programado no está disponible en Chile Central; se desasignará al terminar las pruebas.', flush=True)
    print('Creando y conectando el disco adicional nuevo de 32 GiB...', flush=True)
    disk = az(['disk', 'create', '--resource-group', RG, '--name', 'disco-datos-iaas', '--location', LOCATION, '--size-gb', '32', '--sku', 'Standard_LRS', '--tags', 'practica=iaas'], timeout=180)
    save('03-disco-creado.json', disk)
    az(['vm', 'disk', 'attach', '--resource-group', RG, '--vm-name', VM, '--name', 'disco-datos-iaas', '--lun', '0', '--caching', 'None'], timeout=180)
    save('04-discos-conectados.json', az(['vm', 'show', '--resource-group', RG, '--name', VM, '--query', 'storageProfile']))
    print('VM lista. Disco adicional conectado en LUN 0. Pendiente preparar y verificar por SSH.', flush=True)
except Exception:
    print('La preparación tuvo un error; se intenta desasignar la VM para detener cómputo.', flush=True)
    try:
        az(['vm', 'deallocate', '--resource-group', RG, '--name', VM], timeout=300)
    except Exception as stop_error:
        print('No se pudo confirmar la desasignación: ' + str(stop_error), flush=True)
    raise
