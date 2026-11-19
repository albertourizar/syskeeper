"""Pruebas del menú interactivo de inicio."""

from __future__ import annotations

import builtins

import iniciar
from iniciar import ACCIONES, ejecutar, main


def test_acciones_disponibles() -> None:
    assert set(ACCIONES) == {"1", "2", "3", "4", "5", "6"}
    assert ACCIONES["1"][1] == ["limpiar"]
    assert ACCIONES["3"][1] == ["smart"]
    assert ACCIONES["5"][1] == ["todo", "--aplicar"]


def test_ejecutar_delega_en_el_paquete(monkeypatch) -> None:
    capturado: dict[str, object] = {}

    def falso(comando, cwd=None):
        capturado["comando"] = comando
        capturado["cwd"] = cwd
        return 1

    monkeypatch.setattr(iniciar.subprocess, "call", falso)

    assert ejecutar(["smart"]) == 1
    comando = capturado["comando"]
    assert isinstance(comando, list)
    assert comando[1:] == ["-m", "syskeeper", "smart"]


def test_opcion_invalida_vuelve_al_menu(monkeypatch, capsys) -> None:
    entradas = iter(["9", "", "0"])
    monkeypatch.setattr(builtins, "input", lambda *_: next(entradas))

    assert main() == 0
    salida = capsys.readouterr().out
    assert "Opción no válida" in salida
    assert "Hasta luego" in salida


def test_accion_se_ejecuta_y_se_puede_salir(monkeypatch, capsys) -> None:
    entradas = iter(["3", "", "0"])
    monkeypatch.setattr(builtins, "input", lambda *_: next(entradas))
    llamadas: list[list[str]] = []
    monkeypatch.setattr(iniciar, "ejecutar", lambda args: llamadas.append(args) or 0)

    assert main() == 0
    assert llamadas == [["smart"]]
    assert "[OK] Tarea completada." in capsys.readouterr().out


def test_interrupcion_sale_sin_error(monkeypatch) -> None:
    def interrumpir(*_):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", interrumpir)
    assert main() == 0
