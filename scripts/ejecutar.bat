@echo off
rem ---------------------------------------------------------------------------
rem  syskeeper - lanzador
rem
rem  Sin argumentos  -> abre el menu interactivo (pensado para doble clic).
rem  Con argumentos  -> ejecuta ese comando:
rem                     scripts\ejecutar.bat limpiar
rem                     scripts\ejecutar.bat smart
rem
rem  Requiere el paquete instalado:  python -m pip install -e .
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

if "%~1"=="" goto :menu

python -m syskeeper %*
set "CODIGO=%ERRORLEVEL%"

if "%CODIGO%"=="0" goto :fin
if "%CODIGO%"=="1" echo [AVISO] La ejecucion termino con avisos. Revisa el informe.
if "%CODIGO%"=="2" echo [ERROR] La ejecucion fallo. Revisa el registro.
goto :fin

:menu
python iniciar.py
set "CODIGO=%ERRORLEVEL%"
if "%CODIGO%"=="0" goto :fin
echo.
echo syskeeper termino con el codigo %CODIGO%.
pause

:fin
exit /b %CODIGO%
