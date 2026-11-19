"""Modelos de datos compartidos por los módulos y los informes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

NIVEL_OK = "ok"
NIVEL_AVISO = "aviso"
NIVEL_CRITICO = "critico"


@dataclass
class ResultadoLimpieza:
    """Resultado de un módulo de limpieza."""

    modulo: str
    aplicado: bool = False
    archivos: int = 0
    bytes_liberados: int = 0
    errores: int = 0
    omitidos: int = 0
    notas: list[str] = field(default_factory=list)

    def fusionar(self, otro: ResultadoLimpieza) -> None:
        """Suma los contadores de otro resultado al actual."""
        self.archivos += otro.archivos
        self.bytes_liberados += otro.bytes_liberados
        self.errores += otro.errores
        self.omitidos += otro.omitidos
        self.notas.extend(otro.notas)

    @property
    def correcto(self) -> bool:
        return self.errores == 0

    def a_dict(self) -> dict[str, Any]:
        return {
            "modulo": self.modulo,
            "aplicado": self.aplicado,
            "archivos": self.archivos,
            "bytes_liberados": self.bytes_liberados,
            "errores": self.errores,
            "omitidos": self.omitidos,
            "notas": list(self.notas),
        }


@dataclass
class SaludDisco:
    """Datos SMART y de fiabilidad de un disco físico."""

    nombre: str
    tipo: str = "Desconocido"
    estado: str = "Desconocido"
    salud: str = "Desconocido"
    tamano_bytes: int = 0
    desgaste: int | None = None
    temperatura: int | None = None
    horas_encendido: int | None = None
    errores_lectura: int | None = None
    errores_escritura: int | None = None
    prediccion_fallo: str | None = None
    notas: list[str] = field(default_factory=list)

    def nivel_alerta(self) -> str:
        """Clasifica la salud del disco en ``ok``, ``aviso`` o ``critico``."""
        salud = self.salud.lower()
        estado = self.estado.lower()
        prediccion = (self.prediccion_fallo or "").lower()

        if (
            "unhealthy" in salud
            or "fail" in salud
            or "unhealthy" in estado
            or "pred fail" in prediccion
            or "fail" in prediccion
        ):
            return NIVEL_CRITICO
        if self.desgaste is not None and self.desgaste >= 95:
            return NIVEL_CRITICO
        if self.temperatura is not None and self.temperatura >= 70:
            return NIVEL_CRITICO

        if self.desgaste is not None and self.desgaste >= 80:
            return NIVEL_AVISO
        if self.temperatura is not None and self.temperatura >= 60:
            return NIVEL_AVISO
        if self.errores_lectura is not None and self.errores_lectura > 0:
            return NIVEL_AVISO
        if self.errores_escritura is not None and self.errores_escritura > 0:
            return NIVEL_AVISO
        if "warning" in estado or "degraded" in estado or "warning" in salud:
            return NIVEL_AVISO
        return NIVEL_OK

    @property
    def sano(self) -> bool:
        return self.nivel_alerta() == NIVEL_OK

    def a_dict(self) -> dict[str, Any]:
        return {
            "nombre": self.nombre,
            "tipo": self.tipo,
            "estado": self.estado,
            "salud": self.salud,
            "tamano_bytes": self.tamano_bytes,
            "desgaste": self.desgaste,
            "temperatura": self.temperatura,
            "horas_encendido": self.horas_encendido,
            "errores_lectura": self.errores_lectura,
            "errores_escritura": self.errores_escritura,
            "prediccion_fallo": self.prediccion_fallo,
            "nivel_alerta": self.nivel_alerta(),
            "notas": list(self.notas),
        }


@dataclass
class Informe:
    """Informe completo de una ejecución."""

    version: str
    fecha: datetime
    modo: str
    limpiezas: list[ResultadoLimpieza] = field(default_factory=list)
    discos: list[SaludDisco] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    espacio: list[tuple[str, int, int]] = field(default_factory=list)

    @property
    def total_archivos(self) -> int:
        return sum(resultado.archivos for resultado in self.limpiezas)

    @property
    def total_bytes(self) -> int:
        return sum(resultado.bytes_liberados for resultado in self.limpiezas)

    @property
    def total_errores(self) -> int:
        return sum(resultado.errores for resultado in self.limpiezas)

    @property
    def discos_con_problemas(self) -> list[SaludDisco]:
        return [disco for disco in self.discos if not disco.sano]

    @property
    def hay_problemas(self) -> bool:
        return bool(self.total_errores or self.discos_con_problemas or self.advertencias)

    def a_dict(self) -> dict[str, Any]:
        return {
            "programa": "syskeeper",
            "version": self.version,
            "fecha": self.fecha.isoformat(timespec="seconds"),
            "modo": self.modo,
            "resumen": {
                "archivos": self.total_archivos,
                "bytes_liberados": self.total_bytes,
                "errores": self.total_errores,
                "discos": len(self.discos),
                "discos_con_problemas": len(self.discos_con_problemas),
            },
            "limpiezas": [resultado.a_dict() for resultado in self.limpiezas],
            "discos": [disco.a_dict() for disco in self.discos],
            "espacio": [
                {"unidad": unidad, "total_bytes": total, "libre_bytes": libre}
                for unidad, total, libre in self.espacio
            ],
            "advertencias": list(self.advertencias),
        }
