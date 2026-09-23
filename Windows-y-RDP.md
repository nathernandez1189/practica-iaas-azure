# Punto 4: Windows y escritorio remoto

## Implementación

Se creó una VM independiente con **Windows Server 2022 Datacenter**, arquitectura x64 y generación 2. Se eligió la variante `2022-datacenter-smalldisk-g2`, con escritorio gráfico, y un disco de sistema de 32 GiB Standard HDD LRS. La máquina usa `Standard_B2als_v2`: dos CPU virtuales y 4 GiB de memoria, con Trusted Launch, arranque seguro y TPM virtual.

| Elemento | Valor |
|---|---|
| VM | `vm-win-iaas` |
| Grupo de recursos | `rg-iaas-windows` |
| Región de la VM y su red | `northcentralus` |
| Usuario local | `azureuser` |
| Acceso | RDP sobre TCP 3389 |
| Cliente | Windows App 11.4.1 para macOS |
| Autenticación de nivel de red | Activada |

Chile Central ya tenía utilizadas las tres IP públicas Standard permitidas por su cuota regional. Se verificó disponibilidad en North Central US, una región autorizada por la política de la suscripción, y allí se desplegó Windows. El grupo de recursos se había creado durante la validación inicial en Chile Central; su ubicación de metadatos no cambia la región de la VM y su red.

## Red y credenciales

La regla RDP permite solamente las IP públicas observadas de la conexión del Mac, cada una con máscara `/32`. No se habilitó acceso RDP desde cualquier dirección de Internet. El archivo local `.rdp` no contiene la contraseña. La contraseña generada se conserva en `privado/windows/credenciales.json`, con permisos de lectura restringidos, y no se publica en GitHub.

Se verificaron desde el canal autenticado de Azure el servicio `TermService`, el puerto 3389 en escucha, la autenticación de nivel de red y el certificado presentado por el servicio. El usuario estaba habilitado y sin bloqueo. La conexión final mostró un escritorio Windows real en Windows App.

## Demostración realizada

Dentro del escritorio remoto se abrió PowerShell y se ejecutaron estos comandos, uno a uno:

```powershell
hostname
whoami
qwinsta
```

Los resultados mostraron `vm-win-iaas`, `vm-win-iaas\azureuser` y una sesión `rdp-tcp#0` en estado `Active`. Se guardó una captura local; queda fuera de GitHub porque el título de la ventana contiene la dirección pública del equipo.

También se consultó el registro de Windows para verificar un inicio de sesión remoto interactivo, evento de seguridad **4624 con tipo de inicio 10**, y se conservó el registro de Terminal Services. Esta verificación distingue una conexión real de una simple comprobación de que el puerto está abierto.

## Evidencias

- [Despliegue](evidencias/windows/despliegue.json).
- [Sistema operativo y servicio RDP](evidencias/windows/windows-y-servicio-rdp.json).
- [Cuenta de Windows](evidencias/windows/comprobacion-cuenta-rdp.json).
- [Descripción de la evidencia visual](evidencias/windows/evidencia-visual.json).
- [Registro de la sesión RDP](evidencias/windows/sesion-rdp.json).
- [Resumen de la validación](evidencias/windows/resumen.json).
- [Estado final](evidencias/windows/estado-final-vm.json).
- [Disco conservado](evidencias/windows/discos-conservados.json).

Después de validar la conexión se desasignó la VM y se conservó su disco. Los estados de los archivos son observaciones de esa ejecución; para consultar el estado actual usa `controlar_extra.py windows estado`.

## Explicación para la sustentación

Desplegué Windows Server con escritorio gráfico y me conecté desde el Mac usando Windows App y el protocolo RDP. La VM exige usuario y contraseña y mantiene autenticación de nivel de red. Restringí el puerto 3389 a las direcciones observadas de mi conexión. Mostré el equipo y la sesión activa desde PowerShell y contrasté la conexión con el registro de Windows. Al terminar desasigné la VM para detener el consumo de cómputo y conservar el sistema instalado.

## Referencias

- [Crear una VM Windows en Azure](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/quick-create-template).
- [Conectarse a una VM Windows mediante RDP](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/connect-rdp).
- [Estados de las máquinas y facturación](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing).
