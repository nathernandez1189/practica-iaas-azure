# Práctica IaaS: guía completa para la sustentación

Esta práctica demuestra cómo administrar máquinas virtuales, almacenamiento y conexiones remotas en Azure. Azure se encarga de la infraestructura física; la estudiante configura los sistemas operativos, accesos y discos.

Se comprobaron los cuatro componentes técnicos: Ubuntu con SSH, disco adicional persistente, una VM desde una plantilla del catálogo y Windows con RDP. Esto no equivale a haber presentado la práctica al docente ni a haber verificado cada detalle del video original del curso.

## Máquinas de la demostración

| Punto | Máquina | Región | Qué mostrar |
|---|---|---|---|
| 1 y 2 | `vm-ubuntu-iaas` | Chile Central | Ubuntu, SSH, disco `/datos`, UUID y SHA256 |
| 3 | `vm-plantilla-iaas` | Chile Central | Plantilla oficial seleccionada, parámetros, recursos y acceso SSH |
| 4 | `vm-win-iaas` | North Central US | Windows Server 2022 y sesión de escritorio remoto RDP |

Cada VM tiene 2 CPU y 4 GiB. Ubuntu original tiene dos discos; las otras dos VM tienen un disco cada una. Los cuatro discos son de 32 GiB. Al cerrar la validación se desasignaron las máquinas y se conservaron los discos.

## Preparación en Warp

Ejecuta cada bloque por separado. Ante un error, detente y revisa el mensaje antes de continuar. Los comandos que dicen «Mac» van en Warp; los que dicen «Ubuntu» o «Windows» van dentro de la sesión remota correspondiente.

```bash
cd /ruta/a/practica-iaas-azure
export AZURE_SUBSCRIPTION_ID='ID_DE_TU_SUSCRIPCION'
az account show --subscription "$AZURE_SUBSCRIPTION_ID" --query '{Suscripcion:name,Estado:state}' -o table
```

El resultado esperado es `Azure for Students` y `Enabled`. Si la sesión ha vencido, ejecuta `az login` y vuelve a comprobarla. Sustituye la ruta y el identificador por los de tu equipo. Si usas una carpeta propia para Azure CLI, define AZURE_CONFIG_DIR antes de autenticarte. Una copia recién clonada de GitHub no contiene las claves ni las credenciales originales: deben estar disponibles localmente en privado/. La guía local del Mac original contiene sus rutas exactas.

Para abrir esta guía en el navegador:

```bash
open "https://github.com/nathernandez1189/practica-iaas-azure/blob/main/Guia-completa-sustentacion.md"
```

## Puntos 1 y 2: Ubuntu y almacenamiento

En el Mac:

```bash
python3 scripts/controlar_vm.py iniciar
```

Copia la línea SSH que imprime el programa y ejecútala. Cuando veas el usuario `azureuser` dentro de Ubuntu, ejecuta:

```bash
hostname
lsb_release -ds
lsblk -o NAME,HCTL,SIZE,FSTYPE,MOUNTPOINTS
findmnt /datos
df -hT /datos
cat /datos/prueba-iaas.txt
cd /datos && sha256sum --check SHA256SUMS
```

Debes mostrar Ubuntu 22.04, el disco ext4 montado en `/datos` y dos resultados `OK`. Explica que `/etc/fstab` utiliza el UUID para conservar el montaje aunque cambie el nombre del dispositivo.

Sal de Ubuntu:

```bash
exit
```

En el Mac, muestra la evidencia del reinicio ya realizado y desasigna esta VM:

```bash
cat evidencias/08-persistencia-tras-reinicio.txt
python3 scripts/controlar_vm.py detener
```

El archivo acredita el cambio de identificador de arranque y la persistencia de los archivos. No es un reinicio nuevo ejecutado durante esta demostración.

## Punto 3: plantilla del catálogo

Abre la ficha oficial y explica el contenido de [Plantilla-del-catalogo.md](Plantilla-del-catalogo.md):

```bash
open "https://learn.microsoft.com/en-us/samples/azure/azure-quickstart-templates/vm-simple-linux/"
```

Muestra `plantillas/catalogo-linux.original.json`, `plantillas/catalogo-linux.adaptada.json` y los parámetros: Ubuntu 22.04, `Standard_B2als_v2`, Chile Central y SSH con clave. Explica la red, subred, interfaz, IP, regla SSH y VM que define la plantilla, junto con las adaptaciones documentadas.

En el Mac:

```bash
python3 scripts/controlar_extra.py plantilla iniciar
```

Copia y ejecuta el comando SSH que imprime. Dentro de esa segunda Ubuntu:

```bash
hostname
whoami
lsb_release -ds
nproc
```

Debe aparecer `vm-plantilla-iaas`, `azureuser`, Ubuntu 22.04 y `2`. Sal y, desde el Mac, desasigna:

```bash
exit
```

```bash
python3 scripts/controlar_extra.py plantilla detener
```

## Punto 4: Windows con RDP

En el Mac, inicia Windows:

```bash
python3 scripts/controlar_extra.py windows iniciar
```

Abre el archivo de conexión con Windows App:

```bash
open -b com.microsoft.rdc.macos "$PWD/privado/windows/Windows-IaaS.rdp"
```

Usuario: `vm-win-iaas\azureuser`. Consulta la contraseña solamente en tu terminal local cuando la necesites:

```bash
python3 -c "import json; from pathlib import Path; print(json.loads(Path('privado/windows/credenciales.json').read_text())['password'])"
```

Introduce esa contraseña en Windows App. El escritorio debe abrirse. No muestres la contraseña al compartir pantalla o grabar la sustentación.

Dentro de Windows, abre PowerShell desde **Server Manager → Tools → Windows PowerShell**. Escribe los comandos uno por uno:

```powershell
hostname
whoami
qwinsta
systeminfo
```

Explica el nombre `vm-win-iaas`, el usuario local, la sesión `rdp-tcp` activa y el sistema Windows Server 2022. Puedes complementar con el [registro de la conexión realizada](evidencias/windows/sesion-rdp.json).

Al terminar, vuelve a Warp en el Mac y desasigna Windows:

```bash
python3 scripts/controlar_extra.py windows detener
```

La sesión RDP se desconectará al detenerse la VM.

## Comprobación final desde el Mac

```bash
python3 scripts/controlar_extra.py plantilla estado
python3 scripts/controlar_extra.py windows estado
az vm show -g rg-practica-iaas -n vm-ubuntu-iaas --show-details --query powerState -o tsv
```

Las tres deben mostrar `VM deallocated`. La desasignación conserva los discos, pero el almacenamiento y las IP públicas pueden continuar consumiendo crédito. No se dejó un apagado programado configurado; utiliza los comandos `detener` al terminar.

## Preguntas que debes poder responder

- **¿Por qué IaaS?** Porque se administran máquinas virtuales, sistemas operativos, redes y discos sobre infraestructura física de Azure.
- **¿Para qué sirve una plantilla?** Para definir recursos, parámetros y dependencias de forma declarativa y poder revisar y repetir un despliegue.
- **¿Por qué usar UUID para el disco?** Porque el nombre `/dev/sdX` puede cambiar; el UUID identifica el sistema de archivos.
- **¿Qué diferencia SSH de RDP?** SSH proporciona una terminal remota; RDP permite trabajar con un escritorio gráfico remoto.
- **¿Por qué Windows está en otra región?** La cuota regional de IP públicas de Chile Central estaba completa; se comprobó capacidad en otra región permitida.
- **¿Apagar equivale a desasignar?** No. Desasignar libera la asignación de cómputo; se deben verificar el estado y los recursos que continúan generando cargos.
