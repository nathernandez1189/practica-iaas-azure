from azure_lab import BASE
from pathlib import Path
import json
from datetime import datetime

result = json.loads((BASE / 'evidencias' / '12-resumen-validacion.json').read_text())
assert result.get('pruebas') == 'completadas'
assert result.get('estadoFinal') == 'VM deallocated'
vm = json.loads((BASE / 'evidencias' / '10-estado-final-vm.json').read_text())
disks = json.loads((BASE / 'evidencias' / '11-discos-conservados.json').read_text())
assert {d['name'] for d in disks} == {'disco-so-ubuntu-iaas', 'disco-datos-iaas'}
assert all(d['sizeGB'] == 32 and d['sku'] == 'Standard_LRS' and d['provisioningState'] == 'Succeeded' for d in disks)
assert vm['securityProfile']['securityType'] == 'TrustedLaunch'
assert vm['securityProfile']['uefiSettings']['secureBootEnabled'] is True
assert vm['securityProfile']['uefiSettings']['vTpmEnabled'] is True
py = 'python3'
control = Path('scripts/controlar_vm.py')

body = f'''# Práctica IaaS: Ubuntu y disco adicional

Validación realizada el 22 de septiembre de 2026. Estado observado en esa fecha: **VM detenida y desasignada, con los dos discos conservados**.

## Lo que quedó hecho

| Elemento | Configuración verificada |
|---|---|
| Suscripción | Azure for Students |
| Grupo | rg-practica-iaas |
| VM | vm-ubuntu-iaas |
| Región | Chile Central |
| Sistema | Ubuntu Server 22.04 LTS, x64, generación 2 |
| Tamaño | Standard_B2als_v2: 2 vCPU y 4 GiB de RAM |
| Seguridad | Trusted Launch, arranque seguro y TPM virtual |
| Disco del sistema | 32 GiB, Standard HDD LRS |
| Disco adicional | disco-datos-iaas, 32 GiB, Standard HDD LRS, LUN 0 |
| Sistema de archivos adicional | ext4 |
| Carpeta del disco | /datos |
| Conexión | SSH con clave, limitado a la IP de la conexión usada en la prueba |
| IP pública de la VM | Omitida en la copia publicada |

La región centralus indicada inicialmente en el PDF no figura entre las permitidas por esta suscripción. Chile Central está permitida. Se usó la alternativa B2als_v2 seleccionada para esta ejecución, con tarifa publicada; no se usó el tamaño DS1_v2 del ejemplo.

## Pruebas realizadas

1. Despliegue de Ubuntu completado en Azure.
2. Conexión SSH real desde el Mac, con verificación de la identidad del servidor mediante su clave pública obtenida desde Azure.
3. Identificación del disco nuevo por LUN 0, tamaño de 32 GiB, ausencia de particiones, montajes y firmas previas.
4. Creación de partición GPT y formato ext4 únicamente en ese disco nuevo.
5. Montaje en /datos y configuración en /etc/fstab mediante UUID y la opción nofail. Se conservó una copia del fstab anterior.
6. Escritura de prueba-iaas.txt y un archivo binario de 1 MiB. Registro de sus sumas SHA256.
7. Reinicio real de la VM: cambió el identificador de arranque, /datos se montó automáticamente y ambos archivos conservaron sus SHA256.
8. Respaldo local de los dos archivos y verificación de sus SHA256.
9. Desasignación final confirmada: VM deallocated. Ambos discos permanecen asociados a la VM.

En esta prueba el disco de datos pasó de /dev/sdb1 a /dev/sda1 después del reinicio. El montaje siguió funcionando porque /etc/fstab identifica el sistema de archivos por UUID, y no por ese nombre variable del dispositivo.

## Cómo mostrarlo en la sustentación

Puedes decir:

> Creé una máquina virtual Ubuntu en Azure para trabajar con infraestructura como servicio. Azure administra el hardware físico, mientras yo configuro el sistema operativo, los accesos y el almacenamiento. Añadí un disco administrado independiente del disco del sistema, lo preparé con ext4 y lo monté en /datos. Configuré el montaje por UUID para que funcionara después de reiniciar. Verifiqué la persistencia comprobando que los archivos conservaron sus sumas SHA256 tras el reinicio. Finalmente desasigné la máquina para dejar de consumir cómputo y conservé sus discos.

En la sesión SSH, estas consultas muestran el resultado sin modificarlo:

```bash
lsb_release -ds
lsblk -o NAME,HCTL,SIZE,FSTYPE,MOUNTPOINTS
findmnt /datos
df -hT /datos
cat /datos/prueba-iaas.txt
cd /datos
sha256sum --check SHA256SUMS
```

Los resultados esperados son Ubuntu 22.04, una partición ext4 montada en /datos y dos comprobaciones con resultado OK.

## Volver a iniciar y conectarse

Primero configura la suscripción y las claves locales según [README.md](README.md). Desde la raíz del repositorio, este comando actualiza la regla SSH para tu conexión actual e inicia la VM. Vuelve a consumir cómputo mientras permanezca iniciada:

```bash
"{py}" "{control}" iniciar
```

Al finalizar imprime el comando SSH exacto. Ejecútalo para entrar a Ubuntu. La clave y el registro de identidad del servidor están en la carpeta local privado; no son parte del material para entregar.

La conexión del Mac mostró varias IP públicas de salida durante esta ejecución. La utilidad comprueba las direcciones observadas, mantiene una sola dirección /32 en la regla SSH y conserva una sesión autenticada para evitar que cada comando abra una conexión nueva.

Para salir de SSH escribe `exit`. Después, desde la terminal del Mac, detén y desasigna la VM:

```bash
"{py}" "{control}" detener
```

Espera el mensaje «Confirmado: VM desasignada». También puedes comprobar en el portal que el estado sea «Detenida (desasignada)».

**No hay apagado programado configurado.** Se comprobó que Microsoft.DevTestLab/schedules no admite Chile Central y que no puede administrar esta VM desde otra región. Al volver a iniciar la VM debes detenerla con el comando anterior al terminar.

## Consumo de crédito

Tarifas públicas consultadas el 22 de septiembre de 2026, en USD:

| Concepto | Referencia |
|---|---:|
| B2als_v2 Linux encendida | 0,0526 por hora |
| Cada disco HDD LRS de 32 GiB | 2,1504 por mes |
| IP pública Standard IPv4 | 0,005 por hora |

Los dos discos y la IP equivalen aproximadamente a USD 7,95 por un mes de 730 horas si se conservan todo el periodo. Es una estimación de esas tarifas, no una factura ni el saldo disponible de tu cuenta. Las operaciones de disco y transferencias pueden sumar consumo. La VM desasignada deja de consumir cómputo; el almacenamiento y la IP se mantienen.

## Evidencias y respaldo

Las evidencias publicadas son copias con identificadores y direcciones de acceso ocultos. Las nuevas ejecuciones escriben en `resultados-locales/evidencias`, carpeta excluida de Git.

- [Resumen de validación](evidencias/12-resumen-validacion.json)
- [Conexión SSH y sistema operativo](evidencias/06-conexion-ssh.txt)
- [Preparación y montaje del disco](evidencias/07-montaje-disco.txt)
- [Persistencia después del reinicio](evidencias/08-persistencia-tras-reinicio.txt)
- [Integridad del respaldo local](evidencias/09-integridad-respaldo.json)
- [Estado final en Azure](evidencias/10-estado-final-vm.json)
- [Discos conservados](evidencias/11-discos-conservados.json)

El respaldo está en `privado/respaldo-datos`. En la VM, la configuración original de montajes se conserva como `/etc/fstab.antes-practica-iaas`.

## Alcance actual de la práctica

Los puntos de plantilla del catálogo y Windows con RDP se completaron después de la validación de Ubuntu y el disco. Consulta la [guía completa](Guia-completa-sustentacion.md), la [explicación de la plantilla](Plantilla-del-catalogo.md) y la [demostración Windows/RDP](Windows-y-RDP.md).

Se comprobaron los cuatro componentes técnicos. No se afirma haber reproducido cada detalle del video del curso ni haber presentado la práctica ante el docente.

## Referencias

- Documento del curso: 2025-03 Practica IaaS.pdf, compartido por la estudiante.
- Guía de regiones: guia-regiones-azure.pdf, compartida por la estudiante.
- [Montaje de un disco de datos en Linux](https://learn.microsoft.com/en-us/azure/virtual-machines/linux/attach-disk-portal).
- [Estados de VM y facturación](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing).
- [Consulta de tarifas oficiales](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices).
'''

path = BASE / 'Resumen-y-sustentacion.md'
path.write_text(body)
print(path)
