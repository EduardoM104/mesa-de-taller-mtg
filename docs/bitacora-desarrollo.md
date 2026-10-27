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

- Ver la entrada siguiente: la Fase 1 se cerró el mismo día con Ureni en lugar de Aang.

## 2026-10-25 — Fase 1 cerrada: Ureni y ajustes

### Qué se hizo

- **Tokens confirmada:** la lista de Archidekt coincide con el mazo físico (`lista_sincronizada: true`).
- **`--refrescar`:** `taller analizar` y `taller comparar` pueden ignorar la copia de hoy de Archidekt, para analizar un mazo editado el mismo día.
- **Ureni en lugar de Aang:** la lista de Aang sigue incompleta en Archidekt, así que Martín eligió DragonSSSS! (Ureni, bracket 4, ganar en turno 4-5, lista confirmada). El criterio de la Fase 1 en CLAUDE.md se actualizó.
- **Clasificación más fina**, descubierta al analizar un mazo muy distinto a Isshin:
  - `land ramp` cuenta como ramp; las etiquetas `tutor-land...` y `tutor-to-...` ya no cuentan como tutor (fetchlands, Cultivate, Kodama's Reach).
  - Los counterspells (`counterspell-soft`, etc.) cuentan como interacción en removal.
  - Los tutores ya no salen como "candidatas a salir".
- **Campos nuevos del perfil:** `tipos_tema` (ej. `Dragon`, para que los dragones mismos sean piezas del tema) y `referencias` (rangos propios por rol; Ureni usa `ramp: [16, 20]`).
- El resumen cuenta piezas del tema y menciona los combos presentes en bracket 4.

54 pruebas pasando. Isshin no cambió con los ajustes (se comparó el reporte antes y después).

### Qué dice el análisis de DragonSSSS! (Ureni)

- Ramp 20 (dentro de su rango propio 16-20), robo 9 de 10-12, sin wipes ni protección.
- 9 tutores y 2 Game Changers (Worldly Tutor, Gamble): sin problema en bracket 4.
- 7 combos de dos cartas presentes (ej. Niv-Mizzet Parun + Visionary): ruta de victoria alterna.
- 39 piezas del tema; solo 3 cartas sin rol (Reflections of Littjara, Nature's Will, Monstrous Vortex).

### Qué aprendimos

- Un segundo mazo muy distinto encuentra huecos que el primero no mostraba: probar con variedad.
- Antes de cambiar reglas compartidas, comparar el resultado del mazo anterior para confirmar que no se rompió.
- Las referencias generales sirven de punto de partida, pero el perfil de cada mazo puede justificar otras.

### Qué sigue

- **Fase 2: colección.** Importar un CSV de ManaBox por caja y que las sugerencias digan "ya la tienes, está en tal caja".
- Pendiente cuando haya lista: perfil y reporte de Aang.

## 2026-10-26 — Fase 2: colección

### Qué se hizo

- **`config.toml`** (no se versiona; plantilla en `config.example.toml`): guarda la carpeta de exportaciones de ManaBox, `/Users/martrod104/Documents/MTG Archive`. La ruta vive en configuración, no en el código.
- **`taller coleccion importar`:** sin argumentos toma el CSV más reciente de esa carpeta y reemplaza la colección completa en una sola transacción. La carpeta es de solo lectura para el taller: solo se lista y se abre en modo lectura (hay una prueba que lo revisa).
- Cada carta se guarda con su `oracle_id` (buscado por nombre en Scryfall) para cruzarla con los mazos. Los binders de tipo `list` (listas de deseos en ManaBox) no cuentan como cartas que tienes.
- **Reportes:** el encabezado dice qué colección se usó; en Sugerencias, el Maybeboard y las cartas de la colección que cubren un rol bajo dicen dónde están ("la tienes: Orzhov WB"). La comparación marca las cartas ajenas que ya tienes.
- Primera importación: 22 cartas (Orzhov WB y Golgari - GB). En el reporte de Isshin aparece Frodo, Adventurous Hobbit (Orzhov WB) como opción de robo.

69 pruebas pasando.

### Qué aprendimos

- Separar configuración (rutas de esta Mac) del código: `tomllib` viene con Python y lee TOML sin instalar nada.
- `pathlib.Path` maneja rutas con espacios sin problema mientras no pasen por la terminal.
- "Reemplazar todo" con `DELETE` + inserciones dentro de `with connection:` es todo o nada: si algo falla, queda la colección anterior.
- Las cartas de la colección no traen etiquetas de Tagger: sus roles salen del texto y son aproximados, así que el reporte lo dice.

### Qué sigue

- Escanear más cajas en ManaBox y reimportar; con más colores habrá sugerencias para Ureni (hoy no hay cartas Temur en la colección).
- **Fase 3: precios.**

### Más tarde el mismo día

- Martín actualizó el CSV con el binder **Dimir** (23 cartas). Colección: 45 cartas en 39 filas, todas encontradas en Scryfall. Ningún mazo con perfil es azul-negro, así que los reportes de Isshin y Ureni no cambian.
- Prueba nueva: `latest_csv` ignora archivos que no son `.csv`. Se comprobó que falla si se quita el filtro: una prueba que no falla al romper lo que vigila no vigila nada.
- Al leer el CSV, macOS puede descargarlo de iCloud y marcar su "último uso"; el contenido, el nombre y la fecha de modificación no cambian.

70 pruebas pasando.

## 2026-10-26 — Fase 3: precios

### Qué se hizo

- **Lista de compra** en la sección 7 del reporte: las sugerencias del Maybeboard que no están en la colección, de la más barata a la más cara.
  - **Referencia:** precio de Scryfall (TCGplayer, USD) convertido con el tipo de cambio de `config.toml` (18 por defecto).
  - **Yellow Rabbit:** la copia más barata en stock (NM o LP) de esa carta exacta, por su canal oficial para agentes (UCP). Caché diaria y una pausa entre consultas.
  - **Ligas de búsqueda** a Yellow Rabbit y TCG Wolf por carta.
  - **Costo total con envío** por tienda, con las reglas de `[envios]` en `config.toml`: Yellow Rabbit sin envío (recoger en sucursal); TCG Wolf $150, gratis desde $2,200 (estimado con la referencia, porque no tiene precios automáticos).
- **Perfil público UCP:** Martín publicó el gist `mesa-de-taller-ucp.json`. La dirección normal del gist entrega texto plano y la tienda lo rechazó; servido por githack (como JSON) sí lo aceptó. Después hubo que declarar los permisos de búsqueda de catálogo para que la tienda ofreciera la herramienta.
- **TCG Wolf** no se automatiza: reto de Cloudflare en sus páginas y `/api/` prohibido en `robots.txt` (misma regla que Moxfield).
- Resultado en Isshin: referencia $976; Yellow Rabbit $830 (Mentor of the Meek $15, Teferi's Protection $815; 2 sin stock); TCG Wolf estimado $1,126 con envío.

89 pruebas pasando.

### Qué aprendimos

- Antes de automatizar una tienda, leer su `robots.txt` y su guía para agentes: dicen qué se permite y por qué canal.
- Los precios de referencia y los de tienda pueden ser muy distintos (Mentor of the Meek: $85 de referencia, $15 en tienda), porque la referencia es de una impresión específica.
- Revisar los resultados reales encontró dos errores que las pruebas no veían: nombres alternos ("T'Challa's Protection - Teferi's Protection") y búsquedas que traían cartas parecidas (se arregló buscando entre comillas).
- Una caché debe guardar solo respuestas buenas; un error guardado duraría todo el día.

### Qué sigue

- Si se edita el gist, actualizar la versión en `perfil_ucp` de `config.toml` (githack guarda copia de la versión anterior).
- Candidata: CardTrader (API oficial con token de la cuenta de Martín).
- **Fase 4: web.** Antes de arrancar hay que decidir entre Streamlit y Next.js, y el hosting.
