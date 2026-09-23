"""Despliega únicamente las dos VM adicionales de la práctica."""
from extra_common import *
import argparse
import secrets
import string

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('parte', choices=PARTS)
args = parser.parse_args()
part = args.parte
cfg = PARTS[part]
location = cfg['location']
private = private_dir(part)

account = az(['account', 'show'])
assert account['state'] == 'Enabled' and account['id'] == SUBSCRIPTION
allowed = az(['policy', 'assignment', 'show', '--name', 'sys.regionrestriction', '--scope', '/subscriptions/' + SUBSCRIPTION, '--query', 'parameters.listOfAllowedLocations.value'])
assert location in allowed
group_exists = az(['group', 'exists', '-n', cfg['group']])
if group_exists:
    group = az(['group', 'show', '-n', cfg['group']])
    assert group.get('tags', {}).get('practica') == 'iaas'
    assert group.get('tags', {}).get('parte') == part
    assert not az(['vm', 'list', '-g', cfg['group']]), 'Ya existe una VM; no volver a desplegar.'

ip = source_ips()[0]
if part == 'plantilla':
    template = BASE / 'plantillas' / 'catalogo-linux.adaptada.json'
    key = private / 'iaas_plantilla_rsa'
    if not key.exists():
        subprocess.run(['ssh-keygen', '-q', '-t', 'rsa', '-b', '3072', '-N', '', '-C', 'practica-iaas-plantilla', '-f', str(key)], check=True)
    key.chmod(0o600)
    params = {'vmName': cfg['vm'], 'adminUsername': 'azureuser', 'authenticationType': 'sshPublicKey', 'adminPasswordOrKey': key.with_suffix('.pub').read_text().strip(), 'ubuntuOSVersion': 'Ubuntu-2204', 'location': location, 'vmSize': SIZE, 'virtualNetworkName': 'vnet-plantilla-iaas', 'subnetName': 'subnet-iaas', 'networkSecurityGroupName': cfg['nsg'], 'securityType': 'TrustedLaunch', 'sourceAddressPrefix': ip + '/32'}
else:
    template = BASE / 'plantillas' / 'windows-iaas.json'
    credential_file = private / 'credenciales.json'
    if not credential_file.exists():
        alphabet = string.ascii_letters + string.digits + '!@_-'
        password = 'Aa9!' + ''.join(secrets.choice(alphabet) for _ in range(24))
        private_json(credential_file, {'username': 'azureuser', 'password': password})
    credentials = json.loads(credential_file.read_text())
    params = {'vmName': cfg['vm'], 'adminUsername': credentials['username'], 'adminPassword': credentials['password'], 'location': location, 'vmSize': SIZE, 'sourceAddressPrefix': ip + '/32'}

params_file = private / 'parametros-despliegue.json'
private_json(params_file, {'$schema': 'https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#', 'contentVersion': '1.0.0.0', 'parameters': {k: {'value': v} for k, v in params.items()}})
if not group_exists:
    az(['group', 'create', '-n', cfg['group'], '-l', location, '--tags', 'practica=iaas', 'parte=' + part])
try:
    print('Validando plantilla de ' + part + '...', flush=True)
    validation = az(['deployment', 'group', 'validate', '-g', cfg['group'], '--template-file', str(template), '--parameters', '@' + str(params_file)], timeout=300)
    evidence(part, 'validacion-plantilla.json', {'estado': validation.get('properties', {}).get('provisioningState'), 'fechaUtc': datetime.now(timezone.utc).isoformat(), 'plantilla': template.name})
    print('Desplegando ' + cfg['vm'] + '...', flush=True)
    deployment = az(['deployment', 'group', 'create', '-g', cfg['group'], '-n', 'despliegue-' + part, '--template-file', str(template), '--parameters', '@' + str(params_file)], timeout=1200)
    evidence(part, 'despliegue.json', {'name': deployment['name'], 'state': deployment['properties']['provisioningState'], 'timestamp': deployment['properties'].get('timestamp'), 'template': template.name, 'resources': deployment['properties'].get('outputResources', [])})
    vm = vm_info(part)
    evidence(part, 'vm-creada.json', vm)
    print('Despliegue completado. Estado: ' + vm['powerState'] + '. Pendiente prueba de conexión y desasignación.', flush=True)
except BaseException:
    try:
        if az(['vm', 'list', '-g', cfg['group']]):
            stop(part)
    except Exception as stop_error:
        print('Debe comprobarse la desasignación: ' + str(stop_error), flush=True)
    raise
