# Política de seguridad

## Versiones soportadas

| Versión | Soporte |
|---|---|
| 1.0.x | Sí |
| < 1.0 | No |

## Cómo reportar una vulnerabilidad

No abras un issue público para problemas de seguridad. Usa
[GitHub Security Advisories](https://github.com/albertourizar/syskeeper/security/advisories/new)
o escribe al mantenedor a través de su perfil de GitHub.

Incluye, si es posible:

- Versión de syskeeper, Windows y Python.
- Descripción del impacto y pasos para reproducirlo.
- Comando ejecutado y configuración (sin datos personales).
- Fragmento del informe JSON o del registro.

Recibirás acuse de recibo en un plazo orientativo de 72 horas. Si el problema se
confirma, se preparará un parche y se coordinará la divulgación.

## Alcance

Se consideran vulnerabilidades:

- Borrado de archivos fuera de las rutas permitidas.
- Evasión de la lista de rutas protegidas.
- Inyección de comandos a través de la configuración o de nombres de archivo.
- Elevación de privilegios no solicitada.
- Exposición de datos en informes o registros.

No se consideran vulnerabilidades:

- El borrado intencionado con `--aplicar` de archivos temporales o cacheados.
- La ausencia de datos SMART cuando faltan permisos.
- El comportamiento de herramientas externas como `smartctl`.
- Windows modificados o con PowerShell sustituido.

## Diseño defensivo

- La configuración se valida con tipos estrictos antes de ejecutar nada.
- Los scripts de PowerShell son constantes del código; no se interpolan rutas
  del usuario. Las rutas se pasan a `Path` y se validan en Python.
- Las rutas protegidas se comprueban antes de cada limpieza.
- Los enlaces simbólicos y puntos de unión se ignoran.
- No se ejecuta nada como SYSTEM ni se solicita elevación automática.
- No hay telemetría ni conexiones de red.

## Buenas prácticas para usuarios

- Ejecuta primero en modo simulación y revisa el informe.
- Mantén copias de seguridad de los datos importantes.
- No uses `--si` en scripts que no controlas.
- Descarga el proyecto solo desde este repositorio y verifica la etiqueta de
  versión.
