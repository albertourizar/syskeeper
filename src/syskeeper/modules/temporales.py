"""Limpieza de archivos temporales del usuario y del sistema."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from ..config import Config
from ..limpieza import limpiar_directorio
from ..modelos import ResultadoLimpieza
from ..utilidades import ruta_protegida

LOGGER = logging.getLogger("syskeeper.temporales")


def directorios_temporales(config: Config) -> list[tuple[str, Path]]:
    """Lista las carpetas temporales existentes y aptas para limpiar."""
    candidatos: list[tuple[str, Path]] = [
        ("Temp del usuario (%TEMP%)", Path(tempfile.gettempdir()))
    ]

    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidatos.append(("Temp local del perfil", Path(local) / "Temp"))

    if config.incluir_temporales_sistema:
        windir = os.environ.get("WINDIR")
        if windir:
            candidatos.append(("Temp de Windows", Path(windir) / "Temp"))
            if config.incluir_prefetch:
                candidatos.append(("Prefetch de Windows", Path(windir) / "Prefetch"))

    for extra in config.directorios_temporales_extra:
        ruta = Path(os.path.expandvars(extra)).expanduser()
        candidatos.append(("Carpeta personalizada", ruta))

    vistos: set[str] = set()
    resultado: list[tuple[str, Path]] = []
    for etiqueta, ruta in candidatos:
        try:
            clave = str(ruta.resolve()).lower()
        except OSError:
            clave = str(ruta).lower()
        if clave in vistos:
            continue
        vistos.add(clave)
        if ruta.is_dir():
            resultado.append((etiqueta, ruta))
        else:
            LOGGER.debug("Carpeta temporal inexistente: %s", ruta)
    return resultado


def limpiar_temporales(
    config: Config,
    *,
    aplicar: bool,
    directorios: list[tuple[str, Path]] | None = None,
) -> ResultadoLimpieza:
    """Analiza y, si ``aplicar`` es ``True``, borra los archivos temporales."""
    total = ResultadoLimpieza(modulo="Archivos temporales", aplicado=aplicar)
    protegidas = [Path(ruta) for ruta in config.rutas_protegidas_extra]
    carpetas = directorios if directorios is not None else directorios_temporales(config)

    for etiqueta, ruta in carpetas:
        LOGGER.debug("Revisando temporales en %s (%s)", ruta, etiqueta)
        if ruta_protegida(ruta, protegidas, permitidas=[ruta]):
            total.omitidos += 1
            total.notas.append(f"Ruta protegida, omitida: {ruta}")
            continue
        parcial = limpiar_directorio(
            ruta,
            etiqueta=etiqueta,
            horas_minimas=config.antiguedad_horas,
            aplicar=aplicar,
            protegidas=protegidas,
            permitidas=[ruta],
        )
        total.fusionar(parcial)

    return total
