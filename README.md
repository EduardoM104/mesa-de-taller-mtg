# Mesa de Taller MTG

Mesa de taller personal para analizar y optimizar mazos de Commander. Complementa a Archidekt y EDHREC con los objetivos de cada mazo, la colección física, precios en tiendas mexicanas y la bitácora de partidas.

El brief completo del proyecto está en [CLAUDE.md](CLAUDE.md).

## Instalación

Requiere [uv](https://docs.astral.sh/uv/). Desde la carpeta del proyecto:

```sh
uv sync
```

Esto crea el entorno `.venv/` con Python 3.12 y todas las dependencias.

## Pruebas

```sh
uv run pytest
```
