# Práctica IaaS en Azure

Implementación académica de una máquina virtual Ubuntu y un disco de datos persistente en Microsoft Azure. Incluye los programas utilizados, las evidencias de las pruebas y una guía para la sustentación.

**Última validación documentada: 22 de septiembre de 2026.** Al finalizar, la VM quedó detenida y desasignada (`VM deallocated`), con sus dos discos conservados. Este repositorio registra esa ejecución; no consulta el estado actual de Azure.

## Alcance

| Parte de la práctica | Estado documentado |
|---|---|
| Crear Ubuntu y conectarse por SSH | Completada |
| Añadir y montar un disco; probar persistencia tras reiniciar | Completada |
| Elegir una plantilla del catálogo de Azure y crear una VM desde ella | Pendiente |
| Crear Windows y conectarse por RDP | Pendiente |

Se utilizó una definición ARM propia para crear Ubuntu. Esto no sustituye el ejercicio de seleccionar y explicar una plantilla del catálogo. No se afirma haber reproducido todos los detalles del video del curso ni haber presentado la práctica al docente.

## Material

- [Resumen y guion de sustentación](Resumen-y-sustentacion.md).
- [Evidencias y criterios de publicación](evidencias/README.md).
- [Instrucciones del curso](referencias/2025-03%20Practica%20IaaS.pdf).
- [Guía de regiones](referencias/guia-regiones-azure.pdf).
- [Consulta histórica de tamaños disponibles](disponibilidad-vm.json).

## Configuración verificada

| Recurso | Configuración |
|---|---|
| Suscripción | Azure for Students |
| Grupo / VM | `rg-practica-iaas` / `vm-ubuntu-iaas` |
| Región | `chilecentral` |
| Ubuntu | 22.04 LTS, x64, generación 2 |
| Tamaño | `Standard_B2als_v2`: 2 vCPU, 4 GiB |
| Seguridad | Trusted Launch, arranque seguro y TPM virtual |
| Almacenamiento | Dos discos Standard HDD LRS de 32 GiB cada uno |
| Disco adicional | `disco-datos-iaas`, LUN 0, ext4, montado en `/datos` |
| Acceso | Clave SSH, puerto 22 limitado a una IP de origen `/32` |

La prueba de persistencia verificó el montaje automático por UUID y las sumas SHA256 de ambos archivos después de un reinicio real. También se comprobó la integridad de un respaldo local.

## Usar los programas

Requisitos: Python 3, Azure CLI, OpenSSH y `curl`, en macOS o Linux. No se necesitan paquetes adicionales de Python. Los programas están preparados para la configuración concreta de esta práctica y la política de regiones de Azure for Students.

Autentícate y revisa las suscripciones disponibles:

```bash
az login
az account list --query '[].{nombre:name,id:id,estado:state}' -o table
```

Selecciona el identificador correcto en tu terminal. Sustituye el texto de ejemplo por el ID de tu propia suscripción:

```bash
export AZURE_SUBSCRIPTION_ID='ID_DE_TU_SUSCRIPCION'
```

Si utilizas una carpeta de configuración de Azure CLI distinta de la habitual, define `AZURE_CONFIG_DIR` antes de autenticarte. Ninguna ruta personal ni credencial está incorporada a estos programas.

### Trabajar con la VM ya creada

Para conectarte necesitas los archivos originales de tu equipo en la carpeta local `privado/`: `iaas_ubuntu_rsa`, `iaas_ubuntu_rsa.pub` y `known_hosts`. Estos archivos se conservaron localmente y no se subieron a GitHub. No generes otra clave para intentar acceder a la VM existente.

Desde la raíz del repositorio, inicia la VM y actualiza la regla SSH para tu conexión:

```bash
python3 scripts/controlar_vm.py iniciar
```

El programa imprime el comando SSH para entrar. Para terminar, sal de SSH con `exit` y desasigna la VM desde tu terminal local:

```bash
python3 scripts/controlar_vm.py detener
```

El resultado esperado es `Confirmado: VM desasignada`. No hay apagado programado configurado para esta ejecución. Al iniciar la VM vuelve a consumirse cómputo; la desasignación conserva los discos y la IP, que pueden seguir generando cargos.

### Reproducir el despliegue en un entorno nuevo

Estos pasos crean recursos y consumen crédito. No son necesarios para mostrar la VM que ya existe. La creación comprueba que no haya una VM previa en el grupo.

```bash
python3 scripts/crear_ubuntu.py
python3 scripts/validar_y_detener.py
```

El segundo programa **formatea el disco adicional nuevo** después de comprobar LUN 0, tamaño de 32 GiB y ausencia de particiones, firmas y montajes. Se detiene si el disco ya tiene datos o particiones. Después prueba el montaje y la persistencia, guarda un respaldo local e intenta desasignar la VM incluso si falla una prueba. Si el proceso se interrumpe o pierde conexión, confirma el estado y ejecuta `controlar_vm.py detener`.

`conectar_disco_y_arrancar.py` es un auxiliar de recuperación para una VM desasignada que todavía no tiene discos de datos. No forma parte de la secuencia normal anterior.

Las nuevas evidencias se guardan en `resultados-locales/evidencias/`, excluida de Git porque puede contener IP e identificadores reales. Los archivos de `evidencias/` corresponden a la ejecución documentada y tienen esos datos ocultos.

### Regenerar el documento

```bash
python3 scripts/generar_resumen.py
```

Este comando reconstruye el resumen a partir de las evidencias históricas publicadas y no consulta ni modifica Azure.

## Publicación y datos locales

Las claves SSH, los archivos de autenticación, la plantilla expandida con datos reales y el respaldo de pruebas permanecen únicamente en el equipo original. Las evidencias publicadas conservan los resultados técnicos, con marcadores donde se ocultaron identificadores y direcciones. Consulta [la nota de evidencias](evidencias/README.md).
