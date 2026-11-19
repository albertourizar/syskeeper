# Publicar syskeeper en GitHub (`albertourizar`)

Guía paso a paso para subir el proyecto y crear la primera release.

## 0. Comprobaciones previas

```powershell
cd C:\Users\L4442\syskeeper
python -m pytest -q
python -m ruff check src tests
python -m mypy src
```

Asegúrate de que el repositorio local tiene la identidad correcta:

```powershell
git config user.name "Alberto Urizar"
git config user.email "albertourizar@users.noreply.github.com"
```

> GitHub solo atribuirá los commits a tu cuenta si el correo coincide con uno
> verificado en ella. `usuario@users.noreply.github.com` es la forma clásica; si
> tu cuenta muestra un identificador numérico, usa
> `12345678+albertourizar@users.noreply.github.com` (lo encontrarás en
> **Settings → Emails**).

## 1. Crear el repositorio remoto

### Opción A: GitHub CLI (recomendado)

`gh` no está instalado en este equipo. Instálalo y autentícate:

```powershell
winget install --id GitHub.cli -e
gh auth login
```

Después, desde la raíz del proyecto:

```powershell
gh repo create albertourizar/syskeeper --public --source . --remote origin --push
```

### Opción B: sin instalar nada

1. Entra en <https://github.com/new>.
2. Nombre: `syskeeper`. Visibilidad: pública. **No** marques «Initialize with a
   README» (ya existe uno).
3. Copia la URL y ejecuta:

```powershell
git remote add origin https://github.com/albertourizar/syskeeper.git
git branch -M main
git push -u origin main
```

## 2. Configurar el repositorio

En **Settings**:

- **Description:** `Automatizador de mantenimiento y limpieza para Windows:
  temporales, papelera, caché de navegadores y salud SMART.`
- **Website:** déjalo vacío o enlaza el README.
- **Topics:** `python`, `windows`, `maintenance`, `cleanup`, `smart`, `cli`,
  `powershell`, `sysadmin`.
- **Features:** Issues activado, Discussions opcional, Wiki desactivada.
- **Actions → General:** permite las acciones del repositorio (las workflows ya
  están incluidas).
- **Security → Code security:** activa Dependabot alerts y secret scanning.

## 3. Verificar la CI

Al hacer push se ejecuta `.github/workflows/ci.yml` en `windows-latest` con
Python 3.10, 3.12 y 3.14. El badge del README se actualizará solo:

```
https://github.com/albertourizar/syskeeper/actions/workflows/ci.yml/badge.svg
```

Si falla, revisa el job y reproduce los comandos en local.

## 4. Crear la release 1.0.0

```powershell
git tag -a v1.0.0 -m "syskeeper 1.0.0"
git push origin v1.0.0
```

El flujo `.github/workflows/release.yml` construye la distribución y crea la
release automáticamente. También puedes hacerlo a mano:

```powershell
gh release create v1.0.0 --title "syskeeper 1.0.0" --notes "Primera versión estable: limpieza de temporales, papelera, cachés de navegadores e informes SMART."
```

## 5. Revisión final

- [ ] README renderiza bien y la captura se ve.
- [ ] Badges de CI, licencia, Python y versión en verde.
- [ ] Topics y descripción configurados.
- [ ] Release `v1.0.0` publicada con artefactos `dist/*`.
- [ ] Issues y plantillas de PR visibles.
- [ ] `SECURITY.md` y `CODE_OF_CONDUCT.md` accesibles desde la pestaña
      correspondiente.
- [ ] `git status` limpio y rama `main` sincronizada.

## 6. Mantenimiento posterior

```powershell
git switch -c feat/nueva-funcion
# trabajar, probar y commitear
git push -u origin feat/nueva-funcion
gh pr create --fill
```

Para una nueva versión: actualiza `version` en `pyproject.toml` y
`src/syskeeper/__init__.py`, añade la entrada en `CHANGELOG.md`, crea el tag
`v1.0.1` y publícalo.

## Notas

- No subas `config.json`, `informes/` ni logs: están en `.gitignore`.
- No incluyas rutas personales en capturas ni en el historial del repositorio.
- Si cambias de cuenta de GitHub, actualiza la URL del remoto con
  `git remote set-url origin ...`.
