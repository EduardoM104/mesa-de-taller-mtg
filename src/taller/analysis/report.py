"""Convierte un DeckAnalysis en el reporte Markdown, siempre contra el perfil.

Cada sección es una función que devuelve una lista de líneas; render()
las junta en el orden que pide CLAUDE.md.
"""

from datetime import date

from taller.analysis.analyze import DeckAnalysis, target_turn
from taller.analysis.bracket import MAX_GAME_CHANGERS
from taller.analysis.collection import with_location
from taller.analysis.pairing import is_land
from taller.analysis.roles import group_by_role
from taller.prices.shopping import shopping_list, total_usd, usd_to_mxn
from taller.prices.stores import search_links

ROLE_TITLES = {
    "ramp": "Ramp",
    "robo": "Robo",
    "removal": "Removal",
    "wipes": "Wipes",
    "protección": "Protección",
    "tokens": "Tokens",
    "cierre": "Cierre",
}
COLOR_NAMES = {"W": "Blanco", "U": "Azul", "B": "Negro", "R": "Rojo", "G": "Verde"}
# Cuántos combos "a una carta" mostrar, de los más populares a los menos.
MAX_NEAR_COMBOS = 10


def render(analysis: DeckAnalysis) -> str:
    """Arma el reporte completo."""
    sections = [
        header(analysis),
        summary(analysis),
        roles_section(analysis),
        mana_section(analysis),
        bracket_section(analysis),
        combos_section(analysis),
        synergy_section(analysis),
        suggestions_section(analysis),
        window_section(analysis),
    ]
    return "\n\n".join("\n".join(lines) for lines in sections) + "\n"


# ---------- Ayudantes ----------


def names(card_names: list[str]) -> str:
    """Lista de nombres separada por " · ", o un guion si está vacía.

    No se usan comas porque muchas cartas las llevan en el nombre
    (ej. "Krenko, Tin Street Kingpin").
    """
    return " · ".join(card_names) if card_names else "—"


def roles_below(analysis: DeckAnalysis) -> list[str]:
    """Roles con menos cartas que el mínimo de referencia."""
    return [role for role, (low, _) in analysis.references.items() if len(analysis.roles[role]) < low]


def format_range(reference: tuple[int, int] | None) -> str:
    """(10, 12) → "10–12"; sin referencia → "—"."""
    return f"{reference[0]}–{reference[1]}" if reference else "—"


def role_status(count: int, reference: tuple[int, int] | None) -> str:
    """✅ dentro del rango, ⬇️ abajo, ⬆️ arriba, — si no hay referencia."""
    if reference is None:
        return "—"
    low, high = reference
    if count < low:
        return "⬇️ abajo"
    if count > high:
        return "⬆️ arriba"
    return "✅"


def nonland_without_role(analysis: DeckAnalysis) -> list[str]:
    """Cartas que no son tierra, comandante, tutor ni pieza del tema, y no tienen rol detectado."""
    with_role = {name for card_names in analysis.roles.values() for name in card_names}
    with_role.update(theme_pieces(analysis))
    with_role.update(analysis.findings["tutores"])
    return [
        deck_card.name
        for deck_card, card in analysis.entries
        if not is_land(card) and deck_card.category != "Commander" and deck_card.name not in with_role
    ]


def theme_pieces(analysis: DeckAnalysis) -> list[str]:
    """Cartas con alguna etiqueta o tipo del tema que define el perfil."""
    wanted_tags = set(analysis.profile.etiquetas_tema)
    return [
        deck_card.name
        for deck_card, card in analysis.entries
        if wanted_tags & set(deck_card.tags) or has_theme_type(card.type_line, analysis.profile.tipos_tema)
    ]


def has_theme_type(type_line: str, theme_types: list[str]) -> bool:
    """¿La línea de tipo trae alguno de los tipos del tema? "Creature — Dragon" → Dragon."""
    words = type_line.replace("—", " ").replace("//", " ").split()
    return any(theme_type in words for theme_type in theme_types)


def collection_text(info: dict | None) -> str:
    """Línea del encabezado: qué colección se usó para las sugerencias."""
    if info is None:
        return "sin importar (`taller coleccion importar`)"
    return f"{info['total']} cartas ({info['source']}, importada {info['imported_at'][:10]})"


def maybe_with_location(analysis: DeckAnalysis, card_names: list[str]) -> list[str]:
    """Nombres del Maybeboard con su ubicación si ya los tienes."""
    oracle_by_name = {deck_card.name: deck_card.oracle_id for deck_card, _ in analysis.maybe_entries}
    return [with_location(name, oracle_by_name.get(name), analysis.owned) for name in card_names]


def collection_with_location(analysis: DeckAnalysis, card_names: list[str]) -> list[str]:
    """Nombres de cartas de la colección con su ubicación."""
    oracle_by_name = {deck_card.name: deck_card.oracle_id for deck_card, _ in analysis.collection_entries}
    return [with_location(name, oracle_by_name[name], analysis.owned) for name in card_names]


# ---------- Secciones ----------


def header(analysis: DeckAnalysis) -> list[str]:
    profile, deck = analysis.profile, analysis.deck
    lines = [
        f"# {profile.nombre} — análisis",
        "",
        f"- **Fecha:** {date.today().isoformat()}",
        f"- **Comandante:** {profile.comandante}",
        f"- **Bracket objetivo:** {profile.bracket}",
        f"- **Ventana de victoria objetivo:** {profile.ventana_victoria}",
        f"- **Tema:** {profile.tema}",
        f"- **Archidekt:** https://archidekt.com/decks/{deck.archidekt_id} (editado {deck.updated_at[:10]})",
    ]
    lines.append(f"- **Colección:** {collection_text(analysis.collection)}")
    if not profile.lista_sincronizada:
        lines += ["", "> ⚠️ **La lista de Archidekt no está confirmada contra el mazo físico.** "
                      "Toma este reporte como análisis de la lista, no del mazo que juegas."]
    if deck.card_count() != 100:
        lines += ["", f"> ⚠️ La lista tiene {deck.card_count()} cartas, no 100. El análisis está incompleto."]
    if analysis.missing:
        lines += ["", f"> ⚠️ No se encontraron en Scryfall: {names(analysis.missing)}."]
    return lines


def summary(analysis: DeckAnalysis) -> list[str]:
    profile = analysis.profile
    lines = ["## 1. Resumen", ""]

    if analysis.warnings:
        lines.append(f"- **Bracket:** {len(analysis.warnings)} aviso(s) para bracket {profile.bracket}; ver sección 4.")
    else:
        lines.append(f"- **Bracket:** nada en la lista rompe bracket {profile.bracket}.")

    below = roles_below(analysis)
    if below:
        detail = "; ".join(f"{role} ({len(analysis.roles[role])} de {format_range(analysis.references[role])})"
                           for role in below)
        lines.append(f"- **Por debajo de la referencia:** {detail}.")
    else:
        lines.append("- **Roles:** todos dentro o arriba de la referencia.")

    lines.append(f"- **Maná:** {analysis.lands} tierras, costo promedio {analysis.average_cmc}, "
                 f"{len(analysis.roles['ramp'])} piezas de ramp.")
    if profile.tipos_tema or profile.etiquetas_tema:
        lines.append(f"- **Plan:** {len(theme_pieces(analysis))} piezas del tema.")
    else:
        lines.append(f"- **Plan:** {len(analysis.roles['tokens'])} cartas de tokens y "
                     f"{len(analysis.roles['cierre'])} de cierre.")
    if analysis.combos and analysis.combos["presentes"] and (profile.bracket or 3) >= 4:
        lines.append(f"- **Combos:** {len(analysis.combos['presentes'])} presentes; son una ruta de victoria "
                     "alterna (ver sección 5).")
    if "robo" in below and (target_turn(profile.ventana_victoria) or 99) <= 5:
        lines.append(f"- **Para ganar en {profile.ventana_victoria}, el cuello de botella es el robo:** "
                     "sin cartas suficientes, el plan no llega completo a tiempo.")
    return lines


def roles_section(analysis: DeckAnalysis) -> list[str]:
    lines = [
        "## 2. Roles",
        "",
        "Fuente: etiquetas de Scryfall Tagger (vía Archidekt). Una carta puede contar en varios roles.",
        "",
        "| Rol | Cartas | Referencia | Estado |",
        "| --- | --- | --- | --- |",
    ]
    for role, title in ROLE_TITLES.items():
        count = len(analysis.roles[role])
        reference = analysis.references.get(role)
        lines.append(f"| {title} | {count} | {format_range(reference)} | {role_status(count, reference)} |")
    lines.append("")
    for role, title in ROLE_TITLES.items():
        lines.append(f"- **{title}:** {names(analysis.roles[role])}")
    return lines


def mana_section(analysis: DeckAnalysis) -> list[str]:
    lines = [
        "## 3. Curva y base de maná",
        "",
        f"- **Tierras:** {analysis.lands}",
        f"- **Costo promedio** (sin tierras ni comandante): {analysis.average_cmc}",
        "",
        "| Costo | Cartas | |",
        "| --- | --- | --- |",
    ]
    for cmc, count in analysis.curve.items():
        label = "7+" if cmc == 7 else str(cmc)
        lines.append(f"| {label} | {count} | {'█' * count} |")

    sources = ", ".join(f"{COLOR_NAMES[color]} {count}" for color, count in analysis.sources.items())
    lines += [
        "",
        f"- **Fuentes por color (tierras):** {sources}",
        f"- **Entran giradas siempre:** {names(analysis.tapped['siempre'])}",
        f"- **Entran giradas a veces:** {names(analysis.tapped['a_veces'])}",
    ]
    return lines


def bracket_section(analysis: DeckAnalysis) -> list[str]:
    findings = analysis.findings
    target = analysis.profile.bracket or 3
    limit = MAX_GAME_CHANGERS.get(target)
    limit_text = "sin límite" if limit is None else f"máximo {limit}"
    lines = [
        "## 4. Bracket",
        "",
        f"- **Game Changers** ({len(findings['game_changers'])}, {limit_text}): {names(findings['game_changers'])}",
        f"- **Tutores:** {names(findings['tutores'])}",
        f"- **Turnos extra:** {names(findings['turnos_extra'])}",
        f"- **Destrucción masiva de tierras:** {names(findings['destruccion_tierras'])}",
    ]
    if analysis.combos is not None:
        two_card = [combo for combo in analysis.combos["presentes"] if len(combo.cards) == 2]
        lines.append(f"- **Combos de dos cartas presentes:** {len(two_card)}")
    lines.append("")
    if analysis.warnings:
        lines += [f"> ⚠️ {warning}" for warning in analysis.warnings]
    else:
        lines.append(f"✅ Nada rompe bracket {target}.")
    return lines


def combos_section(analysis: DeckAnalysis) -> list[str]:
    lines = ["## 5. Combos", "", "Fuente: Commander Spellbook.", ""]
    if analysis.combos is None:
        return lines + ["> ⚠️ Spellbook no respondió; esta sección queda pendiente."]

    present = analysis.combos["presentes"]
    lines.append(f"**Presentes ({len(present)}):**")
    lines.append("")
    lines += [f"- {' + '.join(combo.cards)} → {combo.results[0]}" for combo in present] or ["- Ninguno."]

    near = sorted(analysis.combos["a_una_carta"], key=lambda combo: combo.popularity, reverse=True)
    lines += ["", f"**A una carta ({len(near)}; los {min(len(near), MAX_NEAR_COMBOS)} más populares):**", ""]
    breaks_bracket = (analysis.profile.bracket or 3) <= 3
    for combo in near[:MAX_NEAR_COMBOS]:
        flag = " ⚠️ combo de dos cartas" if breaks_bracket and len(combo.cards) == 2 else ""
        lines.append(f"- Falta **{names(combo.missing)}**: {' + '.join(combo.cards)} → {combo.results[0]}{flag}")
    return lines


def synergy_section(analysis: DeckAnalysis) -> list[str]:
    lines = ["## 6. Sinergia con el tema", ""]
    criteria = analysis.profile.tipos_tema + analysis.profile.etiquetas_tema
    if criteria:
        pieces = theme_pieces(analysis)
        lines.append(f"- **Piezas del tema** ({', '.join(criteria)}; {len(pieces)}): {names(pieces)}")
    else:
        lines.append("- El perfil no define `tipos_tema` ni `etiquetas_tema`; se usan los roles de tokens y cierre.")
    pushers = sorted(set(analysis.roles["tokens"]) | set(analysis.roles["cierre"]))
    lines.append(f"- **Empujan el plan (tokens o cierre; {len(pushers)}):** {names(pushers)}")
    lines.append(f"- **Sin rol detectado:** {names(nonland_without_role(analysis))}")
    return lines


def suggestions_section(analysis: DeckAnalysis) -> list[str]:
    lines = ["## 7. Sugerencias", ""]
    collection_roles = group_by_role(analysis.collection_entries)
    for role in roles_below(analysis):
        low, high = analysis.references[role]
        candidates = maybe_with_location(analysis, analysis.maybe_roles[role])
        source = f"En tu Maybeboard: {names(candidates)}." if candidates else "Nada en tu Maybeboard cubre este rol."
        lines.append(f"- **Sube {ROLE_TITLES[role].lower()}** ({len(analysis.roles[role])}, referencia {low}–{high}). {source}")
        owned = collection_with_location(analysis, collection_roles[role])
        if owned:
            lines.append(f"  - En tu colección (detectadas por texto, revisa que encajen): {names(owned)}")

    for role, (low, high) in analysis.references.items():
        count = len(analysis.roles[role])
        if count > high:
            lines.append(f"- **{ROLE_TITLES[role]} tiene margen** ({count}, referencia {low}–{high}): "
                         "de aquí puedes liberar espacios.")

    lines += game_changer_suggestion(analysis)

    without_role = nonland_without_role(analysis)
    if without_role:
        lines.append(f"- **Revisa si empujan el plan** (sin rol detectado; candidatas a salir): {names(without_role)}")

    if analysis.combos and (analysis.profile.bracket or 3) <= 3:
        risky = sorted({name for combo in analysis.combos["a_una_carta"] if len(combo.cards) == 2 for name in combo.missing})
        if risky:
            lines.append(f"- **Evita agregar** si quieres quedarte en bracket {analysis.profile.bracket} "
                         f"(completarían un combo de dos cartas): {names(risky)}")

    return lines + [""] + shopping_section(analysis)


def shopping_candidates(analysis: DeckAnalysis) -> dict[str, list[str]]:
    """Lo que el reporte sugiere agregar desde el Maybeboard: {motivo: [nombres]}."""
    candidates = {ROLE_TITLES[role].lower(): analysis.maybe_roles[role] for role in roles_below(analysis)}
    if game_changer_suggestion(analysis):
        candidates["Game Changer"] = maybe_game_changers(analysis)
    return candidates


def shopping_section(analysis: DeckAnalysis) -> list[str]:
    """Tabla con las sugerencias que no tienes, de la más barata a la más cara."""
    rate = analysis.exchange_rate
    items = shopping_list(shopping_candidates(analysis), analysis.maybe_entries, analysis.owned)
    lines = [
        "### Lista de compra",
        "",
        f"Sugerencias del Maybeboard que no están en tu colección. Precio de referencia de Scryfall "
        f"(TCGplayer, {analysis.prices_date}), tipo de cambio {rate:g}. Las ligas buscan la carta en "
        "cada tienda para ver su precio en pesos.",
        "",
    ]
    if not items:
        return lines + ["Nada que comprar: no hay sugerencias del Maybeboard o ya las tienes todas."]

    lines += ["| Carta | Para | USD | MXN aprox. | Tiendas |", "| --- | --- | --- | --- | --- |"]
    for item in items:
        if item.price_usd is None:
            prices = "sin precio | —"
        else:
            prices = f"{item.price_usd:.2f} | ${usd_to_mxn(item.price_usd, rate):,}"
        lines.append(f"| {item.name} | {item.reason} | {prices} | {store_links(item.name)} |")
    total = total_usd(items)
    lines.append(f"| **Total** | | **{total:.2f}** | **${usd_to_mxn(total, rate):,}** | |")
    return lines


def game_changer_suggestion(analysis: DeckAnalysis) -> list[str]:
    """Si el bracket permite Game Changers y sobran espacios, lo dice."""
    limit = MAX_GAME_CHANGERS.get(analysis.profile.bracket or 3)
    used = len(analysis.findings["game_changers"])
    if not limit or used >= limit:
        return []
    in_maybe = maybe_game_changers(analysis)
    extra = f" En tu Maybeboard: {names(maybe_with_location(analysis, in_maybe))}." if in_maybe else ""
    return [f"- **Te quedan {limit - used} espacio(s) de Game Changer** en bracket {analysis.profile.bracket}; "
            f"úsalos en consistencia (robo, protección, ramp).{extra}"]


def store_links(card_name: str) -> str:
    """Ligas Markdown a la búsqueda de la carta en cada tienda."""
    return " · ".join(f"[{store}]({url})" for store, url in search_links(card_name).items())


def maybe_game_changers(analysis: DeckAnalysis) -> list[str]:
    """Game Changers que tienes en el Maybeboard."""
    return [deck_card.name for deck_card, card in analysis.maybe_entries if card.game_changer]


def window_section(analysis: DeckAnalysis) -> list[str]:
    turn = target_turn(analysis.profile.ventana_victoria)
    cheap = analysis.curve[0] + analysis.curve[1] + analysis.curve[2]
    lines = [
        "## 8. Ventana de victoria",
        "",
        f"- **Objetivo del perfil:** {analysis.profile.ventana_victoria}",
        f"- **Cartas de costo 0–2:** {cheap}; **ramp:** {len(analysis.roles['ramp'])}; "
        f"**costo promedio:** {analysis.average_cmc}",
    ]
    if turn is not None and turn <= 5:
        lines.append("- Para ganar tan temprano importa más la consistencia que la potencia: robo suficiente, "
                     "ramp barato y protección para el turno clave.")
    lines.append("- *La estimación por simulación llega en la fase 5.*")
    return lines
