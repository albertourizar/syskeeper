"""Carga y validación de la configuración del programa."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

NAVEGADORES_VALIDOS = ("chrome", "edge", "firefox", "brave", "opera")
NOMBRE_CONFIG = "config.json"

TIPOS_CONFIG: dict[str, type] = {
    "antiguedad_horas": float,
    "antiguedad_cache_horas": float,
    "incluir_temporales_sistema": bool,
    "incluir_prefetch": bool,
    "limpiar_papelera": bool,
    "navegadores": list,
    "directorios_temporales_extra": list,
    "rutas_protegidas_extra": list,
    "generar_informe": bool,
    "carpeta_informes": str,
    "retencion_informes_dias": int,
    "incluir_espacio_libre": bool,
}


class ConfigInvalida(ValueError):
    """La configuración no tiene el formato esperado."""


@dataclass
class Config:
    """Opciones de ejecución de syskeeper."""

    antiguedad_horas: float = 24.0
    antiguedad_cache_horas: float = 0.0
    incluir_temporales_sistema: bool = True
    incluir_prefetch: bool = False
    limpiar_papelera: bool = True
    navegadores: list[str] = field(
        default_factory=lambda: ["chrome", "edge", "firefox", "brave", "opera"]
    )
    directorios_temporales_extra: list[str] = field(default_factory=list)
    rutas_protegidas_extra: list[str] = field(default_factory=list)
    generar_informe: bool = True
    carpeta_informes: str = "informes"
    retencion_informes_dias: int = 90
    incluir_espacio_libre: bool = True

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def config_por_defecto() -> Config:
    """Devuelve una configuración nueva con los valores recomendados."""
    return Config()


def _validar_tipo(nombre: str, valor: Any, esperado: type) -> Any:
    if esperado is float:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ConfigInvalida(f"'{nombre}' debe ser un número.")
        if valor < 0:
            raise ConfigInvalida(f"'{nombre}' no puede ser negativo.")
        return float(valor)
    if esperado is int:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ConfigInvalida(f"'{nombre}' debe ser un número entero.")
        if valor < 0:
            raise ConfigInvalida(f"'{nombre}' no puede ser negativo.")
        return valor
    if esperado is bool:
        if not isinstance(valor, bool):
            raise ConfigInvalida(f"'{nombre}' debe ser true o false.")
        return valor
    if esperado is list:
        if not isinstance(valor, list) or not all(isinstance(item, str) for item in valor):
            raise ConfigInvalida(f"'{nombre}' debe ser una lista de textos.")
        return [item.strip() for item in valor if item.strip()]
    if esperado is str:
        if not isinstance(valor, str):
            raise ConfigInvalida(f"'{nombre}' debe ser un texto.")
        return valor
    raise ConfigInvalida(f"Tipo no soportado para '{nombre}'.")


def _normalizar_navegadores(valor: list[str]) -> list[str]:
    resultado: list[str] = []
    for nombre in valor:
        clave = nombre.strip().lower()
        if clave not in NAVEGADORES_VALIDOS:
            raise ConfigInvalida(
                f"Navegador desconocido: '{nombre}'. "
                f"Valores admitidos: {', '.join(NAVEGADORES_VALIDOS)}."
            )
        if clave not in resultado:
            resultado.append(clave)
    return resultado


def cargar_config(ruta: str | Path | None = None) -> Config:
    """Carga la configuración desde un JSON.

    Si ``ruta`` es ``None`` se busca ``config.json`` en el directorio actual y,
    si no existe, se usan los valores por defecto.
    """
    if ruta is None:
        candidata = Path(NOMBRE_CONFIG)
        if not candidata.is_file():
            return config_por_defecto()
        archivo = candidata
    else:
        archivo = Path(ruta)
        if not archivo.is_file():
            raise ConfigInvalida(f"No se ha encontrado el archivo de configuración: {archivo}")

    try:
        contenido = json.loads(archivo.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ConfigInvalida(f"El JSON no es válido ({archivo}): {exc}") from exc

    if not isinstance(contenido, dict):
        raise ConfigInvalida("La raíz de la configuración debe ser un objeto JSON.")

    tipos = TIPOS_CONFIG
    valores: dict[str, Any] = {}
    for nombre, valor in contenido.items():
        esperado = tipos.get(nombre)
        if esperado is None:
            continue
        if nombre == "navegadores":
            valores[nombre] = _normalizar_navegadores(_validar_tipo(nombre, valor, list))
        else:
            valores[nombre] = _validar_tipo(nombre, valor, esperado)

    return Config(**valores)


def guardar_config_ejemplo(ruta: str | Path = NOMBRE_CONFIG) -> Path:
    """Escribe un archivo ``config.json`` con todos los valores por defecto."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(config_por_defecto().a_dict(), ensure_ascii=False, indent=2)
    destino.write_text(texto + "\n", encoding="utf-8")
    return destino
