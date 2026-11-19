@echo off
rem ---------------------------------------------------------------------------
rem  syskeeper - inicio con doble clic
rem  Requiere el paquete instalado:  python -m pip install -e .
rem ---------------------------------------------------------------------------
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
title syskeeper 1.0.0

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] No se ha encontrado Python en el PATH.
    echo Instala Python 3.10 o superior desde https://www.python.org/downloads/
    echo.
    pause
    exit /b 2
)

python iniciar.py
set "CODIGO=%ERRORLEVEL%"
if not "%CODIGO%"=="0" (
    echo.
    echo syskeeper termino con el codigo %CODIGO%.
    pause
)
exit /b %CODIGO%
