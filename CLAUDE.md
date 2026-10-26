# Mesa de Taller MTG

Brief del proyecto para Claude Code (y cualquier otro agente que trabaje en este repo, como Gemini en Antigravity). Léelo completo antes de proponer o escribir código.

## Contexto

- Dueño: Martín, jugador de Commander casual en CDMX. También tiene un proyecto competitivo aparte (Standard en Arena en 2026, papel en 2027).
- Tiene suscripción de pago en EDHREC y Archidekt.
- Colección física de varios miles de cartas: unas dos cajas tipo bundle por color, más cuatro cajas de multicolor, incoloras y tierras no básicas.
- 6 mazos de Commander armados y 3 en construcción (lobos, zombies, criaturas marinas con Runo Stormkirk).
- Usa una Mac en casa. Quiere consultar desde iPhone, iPad y su Mac del trabajo (web).

## Mazos en Archidekt

- Usuario: `MartRod104`. Carpeta principal: https://archidekt.com/folders/42445 (16 mazos, más una subcarpeta "Archivados").
- **Ojo:** no todas las listas de Archidekt coinciden con el mazo físico. Cada perfil indica si la lista está sincronizada con lo físico; si no lo está, los reportes deben avisarlo y no tratarla como verdad.

| Mazo | Comandante | Bracket | Archidekt | Estado |
| --- | --- | --- | --- | --- |
| Tokens | Isshin, Two Heavens as One | 3 | 26390360 | Armado |
| Avastar State | Aang, at the Crossroads | 4 (estimado) | 25803340 | Armado; en Archidekt solo hay 3 cartas |
| DragonSSSS! | Ureni of the Unwritten | 4 (estimado) | 21296260 | Armado |
| Full speed ahead! | Tannuk, Steadfast Second | 4 teórico, 3 realista | 20926846 | Armado |
| Tides of Control | Azami (mono azul) | 3 (estimado) | 25803291 | Armado |
| Counters Counters | Simone, Infinite Analyst | 3 (estimado) | 26352747 | Armado |
| Lobos! | Por confirmar | Por definir | 11708251 | En construcción; lista en revisión |
| Grave Danger | Por confirmar | 3 | 17028221 | En construcción; lista en revisión; evaluando pasarlo a mono negro |
| Monstruos | Por confirmar | Por definir | Sin lista | En construcción |

El resto de mazos de la carpeta se consideran archivados o teóricos hasta que Martín diga lo contrario.

Martín revisa las listas una por una contra el mazo físico. Confirmadas: Tokens y DragonSSSS! (2026-10-25). Las demás llevan `lista_sincronizada: false` hasta que él las confirme.

## Repositorio

https://github.com/EduardoM104/mesa-de-taller-mtg (privado).

## Visión

Una "mesa de taller" personal que **complementa** a EDHREC y Archidekt, no los reemplaza:

- **Archidekt** es la fuente de verdad de los mazos. Ahí se construyen y editan.
- **EDHREC, Scryfall y Commander Spellbook** son fuentes de datos.
- **La mesa de taller** aporta lo que ellos no tienen: los objetivos de cada mazo, la colección física, precios en tiendas mexicanas y la bitácora de lo que pasa en las partidas.

## Qué significa "optimizar"

Llevar cada mazo a su mejor versión **dentro de su objetivo, temática y limitantes**. No es maximizar potencia en abstracto.

- Ejemplo 1: un mazo de zombies para Halloween, bracket 3, centrado en tokens 2/2. Optimizar es evaluar qué cartas hacen sinergia con el plan, si el robo y la base de maná son correctos, qué cartas sobran, qué opciones lo mejoran o lo empeoran, y cuál es su ventana de victoria realista en bracket 3.
- Ejemplo 2: Aang, at the Crossroads, blink, bracket 4. Optimizar es volverlo consistente para ganar en turno 3–4.

Por eso cada mazo tiene un **perfil** (ver abajo) y todo análisis se mide contra ese perfil.

## Modo aprendizaje (importante)

Martín está aprendiendo a programar y sabe cosas básicas. Quiere dar seguimiento al código.

- Antes de cada cambio grande, explica en español qué vas a hacer y por qué, en pocas líneas.
- Prefiere código simple y legible sobre código ingenioso. Funciones cortas.
- Nombres de variables y funciones en inglés; comentarios y documentación en español.
- Cuando haya una pieza pequeña y bien acotada (una función, un test), ofrécele escribirla él y revísala después.
- Al terminar una sesión, deja un resumen en `docs/bitacora-desarrollo.md`: qué se hizo, qué aprendió, qué sigue.

## Stack

- Python 3.12 con `uv` para dependencias y entornos.
- SQLite como base de datos local (`data/taller.db`).
- `httpx` para HTTP, `pydantic` para modelos, `pytest` para pruebas, `typer` para la línea de comandos.
- Web (fase 4): por decidir entre Streamlit y Next.js, y el hosting. No adelantar esta decisión.

## Estructura

```
mesa-de-taller-mtg/
├── CLAUDE.md
├── config.toml            # rutas locales, ej. carpeta de ManaBox (no se versiona; plantilla: config.example.toml)
├── decks/profiles/        # un YAML por mazo (perfil y objetivos)
├── notes/bitacora/        # un .md por mazo con observaciones de partidas
├── data/
│   ├── cache/             # respuestas de APIs con fecha (no se versiona)
│   ├── imports/           # CSV de ManaBox, Archidekt, etc. (no se versiona)
│   └── taller.db          # (no se versiona)
├── reports/               # reportes generados en Markdown
├── src/taller/
│   ├── sources/           # un módulo por fuente: scryfall, archidekt, spellbook, edhrec, tiendas
│   ├── collection/        # importación y consulta de la colección
│   ├── analysis/          # roles, curva, base de maná, bracket, combos, sinergia
│   ├── prices/            # precios y conversión a MXN
│   └── cli.py
├── tests/
└── docs/
```

## Fuentes de datos y reglas de uso

| Fuente | Uso | Cómo |
| --- | --- | --- |
| Scryfall | Datos de cartas, precios de referencia en USD | Bulk data diario, no consultar carta por carta |
| Archidekt | Mazos de Martín | Endpoint público `https://archidekt.com/api/decks/{id}/`; las cartas traen `categories` (ahí se distingue Maybeboard) |
| Moxfield | Mazos que comparten otros jugadores (Martín tiene cuenta gratuita) | Su API está protegida por Cloudflare y no se debe evadir. Vía principal: pegar el texto de exportación del mazo. Vía de conveniencia: el endpoint público de Commander Spellbook que acepta una URL de Moxfield |
| Commander Spellbook | Combos presentes o a una carta de distancia | API pública |
| EDHREC | Promedios, sinergia, inclusión | No tiene API oficial; usar el JSON público de las páginas con caché de 24 h y pocas peticiones |
| ManaBox (CSV) | Colección física escaneada | `taller coleccion importar` toma el CSV más reciente de la carpeta de `config.toml` y reemplaza la colección. Esa carpeta es de solo lectura: nunca escribir, mover ni borrar ahí |
| Tiendas | Precios para comprar | Ver sección de precios |

Reglas generales:

- Cachear todo con fecha. Nunca golpear una fuente repetidamente.
- Identificarse con un User-Agent propio y espaciar peticiones.
- No iniciar sesión ni usar cookies de cuentas para extraer datos.
- Si una fuente cambia o falla, el resto del sistema debe seguir funcionando.

## Perfil de mazo

Un archivo por mazo en `decks/profiles/<slug>.yaml`:

```yaml
slug: zombies-halloween
archidekt_id: 0000000
nombre: Zombies de Halloween
comandante: ""
bracket: 3                 # bracket objetivo
bracket_teorico: null      # si difiere del realista (ej. Tannuk: 4 teórico, 3 realista)
estado: en_construccion    # armado | en_construccion | archivado
lista_sincronizada: false  # ¿la lista de Archidekt es igual al mazo físico?
tema: Zombies con tokens 2/2
plan_de_victoria: Ensanchar la mesa con tokens y cerrar con anthems y drenaje
ventana_victoria: "turno 7-9"
restricciones:
  - Mantener la temática zombie aunque cueste algo de potencia
  - Sin Game Changers
tipos_tema:                # tipos de criatura del tema
  - Zombie
etiquetas_tema:            # etiquetas de Scryfall Tagger que marcan las piezas del tema
  - repeatable creature tokens
referencias:               # opcional: rangos propios por rol (ramp, robo, removal, wipes, protección)
  ramp: [10, 12]
presupuesto_mxn: null
notas: ""
```

Para un mazo de bracket 4 como Aang, `ventana_victoria` sería `"turno 3-4"` y el análisis debe centrarse en consistencia.

## Qué produce el análisis de un mazo

Un reporte en Markdown en `reports/` que siempre compara contra el perfil:

1. **Resumen**: qué tan bien cumple su objetivo, en 3–5 líneas.
2. **Roles**: ramp, robo, removal, wipes, protección, condiciones de victoria y piezas del tema, con conteos y comparación contra referencias habituales del formato.
3. **Curva y base de maná**: tierras, fuentes por color, tierras que entran giradas.
4. **Bracket**: Game Changers, combos de dos cartas, destrucción masiva de tierras, turnos extra, tutores. Señalar si algo rompe el bracket objetivo.
5. **Combos**: presentes y a una carta de distancia (Spellbook).
6. **Sinergia con el tema**: qué cartas empujan el plan y cuáles no.
7. **Sugerencias**: entradas y salidas, priorizando cartas que Martín ya tiene en su colección, y luego las más baratas.
8. **Ventana de victoria**: estimación del turno en que el mazo suele ganar sin interacción (en fases posteriores, por simulación).

## Colección

- Una sola colección compartida entre Commander y el proyecto competitivo.
- Cada carta registra ubicación (caja o mazo) para saber si está libre o asignada.
- Escaneo con ManaBox y exportación a CSV. La organización digital replica la física: un binder por color, uno por cada combinación de colores (ej. "Orzhov", "Golgari"), uno de tierras, uno de artefactos incoloros y uno de incoloros. El nombre del binder es la ubicación de la carta.
- También se puede subir a la colección de Archidekt para que sus herramientas la vean.

## Precios

- Moneda de trabajo: MXN. Referencias en USD de Star City Games, TCGplayer y Card Kingdom, convertidas con un tipo de cambio configurable (por defecto 18).
- Cada tienda mexicana aplica su propia regla de conversión, así que se guarda el precio en MXN tal como la tienda lo publica.
- Tiendas mexicanas a integrar: Yellow Rabbit, TCG Wolf (antes MTG Wolf). Candidatas a evaluar: CardTrader (tiene API y consolida envíos), TCGmercado y otras que resulten confiables.
- Comparar siempre el costo total con envío, no solo el precio unitario.
- Objetivo: completar la colección para tener muchas opciones de juego al mejor precio. No interesa la versión más cara ni la reventa.
- Extra: lista de seguimiento para detectar cartas por debajo de su precio habitual o con riesgo de subir.

## Fases

Cada fase termina cuando cumple su criterio de terminado. No empezar la siguiente sin cerrar la anterior.

- **Fase 0. Arranque.** Repo en GitHub (privado), `uv`, estructura de carpetas, `pytest` corriendo. *Terminado:* `uv run pytest` pasa con una prueba de ejemplo.
- **Fase 1. Analizador de mazos.** Comando `taller analizar <slug>` que lee el perfil, trae el mazo de Archidekt, cruza con Scryfall y Spellbook, y escribe el reporte. También acepta un mazo ajeno (texto exportado de Moxfield o URL de Archidekt) para compararlo contra uno propio. *Terminado:* reportes útiles para el mazo de tokens (Isshin) y para DragonSSSS! (Ureni). Aang se cambió por Ureni porque su lista en Archidekt está incompleta (decisión de Martín, 2026-10-25).
- **Fase 2. Colección.** Importar CSV de ManaBox por caja; las sugerencias marcan "ya la tienes, está en tal caja". *Terminado:* al menos una caja importada y visible en un reporte. ✅ 2026-10-26 (Orzhov WB en el reporte de Isshin).
- **Fase 3. Precios.** Precios de referencia y de tiendas mexicanas, lista de compra al mejor costo total. *Terminado:* lista de compra en MXN para las sugerencias de un mazo.
- **Fase 4. Web.** Consulta de reportes, colección y lista de compra desde iPhone, iPad y la Mac del trabajo. *Terminado:* accesible con login desde el iPhone.
- **Fase 5. Simulación y bitácora.** Simulación de partidas en solitario para estimar la ventana de victoria (prioridad: Aang en turno 3–4) e integración de la bitácora de partidas en los reportes.

## Bitácora de partidas

Martín no quiere registrar cada partida. Cuando comente algo que vio en una partida, se agrega como entrada fechada en `notes/bitacora/<slug>.md` y se toma en cuenta en los siguientes análisis de ese mazo.
