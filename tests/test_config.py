"""Pruebas de la carga de configuración."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from syskeeper.config import (
    NAVEGADORES_VALIDOS,
    Config,
    ConfigInvalida,
    cargar_config,
    config_por_defecto,
    guardar_config_ejemplo,
)


def test_valores_por_defecto() -> None:
    config = config_por_defecto()
    assert isinstance(config, Config)
    assert config.antiguedad_horas == 24.0
    assert config.antiguedad_cache_horas == 0.0
    assert config.limpiar_papelera is True
    assert set(config.navegadores) == set(NAVEGADORES_VALIDOS)


def test_carga_parcial_y_ignora_desconocidos(tmp_path: Path) -> None:
    archivo = tmp_path / "config.json"
    archivo.write_text(
        json.dumps(
            {
                "antiguedad_horas": 4,
                "navegadores": ["Firefox", "chrome", "chrome"],
                "clave_desconocida": True,
            }
        ),
        encoding="utf-8",
    )

    config = cargar_config(archivo)

    assert config.antiguedad_horas == 4.0
    assert config.navegadores == ["firefox", "chrome"]
    assert config.limpiar_papelera is True


def test_archivo_inexistente(tmp_path: Path) -> None:
    with pytest.raises(ConfigInvalida):
        cargar_config(tmp_path / "no-existe.json")


def test_json_invalido(tmp_path: Path) -> None:
    archivo = tmp_path / "config.json"
    archivo.write_text("{esto no es json", encoding="utf-8")
    with pytest.raises(ConfigInvalida):
        cargar_config(archivo)


def test_raiz_no_es_objeto(tmp_path: Path) -> None:
    archivo = tmp_path / "config.json"
    archivo.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ConfigInvalida):
        cargar_config(archivo)


@pytest.mark.parametrize(
    ("clave", "valor"),
    [
        ("antiguedad_horas", "mucho"),
        ("antiguedad_horas", -1),
        ("limpiar_papelera", "si"),
        ("retencion_informes_dias", 1.5),
        ("carpeta_informes", 42),
        ("navegadores", "chrome"),
        ("navegadores", ["netscape"]),
    ],
)
def test_valores_invalidos(tmp_path: Path, clave: str, valor: object) -> None:
    archivo = tmp_path / "config.json"
    archivo.write_text(json.dumps({clave: valor}), encoding="utf-8")
    with pytest.raises(ConfigInvalida):
        cargar_config(archivo)


def test_auto_carga_config_del_directorio(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"limpiar_papelera": False}), encoding="utf-8")
    assert cargar_config().limpiar_papelera is False


def test_sin_config_usa_valores_por_defecto(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert cargar_config().antiguedad_horas == 24.0


def test_guardar_config_ejemplo(tmp_path: Path) -> None:
    destino = guardar_config_ejemplo(tmp_path / "config.json")
    assert destino.is_file()
    config = cargar_config(destino)
    assert config.a_dict() == config_por_defecto().a_dict()
