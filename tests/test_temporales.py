"""Pruebas del módulo de archivos temporales."""

from __future__ import annotations

from pathlib import Path

from syskeeper.config import Config
from syskeeper.modules.temporales import (
    directorios_temporales,
    limpiar_temporales,
)


def test_limpiar_temporales_simula(tmp_path: Path, crear_archivo, config: Config) -> None:
    crear_archivo(tmp_path / "a.tmp", contenido=b"x" * 10)
    resultado = limpiar_temporales(config, aplicar=False, directorios=[("Prueba", tmp_path)])
    assert resultado.modulo == "Archivos temporales"
    assert resultado.archivos == 1
    assert resultado.bytes_liberados == 10
    assert (tmp_path / "a.tmp").exists()


def test_limpiar_temporales_aplica(tmp_path: Path, crear_archivo, config: Config) -> None:
    archivo = crear_archivo(tmp_path / "a.tmp")
    resultado = limpiar_temporales(config, aplicar=True, directorios=[("Prueba", tmp_path)])
    assert not archivo.exists()
    assert resultado.archivos == 1
    assert resultado.aplicado is True


def test_carpeta_protegida_no_se_limpia(tmp_path: Path, crear_archivo, config: Config) -> None:
    protegida = tmp_path / "Documentos"
    archivo = crear_archivo(protegida / "importante.txt")
    config.rutas_protegidas_extra = [str(protegida)]

    resultado = limpiar_temporales(config, aplicar=True, directorios=[("Documentos", protegida)])

    assert archivo.exists()
    assert resultado.archivos == 0
    assert resultado.omitidos == 1


def test_directorios_temporales_incluye_carpeta_extra(tmp_path: Path, config: Config) -> None:
    extra = tmp_path / "mi-temp"
    extra.mkdir()
    config.directorios_temporales_extra = [str(extra)]

    etiquetas = [etiqueta for etiqueta, _ in directorios_temporales(config)]

    assert "Carpeta personalizada" in etiquetas


def test_directorios_temporales_ignora_inexistentes(config: Config) -> None:
    config.directorios_temporales_extra = [r"C:\ruta\que\no\existe\jamas"]
    rutas = [ruta for _, ruta in directorios_temporales(config)]
    assert all(ruta.is_dir() for ruta in rutas)
