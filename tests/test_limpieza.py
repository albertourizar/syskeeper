"""Pruebas del motor de limpieza."""

from __future__ import annotations

from pathlib import Path

from syskeeper.limpieza import limpiar_directorio, resumir
from syskeeper.utilidades import tamano_legible


def test_simulacion_no_borra_archivos(tmp_path: Path, crear_archivo) -> None:
    archivo = crear_archivo(tmp_path / "a.tmp", contenido=b"x" * 32)
    resultado = limpiar_directorio(tmp_path, etiqueta="Prueba", horas_minimas=24, aplicar=False)
    assert archivo.exists()
    assert resultado.archivos == 1
    assert resultado.bytes_liberados == 32
    assert resultado.aplicado is False
    assert resultado.errores == 0


def test_aplicar_borra_solo_los_antiguos(tmp_path: Path, crear_archivo) -> None:
    viejo = crear_archivo(tmp_path / "viejo.tmp", horas=48)
    nuevo = crear_archivo(tmp_path / "nuevo.tmp", horas=1)

    resultado = limpiar_directorio(tmp_path, etiqueta="Prueba", horas_minimas=24, aplicar=True)

    assert not viejo.exists()
    assert nuevo.exists()
    assert resultado.archivos == 1
    assert resultado.aplicado is True


def test_directorio_protegido_se_omite(tmp_path: Path, crear_archivo) -> None:
    protegida = tmp_path / "Documentos"
    importante = crear_archivo(protegida / "importante.txt")

    resultado = limpiar_directorio(
        protegida,
        etiqueta="Prueba",
        horas_minimas=0,
        aplicar=True,
        protegidas=[protegida],
    )

    assert importante.exists()
    assert resultado.archivos == 0
    assert resultado.omitidos == 1
    assert any("protegida" in nota.lower() for nota in resultado.notas)


def test_directorio_inexistente(tmp_path: Path) -> None:
    resultado = limpiar_directorio(
        tmp_path / "no-existe", etiqueta="Prueba", horas_minimas=0, aplicar=True
    )
    assert resultado.archivos == 0
    assert resultado.errores == 0


def test_resumir_usa_tamano_legible(tmp_path: Path, crear_archivo) -> None:
    crear_archivo(tmp_path / "a.tmp", contenido=b"x" * 2048)
    resultado = limpiar_directorio(tmp_path, etiqueta="Temporales", horas_minimas=0, aplicar=False)
    texto = resumir(resultado)
    assert "Temporales" in texto
    assert tamano_legible(2048) in texto
