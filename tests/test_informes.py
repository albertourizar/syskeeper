"""Pruebas de los informes en Markdown, JSON y consola."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from syskeeper.informes import (
    construir_markdown,
    guardar_informe,
    imprimir_informe,
    purgar_informes,
)
from syskeeper.modelos import Informe, ResultadoLimpieza, SaludDisco


def _informe() -> Informe:
    return Informe(
        version="1.0.0",
        fecha=datetime(2026, 11, 19, 3, 0, 0),
        modo="aplicado",
        limpiezas=[
            ResultadoLimpieza(
                modulo="Archivos temporales",
                aplicado=True,
                archivos=5,
                bytes_liberados=2048,
                notas=["Carpeta revisada."],
            )
        ],
        discos=[
            SaludDisco(
                nombre="SSD de prueba",
                tipo="SSD",
                salud="Healthy",
                estado="OK",
                desgaste=10,
                temperatura=35,
            )
        ],
        espacio=[("C:\\", 500 * 1024**3, 200 * 1024**3)],
    )


def test_markdown_contiene_datos() -> None:
    texto = construir_markdown(_informe())
    assert "# Informe de mantenimiento" in texto
    assert "APLICADO" in texto
    assert "Archivos temporales" in texto
    assert "SSD de prueba" in texto
    assert "Carpeta revisada." in texto
    assert "2,0 KB" in texto


def test_markdown_sin_discos() -> None:
    informe = _informe()
    informe.discos = []
    texto = construir_markdown(informe)
    assert "No se pudieron obtener datos SMART" in texto


def test_guardar_informe_crea_md_y_json(tmp_path: Path) -> None:
    rutas = guardar_informe(_informe(), tmp_path / "informes")

    assert len(rutas) == 2
    assert all(ruta.is_file() for ruta in rutas)
    datos = json.loads(rutas[1].read_text(encoding="utf-8"))
    assert datos["version"] == "1.0.0"
    assert datos["resumen"]["bytes_liberados"] == 2048
    assert datos["discos"][0]["nombre"] == "SSD de prueba"


def test_imprimir_sin_color(tmp_path: Path, capsys) -> None:
    imprimir_informe(_informe(), color=False)
    salida = capsys.readouterr().out

    assert "SSD de prueba" in salida
    assert "Archivos temporales" in salida
    assert "todo correcto" in salida
    assert "\033[" not in salida


def test_purgar_informes_antiguos(tmp_path: Path) -> None:
    carpeta = tmp_path / "informes"
    carpeta.mkdir()
    viejo = carpeta / "informe_20200101_000000.md"
    nuevo = carpeta / "informe_20260101_000000.md"
    viejo.write_text("viejo", encoding="utf-8")
    nuevo.write_text("nuevo", encoding="utf-8")
    antiguo = time.time() - 10 * 86400
    os.utime(viejo, (antiguo, antiguo))

    eliminados = purgar_informes(carpeta, dias=5)

    assert eliminados == 1
    assert not viejo.exists()
    assert nuevo.exists()
