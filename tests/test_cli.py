"""Pruebas de la interfaz de línea de comandos."""

from __future__ import annotations

from pathlib import Path

import pytest

from syskeeper import cli
from syskeeper.modelos import ResultadoLimpieza, SaludDisco


def _instalar_fakes(monkeypatch) -> dict[str, bool]:
    registro: dict[str, bool] = {}

    def limpiar_temporales(config, *, aplicar, directorios=None):
        registro["temporales"] = aplicar
        return ResultadoLimpieza(
            modulo="Archivos temporales",
            aplicado=aplicar,
            archivos=2,
            bytes_liberados=100,
        )

    def vaciar_papelera(config, *, aplicar):
        registro["papelera"] = aplicar
        return ResultadoLimpieza(modulo="Papelera de reciclaje", aplicado=aplicar)

    def limpiar_cache(config, *, aplicar, **kwargs):
        registro["navegadores"] = aplicar
        return ResultadoLimpieza(modulo="Caché de navegadores", aplicado=aplicar)

    monkeypatch.setattr(cli.temporales, "limpiar_temporales", limpiar_temporales)
    monkeypatch.setattr(cli.papelera, "vaciar_papelera", vaciar_papelera)
    monkeypatch.setattr(cli.cache_navegadores, "limpiar_cache_navegadores", limpiar_cache)
    return registro


def test_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.construir_parser().parse_args(["--version"])
    assert exc.value.code == 0
    assert "1.0.0" in capsys.readouterr().out


def test_sin_comando_muestra_ayuda(capsys) -> None:
    assert cli.main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_limpiar_simula_por_defecto(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    registro = _instalar_fakes(monkeypatch)

    codigo = cli.main(["limpiar", "--solo", "temporales", "--sin-espacio", "--sin-color"])

    assert codigo == 0
    assert registro["temporales"] is False
    assert "SIMULACIÓN" in capsys.readouterr().out
    assert (tmp_path / "informes").is_dir()


def test_aplicar_pide_confirmacion_y_cancela(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    registro = _instalar_fakes(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda *_: "no")

    codigo = cli.main(
        ["limpiar", "--solo", "temporales", "--aplicar", "--sin-espacio", "--sin-color"]
    )

    assert codigo == 0
    assert "temporales" not in registro
    assert "cancelada" in capsys.readouterr().out.lower()


def test_aplicar_con_si(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    registro = _instalar_fakes(monkeypatch)

    codigo = cli.main(
        [
            "limpiar",
            "--solo",
            "temporales,papelera,navegadores",
            "--aplicar",
            "--si",
            "--sin-espacio",
            "--sin-color",
        ]
    )

    assert codigo == 0
    assert registro == {"temporales": True, "papelera": True, "navegadores": True}


def test_informe_ignora_aplicar(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    registro = _instalar_fakes(monkeypatch)
    monkeypatch.setattr(cli.smart, "obtener_discos", lambda **kwargs: [])

    codigo = cli.main(
        [
            "informe",
            "--solo",
            "temporales",
            "--aplicar",
            "--si",
            "--sin-espacio",
            "--sin-color",
        ]
    )

    assert codigo == 0
    assert registro["temporales"] is False


def test_salud_critica_devuelve_codigo_1(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli.smart,
        "obtener_discos",
        lambda **kwargs: [SaludDisco(nombre="Disco", salud="Unhealthy", estado="OK")],
    )

    assert cli.main(["smart", "--sin-espacio", "--sin-color"]) == 1


def test_salud_correcta_devuelve_codigo_0(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli.smart,
        "obtener_discos",
        lambda **kwargs: [SaludDisco(nombre="Disco", salud="Healthy", estado="OK")],
    )

    assert cli.main(["smart", "--sin-espacio", "--sin-color"]) == 0


def test_sin_datos_smart_devuelve_codigo_1(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.smart, "obtener_discos", lambda **kwargs: [])

    assert cli.main(["smart", "--sin-espacio", "--sin-color"]) == 1
    assert "No se pudieron obtener datos SMART" in capsys.readouterr().out


def test_modulo_desconocido(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli.main(["limpiar", "--solo", "inventado", "--sin-espacio"]) == 2


def test_min_horas_negativo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli.main(["limpiar", "--min-horas", "-1", "--sin-espacio"]) == 2


def test_config_ejemplo(tmp_path: Path) -> None:
    destino = tmp_path / "config.json"
    assert cli.main(["config", "--ejemplo", str(destino)]) == 0
    assert destino.is_file()
