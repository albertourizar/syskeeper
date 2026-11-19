# Programar syskeeper en Windows

Guía para ejecutar la limpieza de forma desatendida con el Programador de
tareas. Se recomienda una ventana de mantenimiento (por ejemplo, a las 03:00) y
ejecutar con privilegios elevados para incluir `C:\Windows\Temp`.

## 1. Localiza el ejecutable de Python

```powershell
where.exe python
```

Ejemplo de resultado:

```
C:\Users\Alberto\AppData\Local\Programs\Python\Python314\python.exe
```

Si usas un entorno virtual, apunta al `python.exe` de `.venv\Scripts`. Instala
el paquete en ese mismo entorno antes de programar la tarea.

## 2. Prueba el comando manualmente

```powershell
& "C:\Users\Alberto\AppData\Local\Programs\Python\Python314\python.exe" `
  -m syskeeper todo --aplicar --si --sin-color
```

Comprueba que aparecen los informes en `informes\` y que el código de salida es
0 (todo correcto) o 1 (avisos). Nunca uses `--si` sin haber probado antes el
modo simulación.

## 3. Crea la tarea con `schtasks`

```powershell
schtasks /Create /TN "syskeeper - limpieza diaria" ^
  /TR "\"C:\Users\Alberto\AppData\Local\Programs\Python\Python314\python.exe\" -m syskeeper todo --aplicar --si --sin-color" ^
  /SC DAILY /ST 03:00 /RL HIGHEST /F
```

- `/SC DAILY /ST 03:00`: todos los días a las 03:00.
- `/RL HIGHEST`: ejecuta con privilegios elevados (necesario para el Temp de
  Windows y los contadores SMART).
- `/F`: sobrescribe la tarea si ya existe.

`todo` ejecuta la limpieza y el análisis SMART. Si solo quieres limpiar:

```
... -m syskeeper limpiar --aplicar --si --sin-color --solo temporales,papelera,navegadores
```

## 4. Alternativa con PowerShell

```powershell
$accion = New-ScheduledTaskAction -Execute "C:\Users\Alberto\AppData\Local\Programs\Python\Python314\python.exe" `
  -Argument "-m syskeeper todo --aplicar --si --sin-color" `
  -WorkingDirectory "C:\Users\Alberto\syskeeper"
$disparador = New-ScheduledTaskTrigger -Daily -At 03:00
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
  -LogonType S4U -RunLevel Highest
Register-ScheduledTask -TaskName "syskeeper - limpieza diaria" `
  -Action $accion -Trigger $disparador -Principal $principal -Force
```

`-WorkingDirectory` determina dónde se guardan `informes\`. Usa una ruta con
permisos de escritura para el usuario de la tarea.

## 5. Verificar y ejecutar ahora

```powershell
schtasks /Query /TN "syskeeper - limpieza diaria" /V /FO LIST
schtasks /Run   /TN "syskeeper - limpieza diaria"
```

Revisa:

- `%LOCALAPPDATA%\syskeeper\logs\syskeeper.log`
- La carpeta `informes\` del directorio de trabajo.
- El historial del Programador de tareas.

## 6. Eliminar la tarea

```powershell
schtasks /Delete /TN "syskeeper - limpieza diaria" /F
```

## Recomendaciones

- Prueba primero `syskeeper limpiar` sin `--aplicar` y revisa el informe.
- No programes la limpieza mientras se ejecutan copias de seguridad.
- Si el equipo se apaga a esa hora, activa «Ejecutar la tarea si se omitió el
  inicio programado» en las propiedades de la tarea.
- El código de salida 1 indica avisos; no siempre requiere intervención, pero
  conviene revisar el informe.
- La tarea no abre ventanas ni pide confirmación porque usa `--si`.
