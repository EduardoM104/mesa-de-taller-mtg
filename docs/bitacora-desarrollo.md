# Bitácora de desarrollo

## 2026-10-23 — Fase 0: Arranque

### Qué se hizo

- Proyecto inicializado con `uv init --package` (paquete `taller`, Python 3.12).
- Estructura de carpetas según CLAUDE.md, con subpaquetes `sources`, `collection`, `analysis` y `prices`.
- `.gitignore` para no subir `data/`, `.venv/` ni archivos temporales.
- pytest como dependencia de desarrollo y una prueba de ejemplo en `tests/test_ejemplo.py`.
- `uv run pytest` pasa (2 pruebas). Primer commit subido a GitHub.

### Qué aprendimos

- `pyproject.toml` es la ficha del proyecto; `uv.lock` fija versiones exactas para instalar igual en cualquier máquina.
- `uv add --dev` agrega dependencias que solo se usan para desarrollar (como pytest).
- `uv run <comando>` ejecuta dentro del entorno del proyecto sin activarlo.
- Git no guarda carpetas vacías: por eso los archivos `.gitkeep`.
- Un `__init__.py` convierte una carpeta en paquete de Python.
- pytest encuentra solo los archivos y funciones que empiezan con `test_`.

### Qué sigue

- Fase 1: analizador de mazos. Primer paso sugerido: el perfil YAML de Isshin y el módulo de Archidekt para traer la lista.
