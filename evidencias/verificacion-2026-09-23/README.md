# Verificación conservada del 23/09/2026 UTC

[Volver al índice](../README.md)

Estos registros corresponden a la noche del **22 de septiembre de 2026 en Colombia**. Se incorporaron al repositorio como copias de las evidencias ya anonimizadas; no se ejecutaron nuevamente las VM para producir esta documentación.

| Archivo | Contenido |
|---|---|
| [ubuntu-ssh.txt](ubuntu-ssh.txt) | Identidad, Ubuntu, recursos, montaje, hashes y lectura/escritura del disco. |
| [plantilla-ssh.txt](plantilla-ssh.txt) | Identidad y sistema de la VM creada desde la plantilla. |
| [plantilla-despliegues.json](plantilla-despliegues.json) | Despliegue ARM registrado como `Succeeded`. |
| [windows-sistema.json](windows-sistema.json) | Nombre de VM, Windows Server, CPU, memoria, servicio RDP y NLA. |
| [windows-sesion.json](windows-sesion.json) | Nuevo inicio de tipo 10 y sesión RDP activa. |
| [reglas-acceso.json](reglas-acceso.json) | Orígenes restringidos mediante entradas `/32`. |
| [estado-final.json](estado-final.json) | Tres VM desasignadas y cuatro discos conservados, consulta de las 02:25:05 UTC. |
| [linux-resumen.json](linux-resumen.json) | Intento con tiempo de espera agotado y comprobaciones posteriores satisfactorias. |

Las respuestas de Windows contienen un JSON adicional dentro de `value[].message`. El verificador interpreta ese contenido, no solo el estado de ejecución del comando de Azure.

El primer intento de actualizar la regla SSH de la plantilla superó 180 segundos. Se conserva junto con la posterior validación correcta. Los marcadores de IP y suscripción no son valores utilizables para conectarse.

[integridad.json](integridad.json) permite contrastar los SHA256 de estas ocho copias. Este manifiesto detecta cambios respecto a los hashes guardados; no certifica de forma independiente el origen de los registros. Ejecutar desde la raíz:

```bash
python3 scripts/verificar_evidencias.py
```
