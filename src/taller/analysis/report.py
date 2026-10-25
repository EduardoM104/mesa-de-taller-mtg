"""Convierte un DeckAnalysis en el reporte Markdown, siempre contra el perfil.

Cada sección es una función que devuelve una lista de líneas; render()
las junta en el orden que pide CLAUDE.md.
"""

from datetime import date

from taller.analysis.analyze import DeckAnalysis, target_turn
from taller.analysis.bracket import MAX_GAME_CHANGERS
from taller.analysis.pairing import is_land
from taller.analysis.roles import REFERENCES

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
    return [role for role, (low, _) in REFERENCES.items() if len(analysis.roles[role]) < low]


def role_status(count: int, role: str) -> str:
    """✅ dentro del rango, ⬇️ abajo, ⬆️ arriba, — si no hay referencia."""
    if role not in REFERENCES:
        return "—"
    low, high = REFERENCES[role]
    if count < low:
        return "⬇️ abajo"
    if count > high:
        return "⬆️ arriba"
    return "✅"


def nonland_without_role(analysis: DeckAnalysis) -> list[str]:
    """Cartas que no son tierra, comandante ni pieza del tema, y no tienen rol detectado."""
    with_role = {name for card_names in analysis.roles.values() for name in card_names}
    with_role.update(theme_pieces(analysis))
    return [
        deck_card.name
        for deck_card, card in analysis.entries
        if not is_land(card) and deck_card.category != "Commander" and deck_card.name not in with_role
    ]


def theme_pieces(analysis: DeckAnalysis) -> list[str]:
    """Cartas con alguna de las etiquetas del tema que define el perfil."""
    wanted = set(analysis.profile.etiquetas_tema)
    return [deck_card.name for deck_card, _ in analysis.entries if wanted & set(deck_card.tags)]


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
        detail = "; ".join(f"{role} ({len(analysis.roles[role])} de {REFERENCES[role][0]}–{REFERENCES[role][1]})" for role in below)
        lines.append(f"- **Por debajo de la referencia:** {detail}.")
    else:
        lines.append("- **Roles:** todos dentro o arriba de la referencia.")

    lines.append(f"- **Maná:** {analysis.lands} tierras, costo promedio {analysis.average_cmc}, "
                 f"{len(analysis.roles['ramp'])} piezas de ramp.")
    lines.append(f"- **Plan:** {len(analysis.roles['tokens'])} cartas de tokens y "
                 f"{len(analysis.roles['cierre'])} de cierre.")
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
        reference = "–".join(str(n) for n in REFERENCES[role]) if role in REFERENCES else "—"
        lines.append(f"| {title} | {count} | {reference} | {role_status(count, role)} |")
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
    tags = analysis.profile.etiquetas_tema
    if tags:
        pieces = theme_pieces(analysis)
        lines.append(f"- **Piezas del tema** (etiquetas: {', '.join(tags)}; {len(pieces)}): {names(pieces)}")
    else:
        lines.append("- El perfil no define `etiquetas_tema`; se usan los roles de tokens y cierre.")
    pushers = sorted(set(analysis.roles["tokens"]) | set(analysis.roles["cierre"]))
    lines.append(f"- **Empujan el plan (tokens o cierre; {len(pushers)}):** {names(pushers)}")
    lines.append(f"- **Sin rol detectado:** {names(nonland_without_role(analysis))}")
    return lines


def suggestions_section(analysis: DeckAnalysis) -> list[str]:
    lines = ["## 7. Sugerencias", ""]
    for role in roles_below(analysis):
        low, high = REFERENCES[role]
        candidates = analysis.maybe_roles[role]
        source = f"En tu Maybeboard: {names(candidates)}." if candidates else "Nada en tu Maybeboard cubre este rol."
        lines.append(f"- **Sube {ROLE_TITLES[role].lower()}** ({len(analysis.roles[role])}, referencia {low}–{high}). {source}")

    for role, (low, high) in REFERENCES.items():
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

    lines.append("- *Prioridad por colección y precio: llega en las fases 2 y 3.*")
    return lines


def game_changer_suggestion(analysis: DeckAnalysis) -> list[str]:
    """Si el bracket permite Game Changers y sobran espacios, lo dice."""
    limit = MAX_GAME_CHANGERS.get(analysis.profile.bracket or 3)
    used = len(analysis.findings["game_changers"])
    if not limit or used >= limit:
        return []
    in_maybe = [deck_card.name for deck_card, card in analysis.maybe_entries if card.game_changer]
    extra = f" En tu Maybeboard: {names(in_maybe)}." if in_maybe else ""
    return [f"- **Te quedan {limit - used} espacio(s) de Game Changer** en bracket {analysis.profile.bracket}; "
            f"úsalos en consistencia (robo, protección, ramp).{extra}"]


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
