# Práctica IaaS en Azure

Implementación y evidencias de cuatro componentes técnicos de una práctica de Azure Virtual Machines: Ubuntu, almacenamiento persistente, uso de una plantilla del catálogo y Windows con RDP.

**Empieza por la [guía completa para la sustentación](Guia-completa-sustentacion.md).** Incluye los comandos para el Mac, Ubuntu y Windows, resultados esperados y pasos para desasignar las máquinas al terminar.

| Componente | Resultado |
|---|---|
| Ubuntu y SSH | VM creada y conexión comprobada |
| Disco adicional | 32 GiB, ext4 en `/datos`, persistencia y SHA256 verificados tras reinicio |
| Plantilla del catálogo | Plantilla oficial seleccionada y documentada; VM independiente creada y acceso SSH comprobado |
| Windows y RDP | Windows Server 2022 creado; escritorio remoto y sesión interactiva comprobados |

## Documentación

- [Guía completa y comandos para la demostración](Guia-completa-sustentacion.md).
- [Ubuntu, disco adicional y prueba de persistencia](Resumen-y-sustentacion.md).
- [Plantilla seleccionada, recursos y cambios](Plantilla-del-catalogo.md).
- [Windows, red y conexión RDP](Windows-y-RDP.md).
- [Criterios de publicación de las evidencias](evidencias/README.md).
- [Enunciado del curso](referencias/2025-03%20Practica%20IaaS.pdf) y [guía de regiones](referencias/guia-regiones-azure.pdf).

## Recursos

| VM | Región | Tamaño | Discos |
|---|---|---|---|
| `vm-ubuntu-iaas` | `chilecentral` | B2als_v2, 2 CPU, 4 GiB | Dos de 32 GiB |
| `vm-plantilla-iaas` | `chilecentral` | B2als_v2, 2 CPU, 4 GiB | Uno de 32 GiB |
| `vm-win-iaas` | `northcentralus` | B2als_v2, 2 CPU, 4 GiB | Uno de 32 GiB |

Al finalizar las validaciones las tres VM quedaron desasignadas y sus discos conservados. Las evidencias son observaciones de esa ejecución, no un panel de estado actual. Iniciar una VM vuelve a consumir cómputo; los discos y las IP públicas conservados pueden generar cargos incluso con las VM desasignadas.

## Usar una copia clonada

Requisitos: Python 3, Azure CLI, OpenSSH y `curl`; Windows App para la parte de RDP en macOS. Autentícate con `az login` y define en tu terminal:

```bash
export AZURE_SUBSCRIPTION_ID='ID_DE_TU_SUSCRIPCION'
```

Si ya utilizas una carpeta propia para la sesión de Azure CLI, define `AZURE_CONFIG_DIR` antes de autenticarte. Para operar las VM existentes necesitas los archivos de acceso originales en tu carpeta local `privado/`; una copia de GitHub no incluye claves, contraseñas, archivos RDP ni respaldos. Los programas publicados requieren una suscripción explícita y escriben las nuevas evidencias en `resultados-locales/`, carpeta excluida de Git.

La guía con rutas locales corresponde al Mac donde se realizó la práctica. En otra copia, entra primero en la raíz del repositorio y configura la suscripción y los archivos privados antes de ejecutar los comandos.

## Despliegue y validación

Los programas `crear_ubuntu.py`, `desplegar_extra.py`, `validar_y_detener.py`, `validar_plantilla.py`, `preparar_windows_rdp.py` y `comprobar_sesion_rdp.py` documentan la automatización empleada. No es necesario volver a crear los recursos para sustentarlos: usa `controlar_vm.py` y `controlar_extra.py`.

`validar_y_detener.py` prepara y formatea un disco adicional nuevo tras comprobar que esté vacío; se detiene si detecta particiones o firmas previas. Está destinado a la creación inicial, no a repetir una demostración sobre el disco existente.

La plantilla oficial original se conserva junto con su licencia. La copia adaptada y su procedencia están en `plantillas/`. La definición ARM de Windows es propia y está separada del ejercicio de seleccionar una plantilla del catálogo.

## Alcance académico

Se comprobaron los objetivos técnicos descritos arriba. No se afirma haber reproducido cada detalle del video original del curso ni haber presentado o entregado la práctica ante el docente. El repositorio reúne lo implementado, la explicación y las evidencias para preparar esa sustentación.
