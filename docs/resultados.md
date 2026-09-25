# Resultados, pruebas y trazabilidad

[Volver al README](../README.md)

## Qué se probó

| Prueba | Resultado registrado | Qué permite concluir |
|---|---|---|
| Acceso SSH a Ubuntu | `vm-ubuntu-iaas`, Ubuntu 22.04.5, 2 CPU | Se accedió a la VM y se consultó su sistema. |
| Montaje del disco | ext4, 32 GiB, `/datos` | El disco adjunto se pudo utilizar desde Linux. |
| Reinicio | Dos identificadores de arranque distintos | Ocurrió un nuevo arranque durante esa prueba. |
| Persistencia | Montaje presente y dos hashes `OK` tras reiniciar | Los archivos mantuvieron su contenido después del reinicio documentado. |
| Respaldo | SHA256 local coincidente | La copia local coincide con las sumas registradas. |
| Plantilla | Despliegue `Succeeded` y SSH a `vm-plantilla-iaas` | La definición produjo una segunda VM utilizable. |
| RDP | Nuevo inicio tipo 10, sesión `Active` y escritorio visible | Existió una conexión remota interactiva autenticada. |
| Cierre | Tres VM `deallocated` y cuatro discos `Reserved` | En esa consulta, el cómputo estaba desasignado y los discos conservados. |

## Fuentes primarias del repositorio

| Tema | Archivos |
|---|---|
| Ubuntu y disco | [SSH](../evidencias/verificacion-2026-09-23/ubuntu-ssh.txt), [montaje inicial](../evidencias/07-montaje-disco.txt), [reinicio](../evidencias/08-persistencia-tras-reinicio.txt), [respaldo](../evidencias/09-integridad-respaldo.json) |
| Plantilla | [JSON original](../plantillas/catalogo-linux.original.json), [adaptación](../plantillas/catalogo-linux.adaptada.json), [revisión y hashes](../plantillas/procedencia-catalogo.json), [despliegue](../evidencias/verificacion-2026-09-23/plantilla-despliegues.json), [SSH](../evidencias/verificacion-2026-09-23/plantilla-ssh.txt) |
| Windows | [Sistema](../evidencias/verificacion-2026-09-23/windows-sistema.json), [sesión](../evidencias/verificacion-2026-09-23/windows-sesion.json), [captura](../evidencias/capturas/windows-server-manager.jpg) |
| Red y cierre | [Reglas de acceso](../evidencias/verificacion-2026-09-23/reglas-acceso.json), [estado final](../evidencias/verificacion-2026-09-23/estado-final.json) |
| Incidencias | [Intentos y resultados Linux](../evidencias/verificacion-2026-09-23/linux-resumen.json) |

La comprobación final conservada tiene marca **2026-09-23T02:25:05 UTC**, equivalente al **22/09/2026, 21:25:05 en Bogotá**. Las marcas dentro de cada archivo describen etapas concretas; no todos los resúmenes se escribieron ni iniciaron al mismo tiempo.

## Captura, diagrama y registro no son lo mismo

- **Captura:** `windows-server-manager.jpg` es un archivo de imagen original de la sesión Windows. Se conserva sin editar y tiene SHA256 en su manifiesto.
- **Diagramas:** las figuras SVG son ilustraciones explicativas elaboradas a partir de la configuración y los registros. No se presentan como pantallas de Azure o capturas de terminal.
- **Registros:** TXT y JSON contienen las observaciones conservadas. Algunas respuestas de Azure incluyen otro JSON dentro de `value[].message`; el verificador lo interpreta para comprobar el contenido.
- **Datos ocultos:** las copias publicables reemplazan IP públicas, claves e identificadores de suscripción por marcadores. La transformación se explica en [el índice de evidencias](../evidencias/README.md).

La captura del escritorio, por sí sola, no prueba el usuario, la VM ni un inicio autenticado. Se complementa con la información del sistema y el registro de RDP. Del mismo modo, `Succeeded` indica resultado de aprovisionamiento; el acceso SSH constituye una comprobación adicional del huésped.

## Verificación local reproducible

Desde la raíz del repositorio:

```bash
python3 scripts/verificar_evidencias.py
```

La utilidad no requiere paquetes adicionales, suscripción ni credenciales. Un resultado correcto significa que las evidencias locales son coherentes con las comprobaciones programadas. No certifica su origen externo de manera independiente, no sustituye la revisión del docente y no consulta el estado actual de las VM.

El verificador comprueba:

1. Lectura de todos los JSON publicados en `evidencias/` y `plantillas/`.
2. Hashes del original y la adaptación de la plantilla frente a su procedencia.
3. Hashes de la captura y de la copia de registros incorporada.
4. Nuevo identificador de arranque y dos comprobaciones SHA256 correctas.
5. Identidad y sistema de ambas Ubuntu; despliegue ARM correcto.
6. Nuevo inicio RDP de tipo 10 y sesión activa en el registro.
7. Tres VM desasignadas y cuatro discos de 32 GiB en la consulta final.
8. Enlaces locales y anclas de los documentos Markdown.
