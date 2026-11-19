"""Generación de informes en consola, Markdown y JSON."""

from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import Iterable, Sequence
from pathlib import Path

from .modelos import NIVEL_AVISO, NIVEL_CRITICO, Informe
from .utilidades import formatear_tabla, tamano_legible

LOGGER = logging.getLogger("syskeeper.informes")

VERDE = "\033[92m"
AMARILLO = "\033[93m"
ROJO = "\033[91m"
CIAN = "\033[96m"
RESET = "\033[0m"

ETIQUETAS_NIVEL = {
    "ok": "Correcto",
    NIVEL_AVISO: "Aviso",
    NIVEL_CRITICO: "Crítico",
}


def _texto_modo(modo: str) -> str:
    if modo == "aplicado":
        return "APLICADO (cambios realizados)"
    return "SIMULACIÓN (sin cambios)"


def _tabla_md(
    cabeceras: Sequence[str],
    filas: Iterable[Sequence[object]],
    *,
    derecha: Iterable[int] = (),
) -> str:
    indices = set(derecha)
    encabezado = "| " + " | ".join(cabeceras) + " |"
    separador = (
        "| "
        + " | ".join("---:" if indice in indices else "---" for indice in range(len(cabeceras)))
        + " |"
    )
    cuerpo = ["| " + " | ".join(str(celda) for celda in fila) + " |" for fila in filas]
    return "\n".join([encabezado, separador, *cuerpo])


def _texto_opcional(valor: int | None, sufijo: str = "") -> str:
    return "—" if valor is None else f"{valor}{sufijo}"


def _notas(informe: Informe) -> list[str]:
    vistos: set[str] = set()
    resultado: list[str] = []
    for nota in informe.advertencias:
        if nota not in vistos:
            vistos.add(nota)
            resultado.append(nota)
    for limpieza in informe.limpiezas:
        for nota in limpieza.notas:
            if nota not in vistos:
                vistos.add(nota)
                resultado.append(nota)
    for disco in informe.discos:
        for nota in disco.notas:
            if nota not in vistos:
                vistos.add(nota)
                resultado.append(nota)
    return resultado


def construir_markdown(informe: Informe) -> str:
    """Construye el informe en formato Markdown."""
    fecha = informe.fecha.strftime("%d/%m/%Y %H:%M:%S")
    lineas: list[str] = [
        f"# Informe de mantenimiento — {fecha}",
        "",
        f"> Generado por **syskeeper** v{informe.version} · Modo: **{_texto_modo(informe.modo)}**",
        "",
        "## Resumen",
        "",
        _tabla_md(
            ["Métrica", "Valor"],
            [
                ["Archivos procesados", informe.total_archivos],
                ["Espacio liberado", tamano_legible(informe.total_bytes)],
                ["Errores", informe.total_errores],
                ["Discos analizados", len(informe.discos)],
                ["Discos con avisos", len(informe.discos_con_problemas)],
            ],
            derecha=(1,),
        ),
        "",
        "## Limpieza",
        "",
    ]

    if informe.limpiezas:
        filas = [
            [
                resultado.modulo,
                resultado.archivos,
                tamano_legible(resultado.bytes_liberados),
                resultado.errores,
                "Correcto" if resultado.correcto else "Con errores",
            ]
            for resultado in informe.limpiezas
        ]
        lineas.append(
            _tabla_md(
                ["Módulo", "Archivos", "Espacio", "Errores", "Estado"],
                filas,
                derecha=(1, 2, 3),
            )
        )
    else:
        lineas.append("_No se ejecutaron módulos de limpieza._")
    lineas.append("")

    lineas.extend(["## Salud de los discos", ""])
    if informe.discos:
        filas_discos = [
            [
                disco.nombre,
                disco.tipo,
                disco.salud,
                _texto_opcional(disco.desgaste, " %"),
                _texto_opcional(disco.temperatura, " °C"),
                _texto_opcional(disco.horas_encendido, " h"),
                ETIQUETAS_NIVEL.get(disco.nivel_alerta(), disco.nivel_alerta()),
            ]
            for disco in informe.discos
        ]
        lineas.append(
            _tabla_md(
                ["Disco", "Tipo", "Salud", "Desgaste", "Temp.", "Horas", "Alerta"],
                filas_discos,
                derecha=(3, 4, 5),
            )
        )
    else:
        lineas.append(
            "_No se pudieron obtener datos SMART. Ejecuta `syskeeper smart` "
            "como administrador para ampliar la información._"
        )
    lineas.append("")

    if informe.espacio:
        lineas.extend(["## Espacio en disco", ""])
        lineas.append(
            _tabla_md(
                ["Unidad", "Total", "Libre", "Uso"],
                [
                    [
                        unidad,
                        tamano_legible(total),
                        tamano_legible(libre),
                        f"{(1 - libre / total) * 100:.1f} %".replace(".", ",") if total else "—",
                    ]
                    for unidad, total, libre in informe.espacio
                ],
                derecha=(1, 2, 3),
            )
        )
        lineas.append("")

    notas = _notas(informe)
    lineas.extend(["## Notas y advertencias", ""])
    if notas:
        lineas.extend(f"- {nota}" for nota in notas)
    else:
        lineas.append("- Sin advertencias.")
    lineas.extend(
        [
            "",
            "---",
            "",
            "_Informe generado automáticamente por "
            "[syskeeper](https://github.com/albertourizar/syskeeper). "
            "Revisa siempre el modo de ejecución antes de borrar archivos._",
            "",
        ]
    )
    return "\n".join(lineas)


def guardar_informe(informe: Informe, carpeta: Path) -> list[Path]:
    """Escribe el informe en Markdown y JSON. Devuelve las rutas creadas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = informe.fecha.strftime("%Y%m%d_%H%M%S")
    ruta_md = carpeta / f"informe_{marca}.md"
    ruta_json = carpeta / f"informe_{marca}.json"

    ruta_md.write_text(construir_markdown(informe), encoding="utf-8")
    ruta_json.write_text(
        json.dumps(informe.a_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return [ruta_md, ruta_json]


def purgar_informes(carpeta: Path, dias: int) -> int:
    """Borra informes más antiguos que ``dias``. Devuelve cuántos eliminó."""
    if dias <= 0 or not carpeta.is_dir():
        return 0
    limite = time.time() - dias * 86400
    eliminados = 0
    for ruta in carpeta.glob("informe_*.*"):
        try:
            if ruta.is_file() and ruta.stat().st_mtime < limite:
                ruta.unlink()
                eliminados += 1
        except OSError:
            continue
    return eliminados


def _color(texto: str, codigo: str, activo: bool) -> str:
    return f"{codigo}{texto}{RESET}" if activo else texto


def _color_nivel(nivel: str, activo: bool) -> str:
    codigos = {"ok": VERDE, NIVEL_AVISO: AMARILLO, NIVEL_CRITICO: ROJO}
    etiqueta = ETIQUETAS_NIVEL.get(nivel, nivel)
    return _color(etiqueta, codigos.get(nivel, ""), activo)


def imprimir_informe(informe: Informe, *, color: bool | None = None) -> None:
    """Muestra el informe por consola con tablas alineadas."""
    if color is None:
        color = sys.stdout.isatty()
    separador = "=" * 72
    fecha = informe.fecha.strftime("%d/%m/%Y %H:%M:%S")

    print()
    print(_color(separador, CIAN, color))
    print(_color(f" syskeeper v{informe.version} · {fecha}", CIAN, color))
    print(_color(f" Modo: {_texto_modo(informe.modo)}", CIAN, color))
    print(_color(separador, CIAN, color))
    resumen = (
        f" Archivos: {informe.total_archivos}   "
        f"Espacio: {tamano_legible(informe.total_bytes)}   "
        f"Errores: {informe.total_errores}"
    )
    print(resumen)
    print()

    if informe.limpiezas:
        filas = [
            [
                resultado.modulo,
                resultado.archivos,
                tamano_legible(resultado.bytes_liberados),
                resultado.errores,
                "OK" if resultado.correcto else "Con errores",
            ]
            for resultado in informe.limpiezas
        ]
        print(
            formatear_tabla(
                ["MÓDULO", "ARCHIVOS", "ESPACIO", "ERRORES", "ESTADO"],
                filas,
                alinear_derecha=(1, 2, 3),
            )
        )
        print()
    else:
        print("No se ejecutaron módulos de limpieza.")
        print()

    if informe.discos:
        filas_discos = [
            [
                disco.nombre,
                disco.tipo,
                disco.salud,
                _texto_opcional(disco.desgaste, " %"),
                _texto_opcional(disco.temperatura, " °C"),
                _texto_opcional(disco.horas_encendido, " h"),
                _color_nivel(disco.nivel_alerta(), color),
            ]
            for disco in informe.discos
        ]
        print(
            formatear_tabla(
                ["DISCO", "TIPO", "SALUD", "DESGASTE", "TEMP.", "HORAS", "ALERTA"],
                filas_discos,
                alinear_derecha=(3, 4, 5),
            )
        )
        print()

    if informe.espacio:
        filas_espacio = [
            [
                unidad,
                tamano_legible(total),
                tamano_legible(libre),
                f"{(1 - libre / total) * 100:.1f} %".replace(".", ",") if total else "—",
            ]
            for unidad, total, libre in informe.espacio
        ]
        print(
            formatear_tabla(
                ["UNIDAD", "TOTAL", "LIBRE", "USO"], filas_espacio, alinear_derecha=(1, 2, 3)
            )
        )
        print()

    notas = _notas(informe)
    if notas:
        print("Notas y advertencias:")
        for nota in notas:
            print(f"  · {nota}")
        print()

    if informe.hay_problemas:
        print(
            _color(
                "Resultado: se han detectado avisos. Revisa el informe antes de continuar.",
                AMARILLO,
                color,
            )
        )
    else:
        print(_color("Resultado: todo correcto.", VERDE, color))
    print()


__all__ = [
    "construir_markdown",
    "guardar_informe",
    "imprimir_informe",
    "purgar_informes",
]
