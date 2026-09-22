from azure_lab import *
from datetime import datetime, timedelta, timezone

vm = az(['vm', 'show', '--resource-group', RG, '--name', VM, '--show-details'])
assert vm.get('tags', {}).get('practica') == 'iaas'
assert vm['hardwareProfile']['vmSize'] == 'Standard_B2als_v2'
assert not vm['storageProfile']['dataDisks'], 'Ya hay un disco conectado; revisar antes de continuar.'
assert vm['powerState'] == 'VM deallocated'
try:
    save('00-apagado-de-respaldo.json', {'configurado': False, 'motivo': 'Microsoft.DevTestLab/schedules no está disponible en chilecentral y exige la misma región de la VM. Se verificará la desasignación directa al terminar.'})
    print('Creando disco adicional de 32 GiB y conectándolo a Ubuntu...', flush=True)
    disk = az(['disk', 'create', '--resource-group', RG, '--name', 'disco-datos-iaas', '--location', LOCATION, '--size-gb', '32', '--sku', 'Standard_LRS', '--tags', 'practica=iaas'], timeout=180)
    save('03-disco-creado.json', disk)
    az(['vm', 'disk', 'attach', '--resource-group', RG, '--vm-name', VM, '--name', 'disco-datos-iaas', '--lun', '0', '--caching', 'None'], timeout=180)
    save('04-discos-conectados.json', az(['vm', 'show', '--resource-group', RG, '--name', VM, '--query', 'storageProfile']))
    print('Iniciando Ubuntu con el disco adicional conectado...', flush=True)
    az(['vm', 'start', '--resource-group', RG, '--name', VM], timeout=360)
    print('Ubuntu lista para validar conexión SSH y preparar el disco.', flush=True)
except Exception as error:
    print(str(error), flush=True)
    print('Se conserva la VM desasignada para detener cómputo.', flush=True)
    az(['vm', 'deallocate', '--resource-group', RG, '--name', VM], timeout=360)
    raise
