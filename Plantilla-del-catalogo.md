# Punto 3: máquina virtual desde una plantilla del catálogo

## Selección

Se exploró el catálogo enlazado por el enunciado, que actualmente redirige a Microsoft Learn Samples. Se eligió **Deploy a simple Ubuntu Linux VM 20.04-LTS**, del repositorio oficial Azure Quickstart Templates. Aunque el título menciona 20.04, la versión del código seleccionada permite usar Ubuntu 22.04 mediante el parámetro `ubuntuOSVersion`.

- [Catálogo de Azure](https://learn.microsoft.com/en-us/samples/browse/?expanded=azure&products=azure-resource-manager).
- [Ficha de la plantilla seleccionada](https://learn.microsoft.com/en-us/samples/azure/azure-quickstart-templates/vm-simple-linux/).
- [Código original en la revisión utilizada](https://github.com/Azure/azure-quickstart-templates/blob/39628293ee6cc2833293c09ff1a19129916dedb6/quickstarts/microsoft.compute/vm-simple-linux/azuredeploy.json).
- [Original conservado](plantillas/catalogo-linux.original.json), [copia adaptada y desplegada](plantillas/catalogo-linux.adaptada.json) y [procedencia con hashes](plantillas/procedencia-catalogo.json).

## Qué despliega

| Recurso | Función |
|---|---|
| Máquina virtual | Ejecuta Ubuntu |
| Disco administrado del sistema | Almacena Ubuntu y sus archivos |
| Red virtual y subred | Organizan la conectividad privada |
| Interfaz de red | Conecta la VM con su red |
| IP pública | Permite llegar al servidor desde Internet |
| Grupo de seguridad de red | Limita las conexiones SSH |
| Extensión Guest Attestation | Complementa la configuración de Trusted Launch |

Los parámetros proporcionan nombres, región, tamaño, versión de Ubuntu y clave pública SSH. Las referencias y `dependsOn` indican a Azure qué recursos deben existir antes de crear otros. ARM interpreta el JSON y coordina el despliegue.

## Ajustes realizados

Se conservaron el original y la licencia del catálogo. La copia desplegada incorpora estos cambios explícitos:

1. IP pública **Standard estática**, porque la suscripción no admite IP Basic.
2. Origen de SSH como parámetro `/32`, en lugar de aceptar cualquier dirección. Para validar la conexión se permitieron únicamente las IP públicas observadas del acceso del Mac, cada una como `/32`.
3. Disco del sistema de **32 GiB Standard HDD LRS**, con conservación al eliminar la VM.
4. Contraseña nula cuando se utiliza autenticación SSH por clave.
5. Etiquetas para identificar los recursos de la práctica.

Se suministraron los parámetros `Ubuntu-2204`, `Standard_B2als_v2`, `TrustedLaunch` y `chilecentral`. El grupo es `rg-iaas-plantilla` y la VM es `vm-plantilla-iaas`.

## Resultado comprobado

La plantilla se validó y el despliegue terminó correctamente. Una conexión SSH real devolvió `PLANTILLA_SSH_OK`, Ubuntu 22.04.5 LTS, dos procesadores virtuales y aproximadamente 4 GiB de memoria. Después se desasignó la VM y se conservó su disco.

- [Despliegue](evidencias/plantilla/despliegue.json).
- [Conexión SSH](evidencias/plantilla/conexion-ssh.txt).
- [Resultado de la prueba](evidencias/plantilla/resumen.json).
- [Estado final](evidencias/plantilla/estado-final-vm.json).
- [Disco conservado](evidencias/plantilla/discos-conservados.json).

Estos archivos registran una ejecución; no son una consulta en tiempo real de Azure. Las IP, claves e identificadores sensibles están ocultos en las copias publicables.

## Explicación para la sustentación

Elegí una plantilla del catálogo oficial porque define los recursos y sus relaciones de forma declarativa. Revisé sus parámetros, adapté la red y el almacenamiento a esta suscripción y desplegué una VM independiente. Comprobé por SSH que el sistema creado era Ubuntu y que sus recursos coincidían con los parámetros. La ventaja es poder revisar y repetir la definición de infraestructura, controlando las diferencias entre despliegues.
