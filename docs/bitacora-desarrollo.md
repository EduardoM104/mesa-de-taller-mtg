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

## 2026-10-25 — Fase 1: analizador de mazos (pasos 1 a 7, Isshin)

### Qué se hizo

1. **Perfiles** (`profiles.py`): modelo `DeckProfile` con pydantic y `load_profile()`. Perfil de Tokens (Isshin) con ventana en turno 5, bracket 3 constante. Martín escribió su primera prueba (`test_invalid_estado_raises`).
2. **Archidekt** (`sources/archidekt.py`, `sources/cache.py`): trae el mazo, lo separa en comandante, mazo y Maybeboard según `includedInDeck`, y guarda cada respuesta en `data/cache/` con fecha.
3. **Scryfall** (`sources/scryfall.py`, `db.py`): bulk diario "Oracle Cards" (`.jsonl.gz`) cargado en la tabla `cards` de `data/taller.db`.
4. **Análisis** (`analysis/roles.py`, `mana.py`, `bracket.py`): roles con etiquetas de Scryfall Tagger (respaldo: reglas de texto), curva, fuentes por color, tierras giradas, Game Changers, tutores, turnos extra y destrucción masiva de tierras.
5. **Combos** (`sources/spellbook.py`): combos presentes y a una carta desde Commander Spellbook, con caché por huella (hash) de la lista.
6. **Reporte y CLI** (`analysis/analyze.py`, `report.py`, `cli.py`): `uv run taller analizar tokens-isshin` escribe el reporte con las 8 secciones. Nuevo campo de perfil `etiquetas_tema`.
7. **Comparar** (`sources/decklist.py`, `analysis/compare.py`, `compare_report.py`): `uv run taller comparar tokens-isshin <URL o .txt>` contra un mazo ajeno (URL de Archidekt o texto de Moxfield).

45 pruebas pasando.

### Qué dice el análisis de Tokens (Isshin)

- Bracket 3 limpio: 0 Game Changers, sin tutores, sin combos presentes.
- Cuello de botella para ganar en turno 5: robo (7 de 10–12). Candidatas en el Maybeboard: Caesar, Mentor of the Meek, Welcoming Vampire.
- Quedan 3 espacios de Game Changer (Teferi's Protection está en el Maybeboard).
- Removal con margen (11); wipes bajo (1).
- Evitar cartas que completan combos de dos cartas (Helm of the Host, etc.): en bracket 3 no deben armarse antes del turno 6.

### Qué aprendimos

- Un modelo de pydantic valida los datos al leerlos: los errores salen pronto y claros.
- Dos funciones con el mismo nombre: la segunda reemplaza a la primera sin avisar.
- La "prueba contraria" (romper a propósito) confirma que una prueba de verdad detecta algo.
- Separar "traer los datos" de "entender los datos" permite probar casi todo sin internet (fixtures).
- List comprehensions, transacciones de SQLite (`with connection:`), placeholders `?` en SQL y hashes como huella.
- Probar con datos reales encuentra errores que ninguna prueba previa imaginaba (la carta "Isshin // Isshin" de Scryfall).

### Qué sigue

- Martín: revisar la lista de Tokens contra el mazo físico y, si coincide, poner `lista_sincronizada: true`.
- Martín: subir la lista completa de Aang a Archidekt (hoy tiene 3 cartas). Con eso se crea su perfil y se cierra la Fase 1.
- Opcional: comparar contra una lista de Isshin de bracket 3 (la usada de prueba tiene 16 Game Changers).
