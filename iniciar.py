"""Menú interactivo de syskeeper para usar con doble clic.

Se lanza desde ``Iniciar syskeeper.bat`` o directamente con ``python iniciar.py``.
No contiene lógica de limpieza: delega en el comando ``syskeeper`` instalado.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ANCHO = 60

try:
    from syskeeper import __version__
except ImportError:  # pragma: no cover - solo si el paquete no está instalado
    __version__ = "1.0.0"

ACCIONES: dict[str, tuple[str, list[str]]] = {
    "1": ("Simular limpieza (no borra nada)", ["limpiar"]),
    "2": ("Limpiar de verdad (pedirá escribir SI)", ["limpiar", "--aplicar"]),
    "3": ("Analizar la salud de los discos (SMART)", ["smart"]),
    "4": ("Generar un informe sin borrar nada", ["informe"]),
    "5": ("Limpieza completa + SMART (pedirá escribir SI)", ["todo", "--aplicar"]),
    "6": ("Crear config.json de ejemplo", ["config", "--ejemplo"]),
}


def limpiar_pantalla() -> None:
    """Limpia la consola solo cuando hay una terminal interactiva."""
    if not sys.stdout.isatty():
        print()
        return
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_menu() -> None:
    print("=" * ANCHO)
    print(f"   syskeeper {__version__} · mantenimiento y limpieza de Windows")
    print("=" * ANCHO)
    print()
    for clave in ("1", "2", "3", "4", "5", "6"):
        print(f"  {clave}. {ACCIONES[clave][0]}")
    print("  0. Salir")
    print()


def esperar() -> None:
    try:
        input("Pulsa Enter para volver al menú...")
    except (EOFError, KeyboardInterrupt):
        print()


def ejecutar(argumentos: list[str]) -> int:
    """Ejecuta el comando syskeeper con los argumentos indicados."""
    comando = [sys.executable, "-m", "syskeeper", *argumentos]
    try:
        return subprocess.call(comando, cwd=str(RAIZ))
    except OSError as exc:
        print(f"\n[ERROR] No se pudo ejecutar syskeeper: {exc}")
        return 2


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    while True:
        limpiar_pantalla()
        mostrar_menu()
        try:
            opcion = input("Elige una opción y pulsa Enter: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Hasta luego.")
            return 0

        if opcion == "0":
            print("Hasta luego.")
            return 0

        accion = ACCIONES.get(opcion)
        if accion is None:
            print("\n[AVISO] Opción no válida. Elige un número del 0 al 6.")
            esperar()
            continue

        descripcion, argumentos = accion
        print(f"\n[{descripcion}]\n")
        codigo = ejecutar(argumentos)

        if codigo == 0:
            print("\n[OK] Tarea completada.")
        elif codigo == 1:
            print("\n[AVISO] Terminó con avisos. Revisa el informe generado.")
        elif codigo == 130:
            print("\n[AVISO] Cancelado por el usuario.")
        else:
            print(f"\n[ERROR] La tarea falló con el código {codigo}.")
            print("Revisa el mensaje anterior o el registro en")
            print(r"%LOCALAPPDATA%\syskeeper\logs\syskeeper.log")

        esperar()


if __name__ == "__main__":
    sys.exit(main())
