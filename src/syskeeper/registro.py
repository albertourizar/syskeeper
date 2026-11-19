"""Configuración del registro de actividad (consola y archivo rotativo)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .utilidades import carpeta_datos_app

NOMBRE_LOGGER = "syskeeper"


def configurar_logger(*, verbose: bool = False, archivo: bool = True) -> logging.Logger:
    """Crea (una sola vez) el logger del programa."""
    logger = logging.getLogger(NOMBRE_LOGGER)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    if logger.handlers:
        for manejador in logger.handlers:
            if isinstance(manejador, logging.StreamHandler) and not isinstance(
                manejador, RotatingFileHandler
            ):
                manejador.setLevel(logging.DEBUG if verbose else logging.INFO)
        return logger

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%d/%m/%Y %H:%M:%S"
    )

    consola = logging.StreamHandler()
    consola.setLevel(logging.DEBUG if verbose else logging.INFO)
    consola.setFormatter(formato)
    logger.addHandler(consola)

    if archivo:
        try:
            carpeta = carpeta_datos_app() / "logs"
            carpeta.mkdir(parents=True, exist_ok=True)
            manejador = RotatingFileHandler(
                Path(carpeta) / "syskeeper.log",
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            manejador.setLevel(logging.DEBUG)
            manejador.setFormatter(formato)
            logger.addHandler(manejador)
        except OSError:
            logger.debug("No se pudo crear el archivo de registro; solo consola.")

    return logger
