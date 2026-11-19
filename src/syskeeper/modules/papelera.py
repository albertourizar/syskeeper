"""Vaciado de la papelera de reciclaje mediante PowerShell."""

from __future__ import annotations

import logging

from ..config import Config
from ..modelos import ResultadoLimpieza
from ..utilidades import ErrorPowerShell, ejecutar_powershell, es_windows

LOGGER = logging.getLogger("syskeeper.papelera")

SCRIPT_MEDIR = r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$items = @($shell.Namespace(10).Items())
$total = [int64]0
foreach ($item in $items) { $total += [int64]$item.Size }
Write-Output ("{0}|{1}" -f $items.Count, $total)
"""

SCRIPT_VACIAR = r"""
$ErrorActionPreference = 'Stop'
Clear-RecycleBin -Force
"""

SCRIPT_VACIAR_ALTERNATIVA = r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$items = @($shell.Namespace(10).Items())
foreach ($item in $items) { $item.InvokeVerb('delete') }
"""


def medir_papelera() -> tuple[int, int]:
    """Devuelve ``(elementos, bytes)`` que hay actualmente en la papelera."""
    salida = ejecutar_powershell(SCRIPT_MEDIR, timeout=90)
    if "|" not in salida:
        raise ErrorPowerShell(f"Respuesta inesperada al medir la papelera: {salida[:80]!r}")
    elementos, tamano = salida.split("|", 1)
    try:
        return int(elementos.strip()), int(tamano.strip())
    except ValueError as exc:
        raise ErrorPowerShell("No se pudo interpretar el tamaño de la papelera.") from exc


def vaciar_papelera(config: Config, *, aplicar: bool) -> ResultadoLimpieza:
    """Mide y, si ``aplicar`` es ``True``, vacía la papelera de reciclaje."""
    resultado = ResultadoLimpieza(modulo="Papelera de reciclaje", aplicado=aplicar)

    if not config.limpiar_papelera:
        resultado.notas.append("El vaciado de la papelera está desactivado en la configuración.")
        return resultado
    if not es_windows():
        resultado.errores += 1
        resultado.notas.append("La papelera solo se puede vaciar en Windows.")
        return resultado

    try:
        elementos_antes, bytes_antes = medir_papelera()
    except ErrorPowerShell as exc:
        resultado.errores += 1
        resultado.notas.append(f"No se pudo medir la papelera: {exc}")
        return resultado

    if elementos_antes == 0:
        resultado.notas.append("La papelera ya estaba vacía.")
        return resultado

    if not aplicar:
        resultado.archivos = elementos_antes
        resultado.bytes_liberados = bytes_antes
        resultado.notas.append("Simulación: no se ha vaciado la papelera.")
        return resultado

    try:
        ejecutar_powershell(SCRIPT_VACIAR, timeout=180)
    except ErrorPowerShell as exc:
        LOGGER.warning("Clear-RecycleBin falló, se prueba el método COM: %s", exc)
        try:
            ejecutar_powershell(SCRIPT_VACIAR_ALTERNATIVA, timeout=180)
        except ErrorPowerShell as exc2:
            resultado.errores += 1
            resultado.notas.append(f"No se pudo vaciar la papelera: {exc2}")
            return resultado

    try:
        elementos_despues, bytes_despues = medir_papelera()
    except ErrorPowerShell:
        elementos_despues, bytes_despues = 0, 0

    resultado.archivos = max(0, elementos_antes - elementos_despues)
    resultado.bytes_liberados = max(0, bytes_antes - bytes_despues)
    if elementos_despues > 0:
        resultado.notas.append(
            f"Quedan {elementos_despues} elementos en la papelera "
            "(puede que estén en uso o pertenezcan a otro usuario)."
        )
    return resultado
