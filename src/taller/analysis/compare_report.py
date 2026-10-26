"""Reporte Markdown de la comparación entre tu mazo y uno ajeno."""

from datetime import date

from taller.analysis.bracket import MAX_GAME_CHANGERS
from taller.analysis.collection import with_location
from taller.analysis.compare import Comparison
from taller.analysis.report import ROLE_TITLES, format_range, names


def render_comparison(comparison: Comparison) -> str:
    """Arma el reporte completo de la comparación."""
    sections = [
        header(comparison),
        roles_table(comparison),
        gaps_section(comparison),
        only_theirs_section(comparison),
        only_mine_section(comparison),
        bracket_section(comparison),
    ]
    return "\n\n".join("\n".join(lines) for lines in sections) + "\n"


def header(comparison: Comparison) -> list[str]:
    own, other = comparison.own, comparison.other
    source = f"https://archidekt.com/decks/{other.archidekt_id}" if other.archidekt_id else "lista en texto"
    lines = [
        f"# {own.profile.nombre} vs {other.name}",
        "",
        f"- **Fecha:** {date.today().isoformat()}",
        f"- **Tu mazo:** {own.profile.nombre}, bracket objetivo {own.profile.bracket}, {own.profile.ventana_victoria}",
        f"- **Su lista:** {other.name} ({source}), {other.card_count()} cartas",
        f"- **Cartas en común** (sin básicas): {comparison.shared}",
    ]
    their_gcs = sum(1 for _, card in comparison.other_entries if card.game_changer)
    limit = MAX_GAME_CHANGERS.get(own.profile.bracket or 3)
    if limit is not None and their_gcs > limit:
        lines += ["", f"> ⚠️ **Su lista lleva {their_gcs} Game Changers**; tu bracket {own.profile.bracket} "
                      f"permite {limit}. Compárala como referencia de ideas, no como modelo a copiar."]
    if comparison.by_text:
        lines += ["", f"> ℹ️ {comparison.by_text} cartas de su lista se clasificaron por su texto "
                      "(sin etiquetas de Tagger); sus conteos de roles son aproximados."]
    if comparison.unresolved:
        lines += ["", f"> ⚠️ No se encontraron en Scryfall: {names(comparison.unresolved)}."]
    return lines


def roles_table(comparison: Comparison) -> list[str]:
    own = comparison.own
    lines = [
        "## 1. Lado a lado",
        "",
        "| | Tú | Ellos | Referencia |",
        "| --- | --- | --- | --- |",
        f"| Tierras | {own.lands} | {comparison.other_lands} | — |",
        f"| Costo promedio | {own.average_cmc} | {comparison.other_average_cmc} | — |",
    ]
    for role, title in ROLE_TITLES.items():
        reference = format_range(own.references.get(role))
        lines.append(f"| {title} | {len(own.roles[role])} | {len(comparison.other_roles[role])} | {reference} |")
    return lines


def theirs_with_location(comparison: Comparison, card_names: list[str]) -> list[str]:
    """Nombres de su lista con su ubicación si ya los tienes en tu colección."""
    oracle_by_name = {deck_card.name: deck_card.oracle_id for deck_card, _ in comparison.other_entries}
    return [with_location(name, oracle_by_name.get(name), comparison.own.owned) for name in card_names]


def gaps_section(comparison: Comparison) -> list[str]:
    lines = ["## 2. Sus cartas que cubren tus huecos", ""]
    if not comparison.fills_gaps:
        return lines + ["Tu mazo no tiene roles por debajo de la referencia."]
    for role, card_names in comparison.fills_gaps.items():
        located = theirs_with_location(comparison, card_names)
        lines.append(f"- **{ROLE_TITLES[role]}** (tienes {len(comparison.own.roles[role])}): {names(located)}")
    return lines


def only_theirs_section(comparison: Comparison) -> list[str]:
    """Las cartas que solo ellos tienen, agrupadas por rol."""
    lines = [f"## 3. Solo en su lista ({len(comparison.only_theirs)})", ""]
    only_theirs = set(comparison.only_theirs)
    placed = set()
    for role, title in ROLE_TITLES.items():
        in_role = [name for name in comparison.other_roles[role] if name in only_theirs]
        placed.update(in_role)
        if in_role:
            lines.append(f"- **{title}:** {names(theirs_with_location(comparison, in_role))}")
    others = [name for name in comparison.only_theirs if name not in placed]
    lines.append(f"- **Sin rol detectado / tierras:** {names(theirs_with_location(comparison, others))}")
    return lines


def only_mine_section(comparison: Comparison) -> list[str]:
    return [
        f"## 4. Solo en tu lista ({len(comparison.only_mine)})",
        "",
        names(comparison.only_mine),
    ]


def bracket_section(comparison: Comparison) -> list[str]:
    """Avisos de su lista contra tu bracket objetivo."""
    own = comparison.own
    only_theirs = set(comparison.only_theirs)
    their_gcs = [deck_card.name for deck_card, card in comparison.other_entries
                 if card.game_changer and deck_card.name in only_theirs]
    lines = [
        "## 5. Ojo con el bracket",
        "",
        f"- **Game Changers que ellos tienen y tú no:** {names(their_gcs)} "
        f"(llevas {len(own.findings['game_changers'])})",
    ]
    if own.combos is not None:
        combo_pieces = {name for combo in own.combos["a_una_carta"] if len(combo.cards) == 2 for name in combo.missing}
        risky = sorted(combo_pieces & only_theirs)
        lines.append(f"- **Completarían un combo de dos cartas en tu mazo:** {names(risky)}")
    return lines
