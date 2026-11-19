# Registro de cambios

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
el proyecto usa [Versionado semántico](https://semver.org/lang/es/).

## [1.0.0] — 2026-11-19

### Añadido

- Limpieza de archivos temporales del usuario, del perfil y de Windows, con
  antigüedad mínima configurable y omisión de archivos bloqueados.
- Vaciado de la papelera de reciclaje mediante `Clear-RecycleBin`, con
  alternativa COM y medición del espacio recuperado.
- Limpieza de cachés de Chrome, Edge, Firefox, Brave y Opera sin tocar cookies,
  historial ni perfiles.
- Diagnóstico SMART con `Get-PhysicalDisk`, `Get-StorageReliabilityCounter` y
  `Win32_DiskDrive`, más integración opcional con `smartctl`.
- Informes en consola, Markdown y JSON con resumen, notas y espacio libre.
- Modo simulación por defecto, confirmación escrita y modo desatendido `--si`.
- Lista de rutas protegidas, protección frente a enlaces simbólicos y raíces de
  unidad.
- Subcomandos `limpiar`, `smart`, `informe`, `todo` y `config`.
- Códigos de salida 0/1/2/130 para automatización y CI.
- Menú interactivo `iniciar.py` y lanzador `Iniciar syskeeper.bat` para usar
  con doble clic, además del lanzador de línea de comandos.
- Suite de 92 pruebas con pytest, cobertura superior al 80 %, ruff y mypy.
- CI en GitHub Actions para Windows (Python 3.10, 3.12 y 3.13) y flujo de
  publicación de releases.
- Documentación completa en español, plantillas de issue/PR y guías de
  instalación, uso, arquitectura y tareas programadas.

### Notas

- Requiere Windows 10 u 11 y Python 3.10 o superior.
- Los contadores de desgaste y temperatura requieren ejecutar como
  administrador; el estado general se obtiene sin elevación.
- No se admiten sistemas distintos de Windows en esta versión.

[1.0.0]: https://github.com/albertourizar/syskeeper/releases/tag/v1.0.0
