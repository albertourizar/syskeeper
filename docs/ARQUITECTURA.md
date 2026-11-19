# Arquitectura

## Objetivo

`syskeeper` automatiza tres tareas de mantenimiento en Windows —limpiar
temporales, vaciar la papelera y borrar cachés de navegadores— y una tarea de
diagnóstico —leer la salud SMART de los discos— presentando el resultado en
consola y en informes reproducibles.

### No objetivos

- No sustituye a una herramienta de recuperación de datos.
- No desinstala programas ni modifica el registro.
- No eleva privilegios por sí mismo.
- No funciona en Linux ni macOS en la versión 1.x.

## Flujo de ejecución

```
argparse
   │
   ▼
config.cargar_config()  ──►  validación de tipos y navegadores
   │
   ▼
cli._seleccionar_modulos()
   │
   ├── temporales.limpiar_temporales() ──┐
   ├── papelera.vaciar_papelera()       ├──► modelos.ResultadoLimpieza
   ├── cache_navegadores.limpiar...()   ─┘
   └── smart.obtener_discos()  ───────────► modelos.SaludDisco
   │
   ▼
modelos.Informe  ──►  informes.imprimir_informe()
   │                  informes.guardar_informe()  (.md + .json)
   ▼
cli._codigo_salida()  ──►  0 / 1 / 2
```

## Capas

| Capa | Módulos | Responsabilidad |
|---|---|---|
| Presentación | `cli.py` | Parseo de argumentos, confirmación, salida y códigos. |
| Dominio | `modelos.py`, `limpieza.py` | Estructuras de resultado y borrado seguro. |
| Servicios | `modules/*` | Cada fuente de limpieza o diagnóstico. |
| Infraestructura | `utilidades.py`, `registro.py`, `config.py` | PowerShell, rutas protegidas, logs y configuración. |
| Informes | `informes.py` | Renderizado en consola, Markdown y JSON. |

Las dependencias apuntan siempre hacia el dominio: los módulos no importan
`cli.py` ni escriben informes.

## Modelo de datos

- `ResultadoLimpieza`: contadores (`archivos`, `bytes_liberados`, `errores`,
  `omitidos`), modo (`aplicado`) y notas legibles.
- `SaludDisco`: identidad, estado, salud, desgaste, temperatura, horas, errores
  y predicción de fallo. `nivel_alerta()` centraliza los umbrales.
- `Informe`: agrega limpiezas, discos, advertencias y espacio libre. Expone
  totales y `hay_problemas`, que decide el código de salida.

Todas las estructuras implementan `a_dict()` para que el JSON sea estable y
consumible por otras herramientas.

## Invariantes de seguridad

1. **Simulación por defecto.** `aplicar` es `False` salvo que el usuario pase
   `--aplicar`; el comando `informe` lo fuerza a `False` siempre.
2. **Confirmación explícita.** En modo real se exige escribir `SI`, excepto con
   `--si` (pensado para tareas programadas).
3. **Lista negra primero.** `ruta_protegida()` comprueba `rutas_protegidas_extra`
   antes que cualquier permiso puntual. Ningún módulo puede saltarse una ruta
   protegida por el usuario.
4. **Raíces de unidad prohibidas.** `objetivo.parent == objetivo` se rechaza.
5. **Sin enlaces.** `recorrer_archivos()` ignora enlaces simbólicos y puntos de
   unión mediante `follow_symlinks=False` y el atributo de reparse point.
6. **Borrado archivo a archivo.** Nunca se elimina un árbol completo: se borran
   archivos y los directorios de caché se conservan vacíos.
7. **Errores aislados.** Un archivo bloqueado incrementa `errores` y añade una
   nota; el resto de la limpieza continúa.
8. **Solo rutas conocidas.** Las cachés se localizan por rutas y nombres
   explícitos; no se buscan patrones amplios en el perfil del usuario.

Las excepciones (`permitidas`) existen únicamente para que `C:\Windows\Temp` y
`Prefetch` puedan limpiarse pese a estar dentro de `C:\Windows`; no anulan las
rutas protegidas por el usuario.

## Integración con PowerShell

`ejecutar_powershell()` centraliza la llamada:

```
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ...
```

- Fuerza `[Console]::OutputEncoding` a UTF-8 para que los acentos de los
  nombres de disco no rompan el JSON.
- Captura bytes y los decodifica probando UTF-8, CP850 y CP1252.
- Impone tiempos de espera (90–180 s según la operación) y convierte los fallos
  en `ErrorPowerShell`.

### SMART

`modules/smart.py` ejecuta dos consultas:

1. `Get-PhysicalDisk` + `Get-StorageReliabilityCounter`: salud, estado, tamaño,
   desgaste, temperatura, horas y errores.
2. `Win32_DiskDrive`: estado predictivo (`OK`, `Pred Fail`). Se cruza por nombre
   de modelo con la lista anterior.

No se usa `wmic`: está obsoleto y desaparece en instalaciones recientes de
Windows 11. Si el usuario pasa `--smartctl`, se ejecuta `smartctl --scan` y
`smartctl -H` sobre cada dispositivo detectado, añadiendo notas sin alterar el
resto del informe salvo un `FAILED` explícito.

## Informes

`informes.construir_markdown()` y `Informe.a_dict()` son funciones puras: no
escriben ni leen del sistema. `guardar_informe()` se limita a crear el
directorio y volcar ambos formatos con UTF-8. Esto permite probar el contenido
sin tocar disco y reutilizar el JSON en un panel externo.

## Pruebas

- `pytest` con `tmp_path` para no tocar datos reales.
- PowerShell simulado mediante funciones inyectadas (`ejecutor`) o
  `monkeypatch` de `ejecutar_powershell`.
- Estructura de perfiles de navegador falsa para comprobar que solo se borran
  las carpetas de caché y que cookies/historial sobreviven.
- Pruebas específicas de Windows marcadas con `skipif` para que la suite siga
  siendo ejecutable en otros sistemas.
- Cobertura mínima objetivo: 80 %. La CI ejecuta además `ruff` y `mypy`.

## Extender el programa

Para añadir un módulo (por ejemplo, «archivos grandes»):

1. Crear `src/syskeeper/modules/archivos_grandes.py`.
2. Devolver un `ResultadoLimpieza` y recibir `Config` + `aplicar`.
3. Reutilizar `limpieza.limpiar_directorio()` si el borrado es por archivos.
4. Registrarlo en `cli.MODULOS`, `NOMBRES_MODULOS` y `_seleccionar_modulos()`.
5. Añadir pruebas con una carpeta temporal y un caso de simulación.
6. Documentarlo en `docs/USO.md` y `CHANGELOG.md`.

## Decisiones y alternativas descartadas

| Decisión | Motivo |
|---|---|
| Solo biblioteca estándar | Instalación trivial, auditoría sencilla y menos cadena de suministro. |
| PowerShell CIM en vez de `wmic` | `wmic` está obsoleto; CIM es el mecanismo soportado. |
| Simulación por defecto | El fallo más caro es borrar datos personales. |
| CLI en vez de GUI | Encaja con tareas programadas y CI; menos superficie de fallo. |
| Windows únicamente | SMART, papelera y rutas de caché tienen APIs distintas en cada sistema. |
| `send2trash` descartado | Para vaciar la papelera no aporta valor frente a `Clear-RecycleBin`. |
