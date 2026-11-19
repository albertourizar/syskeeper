"""Pruebas de las utilidades generales."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from syskeeper.utilidades import (
    es_windows,
    formatear_tabla,
    recorrer_archivos,
    ruta_protegida,
    tamano_legible,
)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (0, "0 B"),
        (512, "512 B"),
        (1024, "1,0 KB"),
        (1536, "1,5 KB"),
        (5 * 1024**3, "5,0 GB"),
        (2 * 1024**4, "2,0 TB"),
    ],
)
def test_tamano_legible(valor: int, esperado: str) -> None:
    assert tamano_legible(valor) == esperado


def test_formatear_tabla_alinea_columnas() -> None:
    tabla = formatear_tabla(["A", "BB"], [["x", 1]], alinear_derecha=(1,))
    assert tabla == "A  BB\n-  --\nx   1\n".rstrip("\n")


def test_formatear_tabla_valida_columnas() -> None:
    with pytest.raises(ValueError):
        formatear_tabla(["A", "B"], [["solo una"]])


def test_ruta_protegida_detecta_raiz_de_unidad() -> None:
    raiz = Path.cwd().anchor
    assert ruta_protegida(raiz) is True


def test_ruta_protegida_bloquea_documentos() -> None:
    perfil = Path(os.environ.get("USERPROFILE") or Path.home())
    documentos = perfil / "Documents"
    assert ruta_protegida(documentos) is True


def test_ruta_protegida_permite_excepcion(tmp_path: Path) -> None:
    documentos = Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents"
    assert ruta_protegida(documentos, permitidas=[documentos]) is False


def test_ruta_protegida_permite_temporal(tmp_path: Path) -> None:
    assert ruta_protegida(tmp_path) is False


def test_ruta_protegida_detecta_papelera(tmp_path: Path) -> None:
    reciclaje = tmp_path / "$Recycle.Bin"
    reciclaje.mkdir()
    assert ruta_protegida(reciclaje) is True


def test_recorrer_archivos_filtra_por_edad(tmp_path: Path, crear_archivo) -> None:
    viejo = crear_archivo(tmp_path / "viejo.tmp", horas=48)
    nuevo = crear_archivo(tmp_path / "nuevo.tmp", horas=1)
    encontrados = set(recorrer_archivos(tmp_path, horas_minimas=24))
    assert viejo in encontrados
    assert nuevo not in encontrados


def test_recorrer_archivos_sin_limite(tmp_path: Path, crear_archivo) -> None:
    nuevo = crear_archivo(tmp_path / "nuevo.tmp", horas=1)
    assert set(recorrer_archivos(tmp_path)) == {nuevo}


def test_recorrer_archivos_entra_en_subcarpetas(tmp_path: Path, crear_archivo) -> None:
    anidado = crear_archivo(tmp_path / "a" / "b" / "c.tmp")
    assert set(recorrer_archivos(tmp_path, horas_minimas=1)) == {anidado}


def test_recorrer_archivos_ignora_directorio_inexistente(tmp_path: Path) -> None:
    assert list(recorrer_archivos(tmp_path / "no-existe")) == []


@pytest.mark.skipif(not es_windows(), reason="Comprobación específica de Windows")
def test_es_windows_en_windows() -> None:
    assert es_windows() is True
