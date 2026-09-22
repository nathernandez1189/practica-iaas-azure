# Evidencias de la ejecución

Estas son copias de los resultados obtenidos el 22 de septiembre de 2026. No representan una consulta en tiempo real ni nuevas pruebas ejecutadas al publicar el repositorio.

## Lectura recomendada

| Archivo | Qué acredita |
|---|---|
| [01-despliegue-ubuntu.json](01-despliegue-ubuntu.json) | Despliegue finalizado en Azure |
| [06-conexion-ssh.txt](06-conexion-ssh.txt) | Acceso SSH y sistema operativo |
| [07-montaje-disco.txt](07-montaje-disco.txt) | Formato, montaje y entrada persistente por UUID |
| [08-persistencia-tras-reinicio.txt](08-persistencia-tras-reinicio.txt) | Nuevo arranque, montaje y SHA256 correctos |
| [09-integridad-respaldo.json](09-integridad-respaldo.json) | Integridad del respaldo local |
| [10-estado-final-vm.json](10-estado-final-vm.json) | VM desasignada al terminar |
| [11-discos-conservados.json](11-discos-conservados.json) | Dos discos de 32 GiB conservados |
| [12-resumen-validacion.json](12-resumen-validacion.json) | Resultado conjunto de Ubuntu y disco |
| [14-seguridad-red.json](14-seguridad-red.json) | SSH limitado a un origen /32 |

Los estados intermedios, como un disco inicialmente `Unattached` o la VM `running`, corresponden a pasos previos; el estado final está en los archivos 10, 11 y 12. El resultado `pruebas: completadas` se refiere exclusivamente a Ubuntu y el disco adicional, no a todas las partes del enunciado.

## Datos ocultos

Se sustituyeron por marcadores el ID de suscripción, las IP públicas de la VM y de la conexión cliente, las claves públicas SSH y otros identificadores únicos de recursos. Se eliminaron caracteres de control de la salida de terminal para facilitar su lectura. Las claves privadas y los respaldos no se incluyeron.

Los marcadores `<SUBSCRIPTION_ID>`, `<VM_PUBLIC_IP>`, `<CLIENT_PUBLIC_IP>`, `<SSH_PUBLIC_KEY>` y `<REDACTED>` no son valores utilizables para operar Azure. Se conservaron nombres de recursos, fechas, tamaños, estados, configuración de seguridad, UUID del sistema de archivos e identificadores de arranque necesarios para entender las pruebas, así como los SHA256 de los archivos de prueba.

Los originales permanecen en el equipo de la estudiante. Los PDF en `referencias/` son el material del curso proporcionado para esta práctica; no son evidencias de ejecución.
