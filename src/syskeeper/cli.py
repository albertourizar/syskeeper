"""Interfaz de línea de comandos de syskeeper."""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from . import __version__
from .config import Config, ConfigInvalida, cargar_config, guardar_config_ejemplo
from .informes import guardar_informe, imprimir_informe, purgar_informes
from .modelos import Informe, ResultadoLimpieza, SaludDisco
from .modules import cache_navegadores, papelera, smart, temporales
from .registro import configurar_logger
from .utilidades import es_administrador, espacio_volumenes, tamano_legible

LOGGER = logging.getLogger("syskeeper")

MODULOS = ("temporales", "papelera", "navegadores", "smart")
NOMBRES_MODULOS = {
    "temporales": "Archivos temporales",
    "papelera": "Papelera de reciclaje",
    "navegadores": "Caché de navegadores",
    "smart": "Salud de los discos",
}


def construir_parser() -> argparse.ArgumentParser:
    """Construye el analizador de argumentos."""
    parser = argparse.ArgumentParser(
        prog="syskeeper",
        description=(
            "Automatizador de mantenimiento y limpieza para Windows: "
            "temporales, papelera, cachés de navegadores y salud SMART."
        ),
        epilog=(
            "Por defecto el programa simula la limpieza. Añade --aplicar para borrar de verdad."
        ),
    )
    parser.add_argument("--version", action="version", version=f"syskeeper {__version__}")

    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument(
        "--aplicar",
        action="store_true",
        help="Borra de verdad (sin esta opción solo se simula).",
    )
    comun.add_argument(
        "--si",
        action="store_true",
        help="No pedir confirmación en modo --aplicar (para tareas programadas).",
    )
    comun.add_argument(
        "--config",
        metavar="ARCHIVO",
        help="Ruta al archivo config.json (por defecto: ./config.json).",
    )
    comun.add_argument(
        "--min-horas",
        type=float,
        metavar="N",
        help="Antigüedad mínima en horas para borrar un archivo temporal.",
    )
    comun.add_argument(
        "--solo",
        metavar="LISTA",
        help="Módulos separados por comas: temporales,papelera,navegadores,smart.",
    )
    comun.add_argument(
        "--sin-informe",
        action="store_true",
        help="No guardar el informe en disco.",
    )
    comun.add_argument(
        "--smartctl",
        action="store_true",
        help="Complementar los datos SMART con smartctl si está instalado.",
    )
    comun.add_argument(
        "--incluir-prefetch",
        action="store_true",
        help="Incluir la carpeta Prefetch de Windows (requiere administrador).",
    )
    comun.add_argument(
        "--sin-espacio",
        action="store_true",
        help="No incluir el espacio libre de las unidades en el informe.",
    )
    comun.add_argument(
        "--sin-color",
        action="store_true",
        help="Desactivar los colores en la consola.",
    )
    comun.add_argument("-v", "--verbose", action="store_true", help="Mostrar más detalles.")

    subparsers = parser.add_subparsers(dest="comando", metavar="COMANDO")

    subparsers.add_parser(
        "limpiar",
        parents=[comun],
        help="Limpia temporales, papelera y cachés (simula salvo --aplicar).",
    )
    subparsers.add_parser(
        "smart",
        parents=[comun],
        help="Analiza la salud de los discos (SMART).",
    )
    subparsers.add_parser(
        "informe",
        parents=[comun],
        help="Mide y genera un informe sin borrar nada.",
    )
    subparsers.add_parser(
        "todo",
        parents=[comun],
        help="Limpieza completa y análisis SMART en una sola ejecución.",
    )
    config_parser = subparsers.add_parser(
        "config",
        parents=[comun],
        help="Muestra la configuración efectiva o crea un archivo de ejemplo.",
    )
    config_parser.add_argument(
        "--ejemplo",
        nargs="?",
        const="config.json",
        default=None,
        metavar="ARCHIVO",
        help="Escribe un config.json con los valores por defecto.",
    )
    return parser


def _pedir_confirmacion(modulos: list[str]) -> bool:
    print()
    print("Se van a eliminar archivos de forma permanente:")
    for modulo in modulos:
        print(f"  - {NOMBRES_MODULOS.get(modulo, modulo)}")
    try:
        respuesta = input("Escribe SI para continuar: ").strip()
    except EOFError:
        return False
    if respuesta.upper() != "SI":
        print("Operación cancelada. No se ha borrado nada.")
        return False
    return True


def _seleccionar_modulos(args: argparse.Namespace) -> list[str]:
    if args.solo:
        elegidos = [parte.strip().lower() for parte in args.solo.split(",") if parte.strip()]
        desconocidos = [modulo for modulo in elegidos if modulo not in MODULOS]
        if desconocidos:
            raise ConfigInvalida(
                f"Módulo desconocido en --solo: {', '.join(desconocidos)}. "
                f"Valores válidos: {', '.join(MODULOS)}."
            )
        if not elegidos:
            raise ConfigInvalida("--solo está vacío.")
        return elegidos
    if args.comando == "smart":
        return ["smart"]
    if args.comando == "limpiar":
        return ["temporales", "papelera", "navegadores"]
    return list(MODULOS)


def _aplicar_ajustes(config: Config, args: argparse.Namespace) -> Config:
    if args.min_horas is not None:
        if args.min_horas < 0:
            raise ConfigInvalida("--min-horas no puede ser negativo.")
        config = replace(config, antiguedad_horas=float(args.min_horas))
    if args.incluir_prefetch:
        config = replace(config, incluir_prefetch=True)
    if args.sin_informe:
        config = replace(config, generar_informe=False)
    if args.sin_espacio:
        config = replace(config, incluir_espacio_libre=False)
    return config


def _ejecutar_limpieza(
    modulos: list[str], config: Config, *, aplicar: bool
) -> list[ResultadoLimpieza]:
    resultados: list[ResultadoLimpieza] = []
    for modulo in modulos:
        if modulo == "smart":
            continue
        etiqueta = NOMBRES_MODULOS[modulo]
        accion = "Limpiando" if aplicar else "Analizando"
        print(f"→ {accion}: {etiqueta}...")
        if modulo == "temporales":
            resultado = temporales.limpiar_temporales(config, aplicar=aplicar)
        elif modulo == "papelera":
            resultado = papelera.vaciar_papelera(config, aplicar=aplicar)
        else:
            resultado = cache_navegadores.limpiar_cache_navegadores(config, aplicar=aplicar)
        resultados.append(resultado)
        LOGGER.debug(
            "%s: %s archivos, %s, %s errores",
            etiqueta,
            resultado.archivos,
            tamano_legible(resultado.bytes_liberados),
            resultado.errores,
        )
    return resultados


def _ejecutar_smart(usar_smartctl: bool) -> tuple[list[SaludDisco], list[str]]:
    print("→ Analizando: salud de los discos...")
    discos = smart.obtener_discos(usar_smartctl=usar_smartctl)
    advertencias: list[str] = []
    if not discos:
        advertencias.append(
            "No se pudieron obtener datos SMART. "
            "Ejecuta como administrador o comprueba que PowerShell funciona."
        )
        return discos, advertencias
    for disco in discos:
        if disco.nivel_alerta() != "ok":
            advertencias.append(
                f"El disco '{disco.nombre}' requiere atención (alerta: {disco.nivel_alerta()})."
            )
    return discos, advertencias


def _codigo_salida(informe: Informe) -> int:
    if informe.hay_problemas:
        return 1
    return 0


def _comando_config(args: argparse.Namespace, config: Config) -> int:
    if args.ejemplo is not None:
        destino = guardar_config_ejemplo(args.ejemplo)
        print(f"Configuración de ejemplo creada en: {destino}")
        return 0
    print(json.dumps(config.a_dict(), ensure_ascii=False, indent=2))
    return 0


def _ejecutar(args: argparse.Namespace) -> int:
    config = cargar_config(args.config)
    config = _aplicar_ajustes(config, args)

    if args.comando == "config":
        return _comando_config(args, config)

    configurar_logger(verbose=args.verbose)

    print(f"syskeeper {__version__} — mantenimiento y limpieza para Windows")
    if not es_administrador():
        print(
            "Nota: sin privilegios de administrador no se puede limpiar "
            "C:\\Windows\\Temp ni leer todos los contadores SMART."
        )

    modulos = _seleccionar_modulos(args)
    aplicar = bool(args.aplicar) and args.comando != "informe"
    if args.aplicar and args.comando == "informe":
        print("El comando 'informe' nunca borra archivos: se ignora --aplicar.")

    if aplicar:
        if not args.si and not _pedir_confirmacion(modulos):
            return 0
    else:
        print("Modo SIMULACIÓN: no se borrará nada. Usa --aplicar para ejecutar la limpieza.")

    limpiezas = _ejecutar_limpieza(modulos, config, aplicar=aplicar)

    discos: list[SaludDisco] = []
    advertencias: list[str] = []
    if "smart" in modulos:
        discos, advertencias = _ejecutar_smart(args.smartctl)

    espacio = espacio_volumenes() if config.incluir_espacio_libre else []
    informe = Informe(
        version=__version__,
        fecha=datetime.now(),
        modo="aplicado" if aplicar else "simulacion",
        limpiezas=limpiezas,
        discos=discos,
        advertencias=advertencias,
        espacio=espacio,
    )

    imprimir_informe(informe, color=not args.sin_color)

    if config.generar_informe:
        rutas = guardar_informe(informe, Path(config.carpeta_informes))
        for ruta in rutas:
            print(f"Informe guardado: {ruta}")
        eliminados = purgar_informes(Path(config.carpeta_informes), config.retencion_informes_dias)
        if eliminados:
            print(f"Informes antiguos eliminados: {eliminados}")

    return _codigo_salida(informe)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la aplicación."""
    with contextlib.suppress(AttributeError, OSError):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    parser = construir_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "comando", None):
        parser.print_help()
        return 0

    try:
        return _ejecutar(args)
    except ConfigInvalida as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - última barrera de seguridad
        LOGGER.exception("Error inesperado")
        print(f"Error inesperado: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
