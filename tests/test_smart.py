"""Pruebas del análisis SMART con PowerShell simulado."""

from __future__ import annotations

import json

import pytest

from syskeeper.modelos import NIVEL_AVISO, NIVEL_CRITICO, NIVEL_OK, SaludDisco
from syskeeper.modules import smart
from syskeeper.utilidades import ErrorPowerShell, es_windows

pytestmark = pytest.mark.skipif(not es_windows(), reason="SMART solo en Windows")

DISCOS = [
    {
        "nombre": "SSD de prueba",
        "tipo": "SSD",
        "salud": "Healthy",
        "estado": "OK",
        "tamano": 480000000000,
        "desgaste": 12,
        "temperatura": 38,
        "horas_encendido": 1200,
        "errores_lectura": 0,
        "errores_escritura": 0,
    }
]


def _ejecutor(discos=DISCOS, cim=None):
    def ejecutar(script: str) -> str:
        if "Win32_DiskDrive" in script:
            return json.dumps(
                cim if cim is not None else [{"Model": "SSD de prueba", "Status": "OK"}]
            )
        return json.dumps(discos)

    return ejecutar


def test_obtener_discos_lista() -> None:
    discos = smart.obtener_discos(ejecutor=_ejecutor())
    assert len(discos) == 1
    disco = discos[0]
    assert disco.nombre == "SSD de prueba"
    assert disco.tipo == "SSD"
    assert disco.desgaste == 12
    assert disco.temperatura == 38
    assert disco.prediccion_fallo == "OK"
    assert disco.nivel_alerta() == NIVEL_OK


def test_obtener_discos_unico_objeto() -> None:
    discos = smart.obtener_discos(ejecutor=_ejecutor(discos=DISCOS[0]))
    assert len(discos) == 1


def test_json_invalido_devuelve_vacio() -> None:
    assert smart.obtener_discos(ejecutor=lambda script: "esto no es json") == []


def test_error_de_powershell_devuelve_vacio() -> None:
    def fallar(script: str) -> str:
        raise ErrorPowerShell("sin permisos")

    assert smart.obtener_discos(ejecutor=fallar) == []


@pytest.mark.parametrize(
    ("cambios", "esperado"),
    [
        ({}, NIVEL_OK),
        ({"salud": "Unhealthy"}, NIVEL_CRITICO),
        ({"estado": "Warning"}, NIVEL_AVISO),
        ({"desgaste": 85}, NIVEL_AVISO),
        ({"desgaste": 96}, NIVEL_CRITICO),
        ({"temperatura": 65}, NIVEL_AVISO),
        ({"temperatura": 75}, NIVEL_CRITICO),
        ({"errores_lectura": 2}, NIVEL_AVISO),
    ],
)
def test_nivel_alerta(cambios: dict, esperado: str) -> None:
    datos = {"nombre": "Disco", "salud": "Healthy", "estado": "OK"}
    datos.update(cambios)
    assert SaludDisco(**datos).nivel_alerta() == esperado


def test_prediccion_de_fallo_cim() -> None:
    discos = smart.obtener_discos(
        ejecutor=_ejecutor(cim=[{"Model": "SSD de prueba", "Status": "Pred Fail"}])
    )
    assert discos[0].prediccion_fallo == "Pred Fail"
    assert discos[0].nivel_alerta() == NIVEL_CRITICO


def test_sin_smartctl_anade_nota(monkeypatch) -> None:
    monkeypatch.setattr(smart.shutil, "which", lambda nombre: None)
    discos = smart.obtener_discos(usar_smartctl=True, ejecutor=_ejecutor())
    assert any("smartctl no está instalado" in nota for nota in discos[0].notas)


def test_sin_discos() -> None:
    assert smart.obtener_discos(ejecutor=lambda script: "[]") == []
