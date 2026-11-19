## Descripción

<!-- Explica qué cambia este pull request y por qué. -->

## Issue relacionado

Closes #

## Tipo de cambio

- [ ] Corrección de error (`fix`)
- [ ] Nueva función (`feat`)
- [ ] Documentación (`docs`)
- [ ] Pruebas (`test`)
- [ ] Integración continua (`ci`)
- [ ] Refactorización (`refactor`)

## Cómo se ha probado

<!-- Comandos ejecutados y resultado. -->

```powershell
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
```

## Checklist

- [ ] El cambio respeta la simulación por defecto y las rutas protegidas.
- [ ] He añadido o actualizado pruebas.
- [ ] La cobertura sigue por encima del 80 %.
- [ ] He actualizado `CHANGELOG.md` si afecta al usuario.
- [ ] La documentación (README/`docs/`) está al día.
- [ ] No incluyo datos personales, rutas privadas ni secretos.
- [ ] La CI está en verde.
