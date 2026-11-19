"""Permite ejecutar el programa con ``python -m syskeeper``."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
