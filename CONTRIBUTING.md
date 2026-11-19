# Contribuir a syskeeper

Gracias por querer mejorar el proyecto. Esta guía resume el entorno, el estilo y
el proceso de revisión.

## Antes de empezar

- Abre un **issue** para proponer funciones nuevas o cambios de comportamiento.
- Para errores, adjunta la versión de Windows, la de Python, el comando exacto y
  el informe JSON (sin rutas personales si lo compartes en público).
- No publiques datos sensibles en issues: nombres de usuario, seriales de disco
  o rutas privadas.

## Entorno de desarrollo

```powershell
git clone https://github.com/albertourizar/syskeeper.git
cd syskeeper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Comprobación rápida:

```powershell
python -m pytest -q
python -m ruff check src tests iniciar.py
python -m ruff format --check src tests iniciar.py
python -m mypy src iniciar.py
```

## Estilo

- Código y nombres de funciones en **español**, siguiendo el resto del paquete.
- Tipado en todas las funciones públicas (`from __future__ import annotations`).
- Líneas de hasta 100 caracteres, formato de `ruff format`.
- Docstrings en español con el formato de reStructuredText ligero ya usado.
- Sin dependencias nuevas obligatorias: justifica cualquier extra.
- Los módulos no deben escribir informes ni llamar a `print`; devuelven
  `ResultadoLimpieza` y el CLI decide la presentación.

## Pruebas

- Toda función nueva necesita al menos una prueba de camino feliz y otra de
  error.
- Usa `tmp_path` y las fixtures de `tests/conftest.py`; nunca borres archivos
  reales del usuario.
- Simula PowerShell inyectando el parámetro `ejecutor` o con `monkeypatch`.
- Mantén la cobertura por encima del 80 %.
- Si la prueba es específica de Windows, márcala con
  `@pytest.mark.skipif(not es_windows(), ...)`.

## Commits

Se usa [Conventional Commits](https://www.conventionalcommits.org/es/):

```
feat: añadir limpieza de miniaturas
fix: evitar borrar archivos en uso
docs: aclarar el modo desatendido
test: cubrir la papelera vacía
ci: ejecutar mypy en Windows
```

Un commit debe contar una sola intención. Los mensajes pueden ir en español.

## Pull requests

1. Crea una rama desde `main`: `feat/mi-mejora` o `fix/mi-error`.
2. Añade o actualiza pruebas y documentación.
3. Ejecuta la batería completa y pega el resultado en la descripción.
4. Rellena la plantilla de PR y enlaza el issue relacionado.
5. Espera a que la CI esté en verde.

### Checklist

- [ ] `pytest` pasa.
- [ ] `ruff check` y `ruff format --check` pasan.
- [ ] `mypy src iniciar.py` pasa.
- [ ] `CHANGELOG.md` actualizado si afecta al usuario.
- [ ] Documentación revisada (README, `docs/`).
- [ ] No se incluyen rutas personales, tokens ni capturas con datos privados.

## Áreas donde ayudar

- Pruebas de integración con más modelos de disco y navegadores.
- Traducción de los informes a otros idiomas (manteniendo español por defecto).
- Detección de cachés de navegadores menos comunes.
- Mejoras de accesibilidad de la salida por consola.

## Código de conducta

Al participar aceptas el [Código de conducta](CODE_OF_CONDUCT.md). Sé respetuoso
y asume buena fe.
