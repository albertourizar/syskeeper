"""Fixtures compartidas por la suite de pruebas."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from syskeeper.config import Config


@pytest.fixture(autouse=True)
def datos_en_temporal(tmp_path: Path, monkeypatch) -> None:
    """Evita escribir registros reales durante las pruebas."""
    monkeypatch.setattr("syskeeper.registro.carpeta_datos_app", lambda: tmp_path / "datos-app")


@pytest.fixture(autouse=True)
def limpiar_logger() -> None:
    """Evita que los manejadores de log se acumulen entre pruebas."""
    logger = logging.getLogger("syskeeper")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(carpeta_informes=str(tmp_path / "informes"))


@pytest.fixture
def crear_archivo() -> Callable[..., Path]:
    """Crea archivos con una antigüedad concreta (48 h por defecto)."""

    def _crear(
        ruta: Path,
        *,
        contenido: bytes = b"0123456789abcdef",
        horas: float = 48.0,
    ) -> Path:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)
        marca = time.time() - horas * 3600
        os.utime(ruta, (marca, marca))
        return ruta

    return _crear
