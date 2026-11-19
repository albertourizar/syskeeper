"""Pruebas del vaciado de la papelera (PowerShell simulado)."""

from __future__ import annotations

import pytest

from syskeeper.config import Config
from syskeeper.modules import papelera
from syskeeper.utilidades import ErrorPowerShell


@pytest.fixture(autouse=True)
def simular_windows(monkeypatch) -> None:
    monkeypatch.setattr(papelera, "es_windows", lambda: True)


def test_simulacion_mide_sin_vaciar(monkeypatch, config: Config) -> None:
    monkeypatch.setattr(papelera, "medir_papelera", lambda: (3, 4096))
    llamadas: list[str] = []
    monkeypatch.setattr(
        papelera,
        "ejecutar_powershell",
        lambda script, timeout=120: llamadas.append(script) or "",
    )

    resultado = papelera.vaciar_papelera(config, aplicar=False)

    assert resultado.archivos == 3
    assert resultado.bytes_liberados == 4096
    assert resultado.errores == 0
    assert llamadas == []
    assert any("Simulación" in nota for nota in resultado.notas)


def test_aplicar_vacia_y_calcula_liberado(monkeypatch, config: Config) -> None:
    mediciones = iter([(3, 4096), (0, 0)])
    monkeypatch.setattr(papelera, "medir_papelera", lambda: next(mediciones))
    llamadas: list[str] = []

    def ejecutar(script: str, timeout: int = 120) -> str:
        llamadas.append(script)
        return ""

    monkeypatch.setattr(papelera, "ejecutar_powershell", ejecutar)

    resultado = papelera.vaciar_papelera(config, aplicar=True)

    assert resultado.archivos == 3
    assert resultado.bytes_liberados == 4096
    assert len(llamadas) == 1
    assert "Clear-RecycleBin" in llamadas[0]


def test_papelera_vacia(monkeypatch, config: Config) -> None:
    monkeypatch.setattr(papelera, "medir_papelera", lambda: (0, 0))
    resultado = papelera.vaciar_papelera(config, aplicar=True)
    assert resultado.archivos == 0
    assert any("ya estaba vacía" in nota for nota in resultado.notas)


def test_error_al_medir(monkeypatch, config: Config) -> None:
    def fallar() -> tuple[int, int]:
        raise ErrorPowerShell("sin COM")

    monkeypatch.setattr(papelera, "medir_papelera", fallar)
    resultado = papelera.vaciar_papelera(config, aplicar=True)
    assert resultado.errores == 1
    assert "sin COM" in resultado.notas[0]


def test_papelera_desactivada(config: Config) -> None:
    config.limpiar_papelera = False
    resultado = papelera.vaciar_papelera(config, aplicar=True)
    assert resultado.archivos == 0
    assert resultado.errores == 0


def test_metodo_alternativo_si_falla_clear(monkeypatch, config: Config) -> None:
    mediciones = iter([(2, 100), (0, 0)])
    monkeypatch.setattr(papelera, "medir_papelera", lambda: next(mediciones))
    llamadas: list[str] = []

    def ejecutar(script: str, timeout: int = 120) -> str:
        llamadas.append(script)
        if "Clear-RecycleBin" in script:
            raise ErrorPowerShell("no disponible")
        return ""

    monkeypatch.setattr(papelera, "ejecutar_powershell", ejecutar)

    resultado = papelera.vaciar_papelera(config, aplicar=True)

    assert resultado.errores == 0
    assert len(llamadas) == 2
    assert "InvokeVerb" in llamadas[1]
