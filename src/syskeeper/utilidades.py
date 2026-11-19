"""Utilidades compartidas: rutas protegidas, tamaños, tablas y PowerShell."""

from __future__ import annotations

import contextlib
import ctypes
import os
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

UNIDADES = ("B", "KB", "MB", "GB", "TB", "PB")
ATRIBUTO_PUNTO_REPARSE = 0x400
_PREFIJO_UTF8 = "try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }; "


class ErrorPowerShell(RuntimeError):
    """PowerShell no está disponible, falló o devolvió una salida inválida."""


def es_windows() -> bool:
    """Indica si el sistema actual es Windows."""
    return sys.platform.startswith("win")


def es_administrador() -> bool:
    """Devuelve ``True`` si el proceso tiene privilegios de administrador."""
    if not es_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001 - cualquier fallo implica "sin privilegios"
        return False


def tamano_legible(bytes_totales: float) -> str:
    """Convierte una cantidad de bytes en un texto legible (por ejemplo ``1,5 GB``)."""
    valor = float(bytes_totales)
    if valor < 1024:
        return f"{int(valor)} B"
    for unidad in UNIDADES[1:]:
        valor /= 1024
        if valor < 1024 or unidad == UNIDADES[-1]:
            texto = f"{valor:.1f} {unidad}"
            return texto.replace(".", ",")
    return f"{valor:.1f} PB"


def formatear_tabla(
    cabeceras: Sequence[str],
    filas: Iterable[Sequence[object]],
    *,
    alinear_derecha: Iterable[int] = (),
) -> str:
    """Devuelve una tabla de texto alineada, sin dependencias externas."""
    datos = [[str(celda) for celda in fila] for fila in filas]
    total_columnas = len(cabeceras)
    for fila in datos:
        if len(fila) != total_columnas:
            raise ValueError(f"La fila tiene {len(fila)} columnas y se esperaban {total_columnas}.")
    derecha = set(alinear_derecha)
    anchos = [len(cabecera) for cabecera in cabeceras]
    for fila in datos:
        for indice, celda in enumerate(fila):
            anchos[indice] = max(anchos[indice], len(celda))

    def componer(fila: Sequence[str]) -> str:
        celdas = []
        for indice, celda in enumerate(fila):
            if indice in derecha:
                celdas.append(celda.rjust(anchos[indice]))
            else:
                celdas.append(celda.ljust(anchos[indice]))
        return "  ".join(celdas).rstrip()

    separador = "  ".join("-" * ancho for ancho in anchos)
    lineas = [componer(list(cabeceras)), separador]
    lineas.extend(componer(fila) for fila in datos)
    return "\n".join(lineas)


def directorios_personales() -> list[Path]:
    """Rutas del perfil del usuario que el programa nunca debe tocar."""
    perfil = Path(os.environ.get("USERPROFILE") or Path.home())
    nombres = (
        "Documents",
        "Desktop",
        "Downloads",
        "Pictures",
        "Music",
        "Videos",
        "OneDrive",
        "Favorites",
        "Saved Games",
        "Contacts",
        "Links",
        "AppData/Roaming/Microsoft",
        ".ssh",
    )
    return [perfil / nombre for nombre in nombres]


def rutas_protegidas(extras: Iterable[Path] = ()) -> list[Path]:
    """Construye la lista de rutas sensibles que no se pueden modificar."""
    candidatos: list[Path] = []
    windir = os.environ.get("WINDIR")
    if windir:
        raiz_windows = Path(windir)
        candidatos.append(raiz_windows)
        candidatos.extend(raiz_windows / nombre for nombre in ("System32", "SysWOW64", "WinSxS"))
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        valor = os.environ.get(variable)
        if valor:
            candidatos.append(Path(valor))
    candidatos.extend(directorios_personales())
    candidatos.extend(Path(extra) for extra in extras)

    resultado: list[Path] = []
    for candidato in candidatos:
        try:
            resultado.append(candidato.resolve())
        except OSError:
            resultado.append(candidato)
    return resultado


def ruta_protegida(
    ruta: Path | str,
    extras: Iterable[Path] = (),
    *,
    permitidas: Iterable[Path] = (),
) -> bool:
    """Comprueba si ``ruta`` es una raíz de unidad o está dentro de una ruta protegida.

    ``permitidas`` contiene excepciones explícitas (por ejemplo, la carpeta
    ``C:\\Windows\\Temp`` cuando el usuario ha pedido limpiarla).
    """
    objetivo = Path(ruta)
    with contextlib.suppress(OSError):
        objetivo = objetivo.resolve()
    if objetivo.parent == objetivo:
        return True
    if objetivo.name.lower() == "$recycle.bin":
        return True
    for extra in extras:
        try:
            ruta_extra = Path(extra).resolve()
            if objetivo == ruta_extra or objetivo.is_relative_to(ruta_extra):
                return True
        except (OSError, ValueError):
            continue
    for permitida in permitidas:
        try:
            ruta_permitida = permitida.resolve()
            if objetivo == ruta_permitida or objetivo.is_relative_to(ruta_permitida):
                return False
        except (OSError, ValueError):
            continue
    for protegida in rutas_protegidas():
        try:
            if objetivo == protegida or objetivo.is_relative_to(protegida):
                return True
        except (OSError, ValueError):
            continue
    return False


def recorrer_archivos(directorio: Path, *, horas_minimas: float = 0.0) -> Iterator[Path]:
    """Recorre ``directorio`` y genera los archivos que superan la antigüedad mínima.

    No sigue enlaces simbólicos, puntos de unión ni accesos directos, y tolera
    carpetas sin permisos de lectura.
    """
    limite = time.time() - horas_minimas * 3600
    pendientes = [directorio]
    while pendientes:
        actual = pendientes.pop()
        try:
            with os.scandir(actual) as iterador:
                entradas = list(iterador)
        except OSError:
            continue
        for entrada in entradas:
            try:
                if entrada.is_symlink():
                    continue
                informacion = entrada.stat(follow_symlinks=False)
                atributos = getattr(informacion, "st_file_attributes", 0)
                if atributos & ATRIBUTO_PUNTO_REPARSE:
                    continue
                if entrada.is_dir(follow_symlinks=False):
                    pendientes.append(Path(entrada.path))
                elif entrada.is_file(follow_symlinks=False) and (
                    horas_minimas <= 0 or informacion.st_mtime <= limite
                ):
                    yield Path(entrada.path)
            except OSError:
                continue


def borrar_archivo(ruta: Path) -> None:
    """Elimina un archivo y reintenta tras quitar el atributo de solo lectura."""
    try:
        ruta.unlink()
    except PermissionError:
        os.chmod(ruta, stat.S_IWRITE | stat.S_IREAD)
        ruta.unlink()


def decodificar(datos: bytes) -> str:
    """Decodifica la salida de PowerShell probando las codificaciones habituales."""
    for codificacion in ("utf-8-sig", "utf-8", "cp850"):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return datos.decode("cp1252", errors="replace")


def ejecutar_powershell(script: str, *, timeout: int = 120) -> str:
    """Ejecuta un script de PowerShell y devuelve su salida estándar.

    Lanza :class:`ErrorPowerShell` si el ejecutable no existe, si se agota el
    tiempo de espera o si el proceso termina con error sin devolver datos.
    """
    if not es_windows():
        raise ErrorPowerShell("PowerShell solo está disponible en Windows.")
    ejecutable = shutil.which("powershell") or shutil.which("pwsh")
    if not ejecutable:
        raise ErrorPowerShell("No se ha encontrado PowerShell en el sistema.")
    comando = [
        ejecutable,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        _PREFIJO_UTF8 + script,
    ]
    try:
        proceso = subprocess.run(
            comando,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ErrorPowerShell("PowerShell tardó demasiado en responder.") from exc
    except OSError as exc:
        raise ErrorPowerShell(f"No se pudo ejecutar PowerShell: {exc}") from exc

    salida = decodificar(proceso.stdout).strip()
    error = decodificar(proceso.stderr).strip()
    if proceso.returncode != 0 and not salida:
        detalle = error or f"código de salida {proceso.returncode}"
        raise ErrorPowerShell(f"PowerShell devolvió un error: {detalle}")
    return salida


def carpeta_datos_app() -> Path:
    """Carpeta de datos del programa (registros y caché interna)."""
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "syskeeper"
    return Path.home() / ".local" / "share" / "syskeeper"


def espacio_volumenes() -> list[tuple[str, int, int]]:
    """Devuelve ``(unidad, total, libre)`` usando psutil si está instalado."""
    datos: list[tuple[str, int, int]] = []
    try:
        import psutil

        for particion in psutil.disk_partitions(all=False):
            try:
                uso = psutil.disk_usage(particion.mountpoint)
            except OSError:
                continue
            datos.append((particion.device or particion.mountpoint, uso.total, uso.free))
        if datos:
            return datos
    except ImportError:
        pass

    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        raiz = f"{letra}:\\"
        if not os.path.exists(raiz):
            continue
        try:
            uso = shutil.disk_usage(raiz)
        except OSError:
            continue
        datos.append((raiz, uso.total, uso.free))
    return datos
