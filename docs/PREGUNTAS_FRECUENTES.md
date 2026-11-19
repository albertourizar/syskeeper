# Preguntas frecuentes

### ¿Borra mis documentos, fotos o partidas guardadas?

No. `syskeeper` solo actúa sobre carpetas temporales, la papelera vaciada por el
sistema y subcarpetas de caché de navegadores. Además mantiene una lista de
rutas protegidas (`Documents`, `Desktop`, `Downloads`, `OneDrive`, etc.) y
rechaza raíces de unidad.

### ¿Necesito ser administrador?

Para la mayor parte de la limpieza, no. Necesitas elevación para:

- Vaciar `C:\Windows\Temp`.
- Limpiar `C:\Windows\Prefetch` (opcional, `--incluir-prefetch`).
- Leer desgaste, temperatura y horas de los discos.
- Ejecutar `smartctl` en algunos dispositivos.

Sin administrador el programa funciona igual y avisa de estas limitaciones.

### ¿Qué pasa si me equivoco y uso `--aplicar`?

El programa pide escribir `SI` antes de borrar. Los archivos temporales y las
cachés se pueden regenerar; la papelera se vacía de forma permanente. Revisa el
informe de simulación (`syskeeper limpiar`) antes de aplicar.

### ¿Puedo recuperar lo que ha borrado?

Lo eliminado con `unlink` no pasa por la papelera. Los navegadores y Windows
volverán a crear sus cachés, pero no se pueden restaurar los archivos
temporales. Mantén copias de seguridad de los datos importantes.

### ¿Por qué no borra todos los archivos temporales?

Porque muchos están en uso o pertenecen a otro usuario. Además se aplica una
antigüedad mínima de 24 horas por defecto para no romper instaladores en curso.
Los fallos se muestran como «errores» en el informe, sin detener el proceso.

### ¿Tengo que cerrar los navegadores?

Sí, para liberar toda la caché. Chrome, Edge, Firefox y Brave mantienen archivos
abiertos; `syskeeper` los omite y te avisa. Cierra también las extensiones y
procesos en segundo plano.

### ¿Borra cookies o contraseñas?

No. Solo se eliminan las carpetas `Cache`, `Code Cache`, `GPUCache`, `Cache2`,
`startupCache` y `CacheStorage`. Cookies, `Login Data`, historial, marcadores y
extensiones quedan intactos.

### ¿Por qué el desgaste del SSD aparece con «—»?

`Get-StorageReliabilityCounter` requiere administrador. Abre PowerShell como
administrador y ejecuta `syskeeper smart`. Si sigue vacío, el disco o su
controladora no exponen ese contador.

### ¿Es fiable el estado "Healthy"?

Es la evaluación que hace Windows con los datos SMART disponibles. No detecta
todos los fallos futuros. Complementa el diagnóstico con copias de seguridad y,
si quieres más detalle, instala `smartmontools` y usa `--smartctl`.

### ¿Puedo usarlo en Linux o macOS?

La versión 1.x es exclusiva de Windows. La gestión de SMART, la papelera y las
rutas de caché son específicas de Windows. La suite de pruebas se puede ejecutar
en otros sistemas, pero el programa no.

### ¿Cómo lo ejecuto cada día sin intervención?

Con el Programador de tareas y `--aplicar --si`. La guía completa está en
[`scripts/tarea_programada.md`](../scripts/tarea_programada.md).

### ¿Dónde están los registros?

En `%LOCALAPPDATA%\syskeeper\logs\syskeeper.log`, con rotación de 1 MB y tres
copias. Los informes se guardan en `informes/` por defecto.

### ¿Por qué hay dos archivos de informe?

El `.md` es legible y se puede adjuntar a una incidencia; el `.json` es estable y
sirve para paneles, alertas o comparaciones entre ejecuciones.

### ¿Puedo añadir mis propias carpetas temporales?

Sí, con `directorios_temporales_extra` en `config.json`. Se expanden variables
de entorno y `~`. Si una carpeta coincide con la lista de protección, se omite.

### ¿Cómo protejo una carpeta que sí quiero conservar?

Añádela a `rutas_protegidas_extra`. Esa lista tiene prioridad absoluta: ningún
módulo ni opción de línea de comandos puede saltársela.

### ¿El programa envía datos a Internet?

No. No hay telemetría, ni comprobación de actualizaciones, ni llamadas de red.
Todo se ejecuta localmente con PowerShell y la biblioteca estándar.

### ¿Puedo contribuir?

Sí. Lee [CONTRIBUTING.md](../CONTRIBUTING.md) y abre un issue antes de cambios
grandes. Las contribuciones deben incluir pruebas y documentación en español.
