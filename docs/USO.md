# Guía de uso

Esta guía amplía el README con recetas, opciones y solución de problemas.

## Comandos y opciones

```
syskeeper {limpiar,smart,informe,todo,config} [opciones]
```

| Opción | Comando | Descripción |
|---|---|---|
| `--aplicar` | limpiar, todo | Borra de verdad. Sin esta opción solo se simula. |
| `--si` | limpiar, todo | No pedir confirmación (modo desatendido). |
| `--solo LISTA` | todos | Módulos separados por comas: `temporales,papelera,navegadores,smart`. |
| `--min-horas N` | limpiar, informe, todo | Antigüedad mínima de los temporales. |
| `--incluir-prefetch` | limpiar, todo | Añade `C:\Windows\Prefetch` (requiere admin). |
| `--smartctl` | smart, todo, informe | Añade el veredicto de `smartctl` si está instalado. |
| `--sin-informe` | todos | No escribir los archivos `.md`/`.json`. |
| `--sin-espacio` | todos | Omitir el espacio libre de las unidades. |
| `--sin-color` | todos | Desactivar colores (recomendado en tareas). |
| `--config ARCHIVO` | todos | Usar otro `config.json`. |
| `-v`, `--verbose` | todos | Registro detallado en consola. |

## Recetas

### Limpieza diaria desatendida

```powershell
syskeeper limpiar --aplicar --si --sin-color --solo temporales,papelera,navegadores
```

Pensada para el Programador de tareas. No pregunta nada y escribe el informe en
`informes/`.

### Solo temporales, sin papelera

```powershell
syskeeper limpiar --aplicar --solo temporales --min-horas 48
```

Útil en equipos compartidos donde la papelera pertenece a otra persona.

### Revisar sin tocar cachés

```powershell
syskeeper informe --solo temporales,smart --sin-espacio
```

### Añadir una carpeta propia

```json
{
  "directorios_temporales_extra": ["D:\\temp-render", "%USERPROFILE%\\tmp"]
}
```

Las variables de entorno y `~` se expanden automáticamente.

### Proteger una carpeta concreta

```json
{
  "rutas_protegidas_extra": ["D:\\proyectos", "C:\\Users\\Alberto\\Escritorio"]
}
```

La lista de protección tiene prioridad sobre cualquier módulo, incluso si la
carpeta aparece como temporal.

### Cambiar el umbral de antigüedad una sola vez

```powershell
syskeeper limpiar --aplicar --min-horas 72
```

El valor de la línea de comandos no modifica `config.json`.

## Interpretar el informe SMART

| Campo | Origen | Lectura |
|---|---|---|
| Salud | `Get-PhysicalDisk.HealthStatus` | `Healthy` es lo esperado. |
| Estado | `OperationalStatus` | `OK` es lo esperado; `Warning`/`Degraded` requiere atención. |
| Desgaste | `Wear` | Porcentaje de vida consumida en SSD. ≥ 80 % aviso, ≥ 95 % crítico. |
| Temperatura | `Temperature` | ≥ 60 °C aviso, ≥ 70 °C crítico. |
| Horas | `PowerOnHours` | Referencia de antigüedad, no un fallo por sí mismo. |
| Errores | `ReadErrorsTotal`, `WriteErrorsTotal` | Cualquier valor > 0 genera aviso. |
| Predicción | `Win32_DiskDrive.Status` | `Pred Fail` se marca como crítico. |

### Por qué aparecen guiones

`Get-StorageReliabilityCounter` necesita privilegios de administrador. Si ves
`—` en desgaste, temperatura u horas, abre PowerShell como administrador y
repite:

```powershell
syskeeper smart
```

También puedes usar `smartctl` (paquete [smartmontools](https://www.smartmontools.org/))
junto a `--smartctl`. El programa no lo instala ni lo ejecuta con elevación
automática.

## Registros y salida

- Registro rotativo: `%LOCALAPPDATA%\syskeeper\logs\syskeeper.log`
  (1 MB × 3 archivos).
- Informes: `informes\informe_AAAAMMDD_HHMMSS.md` y `.json` en el directorio de
  ejecución, salvo que configures otra carpeta.
- Retención: los informes de más de `retencion_informes_dias` se eliminan al
  finalizar.

## Programador de tareas

Consulta [`scripts/tarea_programada.md`](../scripts/tarea_programada.md).

Resumen:

```powershell
schtasks /Create /TN "syskeeper - limpieza diaria" ^
  /TR "\"C:\Ruta\python.exe\" -m syskeeper limpiar --aplicar --si --sin-color" ^
  /SC DAILY /ST 03:00 /RL HIGHEST /F
```

## Solución de problemas

### «No se ha encontrado PowerShell»

Comprueba que `powershell.exe` está en el `PATH`:

```powershell
Get-Command powershell
```

Si usas una instalación portable, abre una consola nueva o repara las variables
de entorno.

### «No se pudo medir la papelera»

Otra cuenta puede tener elementos en la papelera. Ejecuta como administrador o
vacía la papelera manualmente una vez. El programa no fuerza el borrado de
elementos ajenos.

### «Algunos archivos estaban en uso»

Cierra los navegadores (y sus procesos en segundo plano) y repite. También
puede ocurrir con archivos temporales de instaladores o antivirus.

### SMART sin datos

- Comprueba que la unidad expone SMART (algunos USB/NVMe en cajas externas no
  lo hacen).
- Ejecuta como administrador.
- Prueba `smartctl --scan` para ver si el dispositivo es visible.

### El informe no se crea

Verifica permisos de escritura en el directorio actual o define una ruta
absoluta en `carpeta_informes`. Con `--sin-informe` se omite a propósito.

### Código de salida 1 en una tarea programada

Es un aviso, no un fallo fatal: revisa el informe para ver si hay un disco
degradado o archivos bloqueados. El código 2 sí indica un error de
configuración o un fallo inesperado.

## Variables de entorno útiles

| Variable | Uso |
|---|---|
| `LOCALAPPDATA` | Cachés de navegadores y registro. |
| `APPDATA` | Perfiles de Opera. |
| `TEMP` / `TMP` | Carpeta temporal del usuario. |
| `WINDIR` | Ruta de Windows (`C:\Windows`). |
| `USERPROFILE` | Perfil del usuario. |

`syskeeper` no modifica estas variables; solo las lee.
