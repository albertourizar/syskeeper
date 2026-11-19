@echo off
rem ---------------------------------------------------------------------------
rem  syskeeper - lanzador para Windows
rem  Requiere haber instalado el paquete:  python -m pip install -e .
rem  Uso:  scripts\ejecutar.bat limpiar --aplicar
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0.."

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se ha encontrado Python en el PATH.
    echo Instala Python 3.10 o superior desde https://www.python.org/downloads/
    exit /b 2
)

python -m syskeeper %*
set CODIGO=%ERRORLEVEL%
if "%CODIGO%"=="0" goto :fin
if "%CODIGO%"=="1" echo [AVISO] La ejecucion termino con avisos. Revisa el informe.
if "%CODIGO%"=="2" echo [ERROR] La ejecucion fallo. Revisa el registro.
:fin
exit /b %CODIGO%
