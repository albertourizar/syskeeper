"""Pruebas de la limpieza de cachés de navegadores."""

from __future__ import annotations

from pathlib import Path

from syskeeper.config import Config
from syskeeper.modules.cache_navegadores import (
    carpetas_de_cache,
    limpiar_cache_navegadores,
)


def _crear_perfil_chrome(local: Path) -> tuple[Path, Path, Path]:
    perfil = local / "Google" / "Chrome" / "User Data" / "Default"
    cache = perfil / "Cache"
    cache.mkdir(parents=True)
    (cache / "datos.bin").write_bytes(b"x" * 100)
    gpu = perfil / "GPUCache"
    gpu.mkdir()
    (gpu / "gpu.bin").write_bytes(b"y" * 50)
    cookies = perfil / "Cookies"
    cookies.write_text("no tocar", encoding="utf-8")
    historial = perfil / "History"
    historial.write_text("no tocar", encoding="utf-8")
    return cache, cookies, historial


def test_detecta_carpetas_de_cache(tmp_path: Path) -> None:
    local = tmp_path / "Local"
    _crear_perfil_chrome(local)

    carpetas = carpetas_de_cache(["chrome"], raiz_local=local, raiz_roaming=tmp_path)

    nombres = {ruta.name for _, ruta in carpetas}
    assert nombres == {"Cache", "GPUCache"}


def test_ignora_carpetas_que_no_son_perfiles(tmp_path: Path) -> None:
    local = tmp_path / "Local"
    shader = local / "Google" / "Chrome" / "User Data" / "ShaderCache" / "Cache"
    shader.mkdir(parents=True)
    (shader / "shader.bin").write_bytes(b"x")

    carpetas = carpetas_de_cache(["chrome"], raiz_local=local, raiz_roaming=tmp_path)

    assert carpetas == []


def test_simulacion_conserva_todo(tmp_path: Path, config: Config) -> None:
    local = tmp_path / "Local"
    cache, cookies, historial = _crear_perfil_chrome(local)

    resultado = limpiar_cache_navegadores(
        config, aplicar=False, raiz_local=local, raiz_roaming=tmp_path
    )

    assert resultado.archivos == 2
    assert resultado.bytes_liberados == 150
    assert cache.joinpath("datos.bin").exists()
    assert cookies.exists()
    assert historial.exists()


def test_aplicar_borra_cache_y_conserva_datos(tmp_path: Path, config: Config) -> None:
    local = tmp_path / "Local"
    cache, cookies, historial = _crear_perfil_chrome(local)

    resultado = limpiar_cache_navegadores(
        config, aplicar=True, raiz_local=local, raiz_roaming=tmp_path
    )

    assert not (cache / "datos.bin").exists()
    assert cache.is_dir()
    assert cookies.exists()
    assert historial.exists()
    assert resultado.archivos == 2
    assert resultado.errores == 0


def test_detecta_firefox_y_opera(tmp_path: Path) -> None:
    local = tmp_path / "Local"
    roaming = tmp_path / "Roaming"
    firefox = local / "Mozilla" / "Firefox" / "Profiles" / "abc.default" / "cache2"
    firefox.mkdir(parents=True)
    (firefox / "entrada").write_bytes(b"x")
    opera = roaming / "Opera Software" / "Opera Stable" / "Cache"
    opera.mkdir(parents=True)
    (opera / "entrada").write_bytes(b"x")

    carpetas = carpetas_de_cache(["firefox", "opera"], raiz_local=local, raiz_roaming=roaming)

    rutas = {ruta for _, ruta in carpetas}
    assert firefox in rutas
    assert opera in rutas


def test_sin_navegadores_instalados(tmp_path: Path, config: Config) -> None:
    resultado = limpiar_cache_navegadores(
        config, aplicar=True, raiz_local=tmp_path / "vacio", raiz_roaming=tmp_path / "vacio2"
    )
    assert resultado.archivos == 0
    assert resultado.errores == 0
    assert any("No se han encontrado" in nota for nota in resultado.notas)
