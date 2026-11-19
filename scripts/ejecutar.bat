@echo off
rem ---------------------------------------------------------------------------
rem  syskeeper - lanzador para linea de comandos
rem  Requiere haber instalado el paquete:  python -m pip install -e .
rem  Uso:  scripts\ejecutar.bat limpiar --aplicar
rem ---------------------------------------------------------------------------
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0.."
set "PYTHONIOENCODING=utf-8"

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] No se ha encontrado Python en el PATH.
    echo Instala Python 3.10 o superior desde https://www.python.org/downloads/
    echo.
    pause
    exit /b 2
)

python -m syskeeper %*
set "CODIGO=%ERRORLEVEL%"

if "%~1"=="" (
    echo.
    echo Este lanzador necesita argumentos. Ejemplo:
    echo     scripts\ejecutar.bat limpiar
    echo     scripts\ejecutar.bat smart
    echo.
    echo Para un menu interactivo usa "Iniciar syskeeper.bat" en la raiz.
    echo.
    pause
)

if "%CODIGO%"=="0" goto :fin
if "%CODIGO%"=="1" echo [AVISO] La ejecucion termino con avisos. Revisa el informe.
if "%CODIGO%"=="2" echo [ERROR] La ejecucion fallo. Revisa el registro.
:fin
exit /b %CODIGO%
