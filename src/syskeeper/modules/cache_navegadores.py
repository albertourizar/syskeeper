"""Limpieza de las cachés de los navegadores más habituales.

Solo se eliminan carpetas de caché conocidas. Nunca se tocan cookies,
contraseñas, historial, marcadores ni perfiles completos.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from ..config import Config
from ..limpieza import limpiar_directorio
from ..modelos import ResultadoLimpieza

LOGGER = logging.getLogger("syskeeper.navegadores")

SUBCARPETAS_CACHE = (
    "Cache",
    "Code Cache",
    "GPUCache",
    "Cache2",
    "startupCache",
    Path("Service Worker") / "CacheStorage",
)

SUBCARPETAS_FIREFOX = ("cache2", "startupCache", "thumbnails")

# Carpetas dentro de "User Data" que no son perfiles de usuario.
PERFILES_EXCLUIDOS = {
    "BrowserMetrics",
    "Crashpad",
    "First Run",
    "GraphiteDawnCache",
    "GrShaderCache",
    "Safe Browsing",
    "ShaderCache",
    "Snapshots",
    "SwReporter",
    "System Profile",
    "WidevineCdm",
}


def _variable(nombre: str) -> Path | None:
    valor = os.environ.get(nombre)
    return Path(valor) if valor else None


def _perfiles_cromados(base: Path, nombre: str) -> list[tuple[str, Path]]:
    resultado: list[tuple[str, Path]] = []
    if not base.is_dir():
        return resultado
    try:
        perfiles = sorted(base.iterdir())
    except OSError:
        return resultado
    for perfil in perfiles:
        if not perfil.is_dir() or perfil.name in PERFILES_EXCLUIDOS:
            continue
        for subcarpeta in SUBCARPETAS_CACHE:
            ruta = perfil / subcarpeta
            if ruta.is_dir():
                resultado.append((f"{nombre} ({perfil.name})", ruta))
    return resultado


def carpetas_de_cache(
    navegadores: list[str],
    *,
    raiz_local: Path | None = None,
    raiz_roaming: Path | None = None,
) -> list[tuple[str, Path]]:
    """Devuelve las carpetas de caché existentes de los navegadores pedidos."""
    local = raiz_local if raiz_local is not None else _variable("LOCALAPPDATA")
    roaming = raiz_roaming if raiz_roaming is not None else _variable("APPDATA")
    resultado: list[tuple[str, Path]] = []
    seleccion = {nombre.lower() for nombre in navegadores}

    if local:
        if "chrome" in seleccion:
            resultado += _perfiles_cromados(local / "Google" / "Chrome" / "User Data", "Chrome")
        if "edge" in seleccion:
            resultado += _perfiles_cromados(local / "Microsoft" / "Edge" / "User Data", "Edge")
        if "brave" in seleccion:
            resultado += _perfiles_cromados(
                local / "BraveSoftware" / "Brave-Browser" / "User Data", "Brave"
            )
        if "firefox" in seleccion:
            base = local / "Mozilla" / "Firefox" / "Profiles"
            if base.is_dir():
                try:
                    perfiles = sorted(ruta for ruta in base.iterdir() if ruta.is_dir())
                except OSError:
                    perfiles = []
                for perfil in perfiles:
                    for nombre_cache in SUBCARPETAS_FIREFOX:
                        ruta = perfil / nombre_cache
                        if ruta.is_dir():
                            resultado.append((f"Firefox ({perfil.name})", ruta))

    if roaming and "opera" in seleccion:
        for carpeta in ("Opera Stable", "Opera GX Stable"):
            base = roaming / "Opera Software" / carpeta
            if not base.is_dir():
                continue
            for subcarpeta in SUBCARPETAS_CACHE:
                ruta = base / subcarpeta
                if ruta.is_dir():
                    resultado.append((f"Opera ({carpeta})", ruta))

    return resultado


def limpiar_cache_navegadores(
    config: Config,
    *,
    aplicar: bool,
    raiz_local: Path | None = None,
    raiz_roaming: Path | None = None,
) -> ResultadoLimpieza:
    """Limpia las cachés de los navegadores configurados."""
    total = ResultadoLimpieza(modulo="Caché de navegadores", aplicado=aplicar)
    protegidas = [Path(ruta) for ruta in config.rutas_protegidas_extra]
    carpetas = carpetas_de_cache(
        config.navegadores, raiz_local=raiz_local, raiz_roaming=raiz_roaming
    )

    if not carpetas:
        total.notas.append(
            "No se han encontrado cachés de navegadores para los navegadores configurados."
        )
        return total

    for etiqueta, ruta in carpetas:
        LOGGER.debug("Limpiando caché %s en %s", etiqueta, ruta)
        parcial = limpiar_directorio(
            ruta,
            etiqueta=etiqueta,
            horas_minimas=config.antiguedad_cache_horas,
            aplicar=aplicar,
            protegidas=protegidas,
            permitidas=[ruta],
        )
        total.fusionar(parcial)

    if total.errores:
        total.notas.append(
            "Algunos archivos estaban en uso. Cierra los navegadores y vuelve a intentarlo."
        )
    return total
