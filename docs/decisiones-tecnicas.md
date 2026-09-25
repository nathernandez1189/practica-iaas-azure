# Decisiones técnicas y límites

[Volver al README](../README.md)

## Regiones y tamaño

El enunciado propone Central US, Ubuntu 22.04 LTS x64 generación 2 y `Standard_DS1_v2`, y permite adaptar región o tamaño. La implementación mantuvo la imagen requerida y utilizó `Standard_B2als_v2`.

| Decisión | Motivo documentado | Evidencia o límite |
|---|---|---|
| Ubuntu en Chile Central | Usar una región autorizada por la política académica | La preparación consulta `sys.regionrestriction`; esa comprobación no sustituye la disponibilidad de SKU o cuota. |
| `Standard_B2als_v2` | Tamaño elegido para esta ejecución: 2 vCPU y 4 GiB | [Inventario consultado](../disponibilidad-vm.json). No se afirma que fuera el más económico de todas las opciones. |
| No usar DS1_v2 | Se eligió una alternativa; no se ha demostrado que DS1_v2 estuviera bloqueado en Chile Central | El inventario también enumera `Standard_DS1_v2` en esa región. |
| Windows en North Central US | Durante el despliegue se documentó agotamiento de la cuota de IP públicas Standard en Chile Central | La configuración y el resultado están en [Windows y RDP](../Windows-y-RDP.md). La cuota debe consultarse de nuevo antes de otro despliegue. |
| Disco Standard HDD LRS | Almacenamiento de laboratorio sin requisitos documentados de alto rendimiento | Cuatro discos de 32 GiB; no se realizó una comparación de IOPS o latencia. |

Las restricciones por política, la disponibilidad del tamaño y las cuotas son controles diferentes. El nombre de la región del grupo de recursos describe sus metadatos y no determina necesariamente dónde se ejecuta cada recurso.

## Seguridad de acceso

- **SSH con clave:** Ubuntu tiene autenticación por contraseña deshabilitada. La clave privada permanece en el equipo administrador.
- **Identidad del servidor:** la automatización obtiene la clave pública del servidor por Azure Run Command y utiliza `StrictHostKeyChecking=yes` en SSH.
- **Reglas de origen:** los accesos TCP 22 y TCP 3389 se limitaron a direcciones observadas de la conexión, cada una con máscara `/32`. No se publicó una regla abierta a cualquier origen para esos puertos.
- **RDP:** se mantuvo la autenticación de nivel de red. El archivo `.rdp` local no incorpora la contraseña.
- **Arranque:** la configuración registrada usa Trusted Launch, Secure Boot y vTPM.
- **Publicación:** el repositorio excluye claves, contraseñas, sesión de Azure CLI y nuevas salidas sin revisar. Las evidencias utilizan marcadores donde se ocultaron identificadores de acceso.

Las [reglas registradas](../evidencias/verificacion-2026-09-23/reglas-acceso.json) son históricas. Una conexión desde otra red puede necesitar actualizar la regla de origen. El alias SSH corto configurado en el equipo original no cambia las reglas ni concede acceso a quien clone el repositorio.

## Ciclo de vida y costos

| Acción | Efecto |
|---|---|
| Cerrar SSH o Windows App | Cierra o desconecta la sesión del cliente; no desasigna la VM. |
| Apagar dentro del sistema invitado | Puede dejar recursos de cómputo asignados. No equivale a desasignar. |
| Desasignar en Azure | Libera la asignación de cómputo. Se verifica `VM deallocated`. |
| Conservar discos e IP públicas | Mantiene recursos que pueden continuar generando cargos. |

La operación elegida al terminar fue **desasignar y conservar discos**, no eliminar los grupos de recursos. Las tarifas históricas guardadas bajo `evidencias/windows/` y `evidencias/plantilla/` son consultas de referencia, no una factura ni precios actuales. No se calcula un costo final sin considerar duración, almacenamiento, operaciones y red. [Estados y facturación oficiales](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing).

La ejecución documentó que no se pudo configurar el recurso de apagado programado previsto para esa VM en Chile Central. Por ello el cierre se realiza mediante los programas de desasignación y se comprueba al finalizar. Es una limitación observada en la ejecución, no una afirmación permanente sobre toda la plataforma. [Registro](../evidencias/00-apagado-de-respaldo.json).

## Incidencia observada

Durante la verificación del 23/09 UTC, una actualización de la regla SSH de la plantilla superó los 180 segundos de espera de la herramienta. La ejecución posterior confirmó el acceso SSH y el despliegue en `Succeeded`. El [registro conserva el primer error y los resultados posteriores](../evidencias/verificacion-2026-09-23/linux-resumen.json); no se eliminó el intento fallido de la secuencia.

## Límites y posibles mejoras

No se implementó alta disponibilidad, balanceo ni recuperación ante pérdida regional. El respaldo local de los archivos de prueba no equivale a una solución administrada de backup. Tampoco se midieron rendimiento, disponibilidad sostenida o costos finales.

Como trabajo futuro, podrían evaluarse Azure Backup, acceso privado o Bastion, presupuestos y alertas de costo, y parámetros externos para adaptar los scripts a distintas suscripciones. **Son propuestas, no componentes implementados en esta práctica.**
