# Captura original de Windows

[Volver al índice](../README.md)

![Windows Server Manager abierto en la sesión remota](windows-server-manager.jpg)

La imagen procede del archivo local conservado durante la validación del **23/09/2026 UTC**, llamado originalmente `verificacion-escritorio-2026-09-23.png`. Se publicó una copia binaria idéntica con un nombre descriptivo: **no se editó su contenido ni se generó artificialmente**.

La barra de título muestra el nombre de la conexión, «Windows IaaS - practica». No muestra IP pública, contraseña ni identificador de suscripción. La captura anterior con PowerShell y dirección de conexión se mantiene fuera del repositorio.

El [manifiesto de procedencia](procedencia.json) registra el nombre original, el alcance y el SHA256 de esta copia. Desde la raíz del repositorio:

```bash
python3 scripts/verificar_evidencias.py
```

La captura acredita que se mostró un escritorio remoto con Server Manager. Para identificar la VM y comprobar la autenticación se complementa con [el sistema consultado](../verificacion-2026-09-23/windows-sistema.json) y [el registro de sesión RDP](../verificacion-2026-09-23/windows-sesion.json). La explicación está en [Windows y RDP](../../Windows-y-RDP.md).

La fecha y hora visibles pertenecen al equipo remoto. Esta es evidencia histórica de aquella validación, no una consulta del estado actual.
