"""Salud de los discos mediante SMART y contadores de fiabilidad de Windows."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

from ..modelos import SaludDisco
from ..utilidades import ErrorPowerShell, decodificar, ejecutar_powershell, es_windows

LOGGER = logging.getLogger("syskeeper.smart")

Ejecutor = Callable[[str], str]

SCRIPT_DISCOS = r"""
$ErrorActionPreference = 'SilentlyContinue'
$salida = @()
foreach ($disco in Get-PhysicalDisk) {
    $fiabilidad = $null
    try {
        $fiabilidad = $disco | Get-StorageReliabilityCounter -ErrorAction Stop
    } catch {
        $fiabilidad = $null
    }

    $desgaste = $null
    $temperatura = $null
    $horas = $null
    $erroresLectura = $null
    $erroresEscritura = $null
    if ($null -ne $fiabilidad) {
        if ($null -ne $fiabilidad.Wear) { $desgaste = [int]$fiabilidad.Wear }
        if ($null -ne $fiabilidad.Temperature) { $temperatura = [int]$fiabilidad.Temperature }
        if ($null -ne $fiabilidad.PowerOnHours) { $horas = [int64]$fiabilidad.PowerOnHours }
        if ($null -ne $fiabilidad.ReadErrorsTotal) {
            $erroresLectura = [int64]$fiabilidad.ReadErrorsTotal
        }
        if ($null -ne $fiabilidad.WriteErrorsTotal) {
            $erroresEscritura = [int64]$fiabilidad.WriteErrorsTotal
        }
    }

    $salida += [PSCustomObject]@{
        nombre = [string]$disco.FriendlyName
        tipo = [string]$disco.MediaType
        salud = [string]$disco.HealthStatus
        estado = [string]$disco.OperationalStatus
        tamano = [double]$disco.Size
        desgaste = $desgaste
        temperatura = $temperatura
        horas_encendido = $horas
        errores_lectura = $erroresLectura
        errores_escritura = $erroresEscritura
    }
}
$salida | ConvertTo-Json -Depth 4 -Compress
"""

SCRIPT_ESTADO_CIM = r"""
$ErrorActionPreference = 'SilentlyContinue'
Get-CimInstance -ClassName Win32_DiskDrive |
    Select-Object Model, Status, SerialNumber |
    ConvertTo-Json -Depth 3 -Compress
"""


def _parsear_json(texto: str) -> list[dict[str, Any]]:
    if not texto.strip():
        return []
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        LOGGER.warning("Respuesta JSON no válida de PowerShell: %s", texto[:200])
        return []
    if isinstance(datos, dict):
        return [datos]
    if isinstance(datos, list):
        return [elemento for elemento in datos if isinstance(elemento, dict)]
    return []


def _a_entero(valor: Any) -> int | None:
    if valor is None or isinstance(valor, bool):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _texto(valor: Any, defecto: str) -> str:
    if valor is None:
        return defecto
    texto = str(valor).strip()
    return texto or defecto


def obtener_discos(
    *, usar_smartctl: bool = False, ejecutor: Ejecutor | None = None
) -> list[SaludDisco]:
    """Obtiene la lista de discos con su estado de salud.

    Usa ``Get-PhysicalDisk`` y ``Get-StorageReliabilityCounter`` (equivalentes a
    los datos SMART que expone Windows). Si ``usar_smartctl`` es ``True`` y la
    herramienta está instalada, se añaden sus resultados como notas.
    """
    if not es_windows():
        LOGGER.error("La comprobación SMART solo está disponible en Windows.")
        return []

    ejecutar = ejecutor or ejecutar_powershell
    try:
        salida = ejecutar(SCRIPT_DISCOS)
    except ErrorPowerShell as exc:
        LOGGER.error("No se pudo consultar la salud de los discos: %s", exc)
        return []

    discos: list[SaludDisco] = []
    for elemento in _parsear_json(salida):
        disco = SaludDisco(
            nombre=_texto(elemento.get("nombre"), "Disco desconocido"),
            tipo=_texto(elemento.get("tipo"), "Desconocido"),
            estado=_texto(elemento.get("estado"), "Desconocido"),
            salud=_texto(elemento.get("salud"), "Desconocido"),
            tamano_bytes=_a_entero(elemento.get("tamano")) or 0,
            desgaste=_a_entero(elemento.get("desgaste")),
            temperatura=_a_entero(elemento.get("temperatura")),
            horas_encendido=_a_entero(elemento.get("horas_encendido")),
            errores_lectura=_a_entero(elemento.get("errores_lectura")),
            errores_escritura=_a_entero(elemento.get("errores_escritura")),
        )
        discos.append(disco)

    if discos:
        _aplicar_estado_cim(discos, ejecutar)
        if usar_smartctl:
            _complementar_con_smartctl(discos)
    return discos


def _aplicar_estado_cim(discos: list[SaludDisco], ejecutar: Ejecutor) -> None:
    """Cruza los discos con ``Win32_DiskDrive.Status`` (predicción de fallo)."""
    try:
        filas = _parsear_json(ejecutar(SCRIPT_ESTADO_CIM))
    except ErrorPowerShell as exc:
        LOGGER.debug("Sin datos CIM de discos: %s", exc)
        return

    for fila in filas:
        modelo = _texto(fila.get("Model"), "")
        estado = _texto(fila.get("Status"), "Desconocido")
        if not modelo:
            continue
        for disco in discos:
            if modelo in disco.nombre or disco.nombre in modelo:
                disco.prediccion_fallo = estado
                break


def _complementar_con_smartctl(discos: list[SaludDisco]) -> None:
    """Añade notas con el resultado de ``smartctl -H`` si está instalado."""
    ejecutable = shutil.which("smartctl")
    if not ejecutable:
        for disco in discos:
            disco.notas.append("smartctl no está instalado; se usan los datos de Windows.")
        return

    try:
        escaneo = subprocess.run(
            [ejecutable, "--scan"],
            capture_output=True,
            timeout=30,
            check=False,
        )
        dispositivos = [
            linea.split()[0]
            for linea in decodificar(escaneo.stdout).splitlines()
            if linea.strip() and not linea.startswith("#")
        ]
    except (OSError, subprocess.TimeoutExpired) as exc:
        for disco in discos:
            disco.notas.append(f"No se pudo ejecutar smartctl: {exc}")
        return

    if not dispositivos:
        for disco in discos:
            disco.notas.append("smartctl no ha detectado dispositivos.")
        return

    for indice, dispositivo in enumerate(dispositivos):
        if indice >= len(discos):
            break
        try:
            prueba = subprocess.run(
                [ejecutable, "-H", dispositivo],
                capture_output=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            discos[indice].notas.append(f"smartctl falló en {dispositivo}: {exc}")
            continue
        texto = decodificar(prueba.stdout) + decodificar(prueba.stderr)
        if "PASSED" in texto.upper():
            discos[indice].notas.append(f"smartctl ({dispositivo}): superado.")
        elif "FAILED" in texto.upper():
            discos[indice].notas.append(f"smartctl ({dispositivo}): FALLÓ la autoevaluación SMART.")
            discos[indice].salud = "Unhealthy (smartctl)"
        else:
            discos[indice].notas.append(
                f"smartctl ({dispositivo}): sin veredicto (¿permisos de administrador?)."
            )
