"""Motor común de limpieza usado por los módulos de temporales y cachés."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from .modelos import ResultadoLimpieza
from .utilidades import borrar_archivo, recorrer_archivos, ruta_protegida, tamano_legible

LOGGER = logging.getLogger("syskeeper.limpieza")

MAX_NOTAS_ERROR = 12


def limpiar_directorio(
    directorio: Path,
    *,
    etiqueta: str,
    horas_minimas: float,
    aplicar: bool,
    protegidas: Sequence[Path] = (),
    permitidas: Sequence[Path] = (),
) -> ResultadoLimpieza:
    """Borra (o simula borrar) los archivos antiguos de ``directorio``.

    En modo simulación se contabiliza el espacio que se liberaría. En modo
    aplicación se eliminan los archivos uno a uno y se registran los fallos sin
    interrumpir el resto de la limpieza.
    """
    resultado = ResultadoLimpieza(modulo=etiqueta, aplicado=aplicar)

    if not directorio.is_dir():
        return resultado

    if ruta_protegida(directorio, protegidas, permitidas=permitidas):
        resultado.omitidos += 1
        resultado.notas.append(f"Ruta protegida, omitida: {directorio}")
        LOGGER.warning("Ruta protegida, se omite: %s", directorio)
        return resultado

    for archivo in recorrer_archivos(directorio, horas_minimas=horas_minimas):
        try:
            tamano = archivo.stat().st_size
        except OSError as exc:
            resultado.errores += 1
            if len(resultado.notas) < MAX_NOTAS_ERROR:
                resultado.notas.append(f"No se pudo leer {archivo.name}: {exc}")
            continue

        if aplicar:
            try:
                borrar_archivo(archivo)
            except OSError as exc:
                resultado.errores += 1
                if len(resultado.notas) < MAX_NOTAS_ERROR:
                    resultado.notas.append(f"No se pudo borrar {archivo.name}: {exc}")
                continue
            resultado.archivos += 1
            resultado.bytes_liberados += tamano
        else:
            resultado.archivos += 1
            resultado.bytes_liberados += tamano

    if not resultado.notas and resultado.archivos == 0:
        LOGGER.debug("Sin archivos que limpiar en %s", directorio)
    return resultado


def resumir(resultado: ResultadoLimpieza) -> str:
    """Devuelve una línea legible con el resultado de un módulo."""
    accion = "liberados" if resultado.aplicado else "liberables"
    return (
        f"{resultado.modulo}: {resultado.archivos} archivos, "
        f"{tamano_legible(resultado.bytes_liberados)} {accion}"
    )
