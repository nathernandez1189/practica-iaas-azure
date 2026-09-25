# Guía técnica de la práctica

[Volver al README](README.md)

Esta guía distingue el **despliegue inicial**, que crea recursos, de la **operación de recursos existentes**. Los nombres y regiones corresponden a la implementación documentada. Los scripts no son un instalador universal: antes de usarlos en otra suscripción deben revisarse nombres, regiones, imágenes, cuotas y parámetros.

## 1. Requisitos y entornos

- Python 3, Azure CLI, OpenSSH y `curl` en el equipo administrador.
- Una suscripción activa con permiso para crear y administrar los recursos del laboratorio.
- Un cliente RDP para Windows; en esta ejecución se usó Windows App en macOS.
- Para operar las VM existentes: las claves, archivos `known_hosts` y credenciales originales, guardados localmente en `privado/`. Clonar este repositorio no concede acceso a Azure.

| Entorno | Operaciones |
|---|---|
| Terminal local | Azure CLI, programas Python, abrir el cliente RDP |
| Ubuntu mediante SSH | `hostname`, `lsb_release`, `lsblk`, `findmnt`, `sha256sum` |
| Windows mediante RDP | PowerShell, `hostname`, `whoami`, `qwinsta` |

## 2. Autenticación y suscripción

Desde la raíz del repositorio, preparar opcionalmente una carpeta local para la sesión de Azure CLI. Se debe elegir antes de iniciar sesión; si ya se utiliza otra carpeta, conservar esa configuración.

```bash
export AZURE_CONFIG_DIR="$PWD/.azure"
az login
```

Seleccionar la suscripción correspondiente. Si hay varias, elegirla explícitamente:

```bash
az account set --subscription "NOMBRE_O_ID_DE_LA_SUSCRIPCION"
az account show --query '{Suscripcion:name,Estado:state}' -o table
export AZURE_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
```

Si la cuenta ya está autenticada y habilitada, no hace falta repetir `az login`. Los programas publicados leen `AZURE_SUBSCRIPTION_ID`; no incluyen un ID personal incrustado.

## 3. Verificar regiones, tamaño y cuota

Listar el catálogo geográfico de la suscripción:

```bash
az account list-locations --query '[].name' -o tsv
```

Consultar además la asignación de política que restringía las regiones de esta suscripción:

```bash
az policy assignment show \
  --name sys.regionrestriction \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID" \
  --query 'parameters.listOfAllowedLocations.value' -o tsv
```

Esa asignación puede tener otro nombre o no existir en otra suscripción. En ese caso, listar las asignaciones y revisar sus parámetros y ámbito:

```bash
az policy assignment list \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID" \
  --query '[].{Nombre:name,Titulo:displayName}' -o table
```

La lista geográfica, una política permisiva y la creación de un grupo de recursos no garantizan que se pueda desplegar cualquier VM. Revisar también SKU, cuota de cómputo y cuota de IP públicas:

```bash
az vm list-skus --location chilecentral \
  --resource-type virtualMachines --size Standard_B2als_v2 --all -o json
az vm list-usage --location chilecentral -o table
az network list-usages --location chilecentral -o table
```

El [inventario conservado](disponibilidad-vm.json) corresponde a la ejecución original; no reemplaza estas consultas. Ver [decisiones de región y tamaño](docs/decisiones-tecnicas.md).

## 4. Despliegue inicial

Esta sección **crea recursos y puede formatear un disco nuevo**. No debe repetirse sobre el disco existente para comprobar su funcionamiento. Revisar los programas y sus parámetros antes de ejecutarlos.

### Ubuntu y disco adicional

`crear_ubuntu.py` genera una definición ARM local, crea la VM, su red y un disco de datos de 32 GiB en LUN 0. Usa una clave generada localmente y limita SSH a una dirección de origen `/32`.

```bash
python3 scripts/crear_ubuntu.py
```

Para la primera preparación del disco, `validar_y_detener.py` obtiene la clave pública del servidor por el canal autenticado de Azure, verifica SSH y llama a `preparar_disco.sh`. Este último comprueba el dispositivo, su tamaño y la ausencia de firmas y particiones antes de prepararlo. Después se comprueba un nuevo arranque, se verifican hashes, se guarda un respaldo local y se desasigna la VM.

```bash
python3 scripts/validar_y_detener.py
```

`conectar_disco_y_arrancar.py` es una herramienta de recuperación para una VM que todavía **no tiene disco de datos conectado**; no forma parte de la secuencia normal después de `crear_ubuntu.py`, que ya lo adjunta.

### VM de la plantilla

```bash
python3 scripts/desplegar_extra.py plantilla
python3 scripts/validar_plantilla.py
```

Ejecutar una línea a la vez. La primera valida y despliega el JSON adaptado; la segunda verifica SSH y desasigna la VM al finalizar. La plantilla de Windows es una definición propia separada del ejercicio del catálogo.

### Windows y RDP

```bash
python3 scripts/desplegar_extra.py windows
python3 scripts/preparar_windows_rdp.py
```

La preparación consulta el sistema y el servicio RDP, actualiza el acceso restringido y genera un archivo `.rdp` local. **No abre por sí sola una sesión gráfica ni apaga Windows.** Abrir ese archivo en el cliente, introducir las credenciales locales y comprobar el escritorio. Después de una conexión satisfactoria:

```bash
python3 scripts/comprobar_sesion_rdp.py
```

Ese programa consulta las evidencias de sesión y desasigna Windows en su cierre. Si se interrumpe el procedimiento, comprobar expresamente el estado; no asumir que un error equivale a apagado.

## 5. Operar las VM existentes

### Encender y entrar a Ubuntu son dos pasos

Desde la terminal local:

```bash
python3 scripts/controlar_vm.py iniciar
```

Esperar a que termine. Este programa enciende la VM y actualiza la regla de origen para la conexión actual. **Ejecutar después el comando SSH que imprime**. El nombre corto `ssh ubuntu-iaas` es una configuración opcional del equipo original; no se instala al clonar el repositorio.

Una vez conectado:

```bash
hostname
```

Continuar solo si devuelve `vm-ubuntu-iaas`. Si devuelve el nombre del Mac, aún se está en la terminal local. Entonces comprobar el sistema y el disco según [Ubuntu y almacenamiento](docs/ubuntu-y-almacenamiento.md).

### Plantilla y Windows

```bash
python3 scripts/controlar_extra.py plantilla iniciar
```

Ejecutar la línea SSH que devuelve y comprobar `hostname`: debe ser `vm-plantilla-iaas`.

En otra terminal local, para Windows:

```bash
python3 scripts/controlar_extra.py windows iniciar
```

El programa actualiza la IP en el archivo RDP. Abrir el archivo con el cliente instalado. En macOS:

```bash
open -b com.microsoft.rdc.macos "$PWD/privado/windows/Windows-IaaS.rdp"
```

## 6. Cierre conservando los datos

Salir primero de las sesiones SSH con `exit`. Desde la terminal local, ejecutar una línea a la vez, cuando ya no se necesiten las VM:

```bash
python3 scripts/controlar_vm.py detener
python3 scripts/controlar_extra.py plantilla detener
python3 scripts/controlar_extra.py windows detener
```

Comprobar los tres recursos:

```bash
az vm show -g rg-practica-iaas -n vm-ubuntu-iaas \
  --show-details --query powerState -o tsv
python3 scripts/controlar_extra.py plantilla estado
python3 scripts/controlar_extra.py windows estado
```

Esperado: `VM deallocated` en las tres VM. Los programas conservan los discos; cerrar SSH o Windows App solo termina o desconecta la sesión. Los costos de almacenamiento y red se tratan en [decisiones técnicas](docs/decisiones-tecnicas.md#ciclo-de-vida-y-costos).

## 7. Diagnóstico de errores

| Síntoma | Comprobación y siguiente acción |
|---|---|
| `zsh: command not found: lsb_release` | Ejecutar `hostname`: si es el Mac, entrar por SSH antes de usar comandos Linux. |
| `RequestDisallowedByPolicy` | Revisar asignaciones y regiones permitidas; no cambiar de región al azar. |
| Error de cuota o capacidad | Revisar SKU, cuota de CPU e IP públicas en la región elegida. |
| SSH agota el tiempo | Revisar estado de la VM, IP de destino, origen `/32` autorizado y conectividad. |
| Verificación de clave SSH falla | Contrastar la identidad del servidor por un canal autenticado; no desactivar `StrictHostKeyChecking`. |
| Un comando de Azure agota el tiempo | Consultar el estado de la operación antes de repetir una creación o actualización. |
| RDP no conecta | Revisar VM, IP, regla de origen, puerto, servicio, usuario y contraseña. Un puerto abierto no prueba una sesión autenticada. |
| `/datos` no aparece | Comprobar `lsblk`, UUID y `/etc/fstab`; no volver a formatear un disco con datos. |

La resolución de un error se registra con su fecha. No sustituir un resultado fallido por un éxito de otra ejecución sin explicar la diferencia.
