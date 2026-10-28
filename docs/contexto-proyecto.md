# Mesa de Taller MTG: contexto del proyecto

Resumen del estado actual para alguien (persona o Claude) que **no ve el repositorio**. Actualizado: 2026-10-27.

## Qué es

Herramienta personal de Martín para analizar y optimizar sus mazos de Commander. No reemplaza a Archidekt ni a EDHREC: los complementa con lo que ellos no tienen.
- **Fuente de verdad de los mazos:** Archidekt.
- **Lo que aporta la mesa de taller:**
  - el **objetivo** de cada mazo (su perfil);
  - la **colección física** (exportada de ManaBox);
  - **precios en tiendas mexicanas** (MXN).

"Optimizar" significa llevar el mazo a su mejor versión **dentro de su objetivo** (bracket, tema, ventana de victoria), no maximizar la potencia en abstracto.

**Stack:**
- Python 3.12, `uv`, `typer` (CLI), `httpx`, `pydantic`, SQLite y `pytest`.
- Web: FastAPI + Jinja2 + CSS propio.
- Corre en la Mac de Martín.
- Repositorio privado en GitHub; 99 pruebas pasando.

## Fases

| Fase | Qué | Estado |
| --- | --- | --- |
| 0 | Arranque: repo, `uv`, `pytest` | ✅ |
| 1 | Analizador de mazos y comparación contra mazos ajenos | ✅ 2026-10-25 |
| 2 | Colección (CSV de ManaBox) y "ya la tienes, está en tal caja" | ✅ 2026-10-26 |
| 3 | Precios: referencia, Yellow Rabbit y lista de compra con envío | ✅ 2026-10-26 |
| 4 | Web para Mac e iPhone | En curso |
| 5 | Simulación de partidas (ventana de victoria) y bitácora de partidas en los reportes | Pendiente |

**Fase 4, en detalle:**
1. Esqueleto web ✅
2. Página de mazo diseñada ✅
3. Página de colección (buscar una carta y ver en qué caja está). Pendiente.
4. Acceso desde el iPhone con Tailscale. Pendiente.

**Criterio de terminado de la fase 4:** "accesible con login desde el iPhone".

**Otros pendientes:**
- CardTrader como tercera tienda.
- El perfil de Aang, cuando su lista en Archidekt esté completa.
- Importar más cajas de la colección.

## Cómo se usa

Todo se corre desde la carpeta del proyecto.

| Comando | Qué hace |
| --- | --- |
| `uv run taller analizar <slug>` | Analiza el mazo del perfil y escribe `reports/<slug>-<fecha>.md` (reporte) y `.json` (datos para la web). `--refrescar` vuelve a descargar de Archidekt. |
| `uv run taller comparar <slug> <fuente>` | Compara un mazo propio contra otro. La fuente es una URL de Archidekt o un `.txt` exportado de Moxfield. Escribe `reports/<slug>-vs-<otro>-<fecha>.md`. |
| `uv run taller coleccion importar [archivo.csv]` | Reemplaza la colección completa con un CSV de ManaBox. Sin argumento, toma el más reciente de la carpeta configurada. |
| `uv run taller web [--puerto 8000]` | Levanta el sitio en http://127.0.0.1:8000. Solo en la Mac; nadie más en la red lo ve. |
| `uv run pytest` | Corre las pruebas. |

**Sitio web.** No consulta internet: lee los `.json` que deja `taller analizar`.
- **`/` (portada):** una tarjeta por mazo con bracket, ventana de victoria, fecha del último análisis y aviso si la lista no está confirmada.
- **`/mazos/<slug>`:** la página del mazo, con estas partes:
  - Encabezado con los símbolos de color.
  - Resumen con cifras clave.
  - Roles como barras contra su rango de referencia (se tocan para ver las cartas).
  - Curva de maná en columnas y fuentes por color.
  - Bracket y combos.
  - Sinergia en grupos.
  - Sugerencias en tarjetas.
  - Lista de compra con precios y ligas.
  - Ventana de victoria.

  Si un mazo no tiene `.json`, la página muestra su último reporte Markdown.
- **Diseño:**
  - Pensado primero para celular; en la Mac usa dos columnas.
  - Modo oscuro automático.

**Configuración.** `config.toml` en la raíz; no se versiona y la plantilla es `config.example.toml`. Contiene:
- `[coleccion] carpeta_manabox`: carpeta de exportaciones de ManaBox.
- `[precios] tipo_de_cambio`: 18 por defecto.
- `[tiendas] perfil_ucp`: perfil público para Yellow Rabbit.
- `[envios]`: reglas de envío por tienda.

## Formato del reporte de mazo

El reporte es Markdown y siempre se mide contra el perfil. Encabezado:
- fecha, comandante, bracket y ventana objetivo, tema;
- liga a Archidekt con su fecha de edición;
- colección usada;
- avisos, si los hay: lista no confirmada contra el mazo físico, lista que no suma 100 cartas, o cartas no encontradas en Scryfall.

Después vienen 8 secciones:
1. Resumen
2. Roles
3. Curva y base de maná
4. Bracket
5. Combos
6. Sinergia con el tema
7. Sugerencias, que incluye la lista de compra
8. Ventana de victoria

**Ejemplo recortado** (Tokens, Isshin, 2026-10-27):

```markdown
# Tokens — análisis

- **Comandante:** Isshin, Two Heavens as One
- **Bracket objetivo:** 3
- **Ventana de victoria objetivo:** turno 5
- **Colección:** 45 cartas (ManaBox_Collection.csv, importada 2026-10-26)

## 1. Resumen
- **Por debajo de la referencia:** robo (7 de 10–12); wipes (1 de 2–4).
- **Maná:** 34 tierras, costo promedio 3.0, 11 piezas de ramp.
- **Para ganar en turno 5, el cuello de botella es el robo.**

## 2. Roles
| Rol | Cartas | Referencia | Estado |
| --- | --- | --- | --- |
| Ramp | 11 | 10–12 | ✅ |
| Robo | 7 | 10–12 | ⬇️ abajo |
| Removal | 11 | 8–10 | ⬆️ arriba |

## 7. Sugerencias
- **Sube robo** (7, referencia 10–12). En tu Maybeboard: Mentor of the Meek · Welcoming Vampire.
  - En tu colección: Frodo, Adventurous Hobbit (la tienes: Orzhov WB)
- **Evita agregar** si quieres quedarte en bracket 3 (completarían un combo de dos cartas): Helm of the Host · …

### Lista de compra
| Carta | Para | Referencia | Yellow Rabbit | Buscar |
| --- | --- | --- | --- | --- |
| Mentor of the Meek | robo | $85 (4.72 USD) | $15 NM · Innistrad Remastered | Yellow Rabbit · TCG Wolf |
| Teferi's Protection | Game Changer | $844 (46.87 USD) | $805 NM · Marvel Universe | Yellow Rabbit · TCG Wolf |
```

**Cómo se calcula cada sección:**
- **Roles:** etiquetas de Scryfall Tagger que trae Archidekt. Si una carta no tiene etiquetas, se usan reglas sobre su texto. Los roles son ramp, robo, removal, wipes, protección, tokens y cierre.
- **Rangos de referencia** (el perfil puede cambiarlos):
  - ramp 10–12
  - robo 10–12
  - removal 8–10
  - wipes 2–4
  - protección 3–6
- **Bracket:** se señalan Game Changers (máximo 3 en bracket 3), tutores, turnos extra, destrucción masiva de tierras y combos de dos cartas.
- **Combos:** vienen de Commander Spellbook.
- **Sugerencias:** primero el Maybeboard del mazo, luego la colección, después lo más barato.

## Perfiles de mazo

Hay un YAML por mazo en `decks/profiles/`. Hoy existen dos; los demás mazos de Martín (Aang, Tannuk, Azami, Simone y tres en construcción) todavía no tienen perfil.

| Campo | `tokens-isshin` | `dragones-ureni` |
| --- | --- | --- |
| nombre | Tokens | DragonSSSS! |
| comandante | Isshin, Two Heavens as One (Mardu) | Ureni of the Unwritten (Temur) |
| archidekt_id | 26390360 | 21296260 |
| bracket | 3 | 4 |
| estado | armado | armado |
| lista_sincronizada | true (2026-10-25) | true (2026-10-25) |
| tema | Mardu de ataques y tokens; Isshin duplica los disparos de ataque | Dragones Temur; rampear y poner dragones grandes sin pagar su costo |
| plan_de_victoria | Tokens al atacar, multiplicados por Isshin; cierre con anthems o daño al entrar (Impact Tremors, Purphoros) | Ramp o trampas (Sneak Attack, See the Unwritten, Tooth and Nail, Birthing Pod) para sacar dragones temprano; cierre con daño al entrar |
| ventana_victoria | turno 5 | turno 4-5 |
| restricciones | Mantenerse en bracket 3; consistencia sobre picos de potencia | Ganar en turno 4-5 de forma consistente |
| tipos_tema | — | Dragon |
| etiquetas_tema | attack trigger | typal-dragon, sneak-creature, tutor-to-battlefield, impulse-onto-battlefield, trigger doubler |
| referencias | (generales) | ramp 16–20 |
| notas | Bracket 3 muy constante, con ventana casi competitiva | — |

**Resultado actual (2026-10-27):**
- **Isshin:**
  - Por debajo de la referencia: robo (7) y wipes (1); removal está arriba (11).
  - 34 tierras, costo promedio 3.0.
  - Lista de compra: referencia $976; Yellow Rabbit $820 (2 cartas sin stock).
- **Ureni:**
  - Por debajo de la referencia: robo (9), wipes (0) y protección (0).
  - 35 tierras, costo promedio 3.92, 20 de ramp, 7 combos presentes.
  - Sin lista de compra: su Maybeboard no cubre lo que falta.

## Importación de ManaBox

1. Martín escanea cartas en ManaBox. Cada **binder** es una caja física (por color o combinación, por ejemplo "Orzhov WB"), así que el nombre del binder es la ubicación de la carta.
2. ManaBox exporta un CSV a `~/Documents/MTG Archive`, que se sincroniza por iCloud. Esa carpeta es de **solo lectura** para el proyecto: nunca se escribe, mueve ni borra nada ahí.
3. `taller coleccion importar` lee el CSV más reciente (por fecha de modificación) y busca el `oracle_id` de cada carta en Scryfall. Luego **reemplaza toda la colección** en SQLite, en una sola transacción: si algo falla, queda la anterior. Al terminar imprime cuántas cartas hay por binder y cuáles no encontró.
4. Los binders de tipo `list` de ManaBox se toman como listas de deseos y no cuentan como cartas que se tienen.
5. Con la colección cargada, los reportes:
   - marcan "la tienes: \<caja\>" en las sugerencias;
   - buscan en la colección cartas que encajen en la identidad de color y cubran roles que faltan;
   - sacan de la lista de compra lo que ya se tiene.

**Colección actual:** 45 cartas en 3 binders, importada el 2026-10-26.

| Binder | Cartas |
| --- | --- |
| Dimir | 23 |
| Orzhov WB | 21 |
| Golgari - GB | 1 |

Columnas del CSV que se usan: Binder Name, Binder Type, Name, Set code, Collector number, Foil, Quantity, Scryfall ID, Language.

## Precios

- **Referencia:** precio USD de Scryfall (TCGplayer), convertido a MXN con el tipo de cambio de `config.toml`.
- **Yellow Rabbit:**
  - Precios automáticos por su canal oficial para agentes (UCP, `search_catalog`).
  - Nos identificamos con un perfil público: un gist servido por githack, fijado a una versión.
  - Se toma la copia más barata en stock, en condición NM o LP.
  - Caché diaria.
  - Sin envío, porque Martín recoge en sucursal.
- **TCG Wolf:**
  - Solo ligas de búsqueda: tiene reto de Cloudflare y `robots.txt` prohíbe `/api/`.
  - Envío promedio $150, gratis desde $2,200.
- **Reglas fijas:** no evadir Cloudflare, no usar sesiones ni cookies, guardar caché con fecha e identificarse con un User-Agent propio.

## Limitaciones conocidas

- **Web:**
  - Solo existe en la Mac (127.0.0.1).
  - No hay login ni acceso desde el iPhone todavía.
  - No hay página de colección.
  - Los datos se actualizan solo cuando se corre `taller analizar`.
- **Ventana de victoria:** es una heurística (cartas baratas, ramp, costo promedio), no una simulación. Eso llega en la fase 5.
- **EDHREC:** no está integrado. Las sugerencias salen solo del Maybeboard y de la colección, no de promedios de EDHREC.
- **Roles:**
  - Dependen de las etiquetas de Tagger. Las cartas de la colección no las tienen, así que sus roles se detectan por texto; el reporte pide revisarlos.
  - "Sin rol detectado" puede incluir cartas útiles para el tema que las etiquetas no cubren.
- **Precio de referencia:**
  - Es de una sola impresión.
  - Cerca del 11 % de las cartas no tiene precio USD.
  - Puede diferir mucho del de tienda: Mentor of the Meek tiene referencia de $85 y está en $15 en tienda.
- **Precios de tienda:** solo Yellow Rabbit es automático. CardTrader está pendiente.
- **Colección:** pequeña (45 cartas en 3 cajas); aún no hay cartas Temur, así que Ureni no recibe sugerencias de la colección.
- **Perfiles y listas:**
  - Solo dos mazos tienen perfil.
  - La lista de Aang en Archidekt está incompleta (3 cartas).
  - Las listas no confirmadas contra el mazo físico se analizan con aviso.
- **Mazos ajenos:**
  - Moxfield no se consulta directo (Cloudflare); se pega su texto exportado.
  - La bitácora de partidas (`notes/bitacora/`) todavía no se usa en los reportes.
- **Perfil UCP:** si se edita el gist, hay que actualizar la versión fijada en `perfil_ucp`.
