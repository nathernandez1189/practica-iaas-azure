# Ubuntu y almacenamiento persistente

[Inicio](../README.md) · [Guía técnica](../Guia-tecnica.md)

## 1. Configuración de Ubuntu

La VM `vm-ubuntu-iaas` se creó con Ubuntu Server 22.04 LTS, x64 y generación 2. El tamaño `Standard_B2als_v2` aporta 2 vCPU y 4 GiB de RAM nominales. Se configuró acceso SSH con clave, autenticación por contraseña deshabilitada, Trusted Launch, arranque seguro y TPM virtual.

La red usa una interfaz asociada a la subred del laboratorio, IP pública Standard y un grupo de seguridad con acceso TCP 22 desde un origen `/32`. Los nombres y propiedades están en la [configuración de Azure](../evidencias/02-configuracion-ubuntu.json).

## 2. Identidad, sistema y recursos

Después de encender la VM y ejecutar el comando SSH, comprobar primero:

```bash
hostname
```

El resultado debe ser `vm-ubuntu-iaas`. Solo dentro de esa sesión ejecutar:

```bash
lsb_release -ds
nproc
free -h
```

La [validación conservada](../evidencias/verificacion-2026-09-23/ubuntu-ssh.txt) registró Ubuntu 22.04.5 LTS, dos procesadores y 3.8 GiB de memoria utilizable. La diferencia con los 4 GiB nominales no significa que se haya elegido otra SKU; la configuración de la VM y la memoria presentada al sistema son mediciones distintas.

## 3. Adjuntar, preparar y montar

| Etapa | Acción realizada | Evidencia |
|---|---|---|
| Crear | Disco administrado `disco-datos-iaas`, 32 GiB, `Standard_LRS` | [Disco creado](../evidencias/03-disco-creado.json) |
| Adjuntar | Conectarlo a la VM como disco de datos en LUN 0 | [Perfil de almacenamiento](../evidencias/04-discos-conectados.json) |
| Identificar | Resolver `/dev/disk/azure/scsi1/lun0`; comprobar tamaño, montajes, particiones y firmas | [Programa de preparación](../scripts/preparar_disco.sh) |
| Preparar | Tabla GPT, una partición y sistema de archivos ext4 | [Registro de preparación](../evidencias/07-montaje-disco.txt) |
| Montar | Crear `/datos`, montar y asignar permisos al usuario del laboratorio | [Montaje e integridad](../evidencias/07-montaje-disco.txt) |
| Hacer persistente | Registrar UUID y `nofail` en `/etc/fstab` | [Configuración de montaje](../evidencias/07-montaje-disco.txt) |

Adjuntar hace visible el dispositivo a la VM; montar asocia su sistema de archivos a una carpeta. La práctica tiene **un disco del sistema y uno de datos**, no dos copias del sistema operativo.

El formateo se aplicó al disco nuevo después de comprobar que estaba vacío. El programa se detiene si encuentra particiones o firmas previas. Las consultas siguientes son suficientes para comprobar el disco existente; no se debe repetir su formateo.

```bash
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
findmnt /datos
df -hT /datos
findmnt --fstab --target /datos
```

La entrada documentada es:

```text
UUID=ef492f4a-1423-404e-98e1-6cc1392162b1 /datos ext4 defaults,nofail 0 2
```

El UUID identifica el sistema de archivos. `nofail` permite que el arranque continúe si ese montaje de datos no está disponible; no es una garantía de que el disco esté sano. El UUID anterior pertenece a esta ejecución y no debe copiarse al preparar otro disco. [Referencia de montaje de Microsoft](https://learn.microsoft.com/en-us/azure/virtual-machines/linux/attach-disk-portal).

## Prueba de persistencia

![Evidencia comparada del montaje y la integridad después del reinicio](figuras/persistencia.svg)

La prueba no se limitó a encontrar archivos en una sesión ya abierta:

1. Se crearon un archivo de texto y un archivo binario de 1 MiB en `/datos`.
2. Se registraron sus SHA256 en `SHA256SUMS`.
3. Se guardó el identificador de arranque de `/proc/sys/kernel/random/boot_id`.
4. Se reinició la VM y se comprobó un identificador de arranque distinto.
5. Se verificaron el montaje automático, ext4 y los mismos hashes.
6. Se copió un respaldo al equipo administrador y se contrastó su integridad.

| Observación | Antes | Después |
|---|---|---|
| Dispositivo del montaje | `/dev/sdb1` | `/dev/sda1` |
| Carpeta | `/datos` | `/datos` |
| Identificador de arranque | `b9d6c39f-baf9-446b-934b-3b45bcf4b241` | `9e8bbc42-4fc5-4aa6-b89d-3f39fb265f1b` |
| SHA256 del texto y del binario | Registrados y comprobados | Ambos `OK` |

Fuentes: [montaje inicial](../evidencias/07-montaje-disco.txt), [nuevo arranque](../evidencias/08-persistencia-tras-reinicio.txt) e [integridad del respaldo](../evidencias/09-integridad-respaldo.json).

El cambio de dispositivo demuestra por qué no conviene depender de nombres como `/dev/sda1`: el montaje se mantuvo usando el UUID. Los hashes prueban integridad respecto a las sumas guardadas; por sí solos no prueban que ocurrió un reinicio ni sustituyen una política de copias de seguridad.

## 4. Comprobación de los archivos

Dentro de Ubuntu:

```bash
cat /datos/prueba-iaas.txt
cd /datos
sha256sum --check SHA256SUMS
```

Resultado registrado:

```text
prueba-iaas.txt: OK
prueba-persistencia.bin: OK
```

La verificación posterior del 23/09 UTC también registró `LECTURA_ESCRITURA_OK`: se comprobó escritura y lectura con un archivo temporal retirado al terminar. Sus resultados están en [ubuntu-ssh.txt](../evidencias/verificacion-2026-09-23/ubuntu-ssh.txt).

## 5. Cierre

La [validación final](../evidencias/verificacion-2026-09-23/estado-final.json) documentó las VM desasignadas y sus discos conservados. Es una observación de esa fecha; para una consulta actual utilizar los pasos de cierre de la [guía técnica](../Guia-tecnica.md#6-cierre-conservando-los-datos).
