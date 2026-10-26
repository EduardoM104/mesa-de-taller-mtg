"""Revisión de bracket: Game Changers, tutores, turnos extra y destrucción masiva de tierras.

Los combos de dos cartas vienen de Commander Spellbook.
Límites según la guía oficial de brackets de Commander.
"""

import re

from taller.analysis.pairing import Entry
from taller.sources.spellbook import Combo

# Máximo de Game Changers por bracket (None = sin límite).
MAX_GAME_CHANGERS = {1: 0, 2: 0, 3: 3, 4: None, 5: None}

MASS_LAND_DESTRUCTION = re.compile(r"destroy all lands|each player sacrifices .*lands", re.IGNORECASE)
EXTRA_TURN = re.compile(r"take an extra turn", re.IGNORECASE)
SEARCH_LIBRARY = re.compile(r"search your library for [^.]*", re.IGNORECASE)


def is_tutor(entry: Entry) -> bool:
    """¿Busca cartas en la biblioteca? No cuenta buscar tierras (eso es ramp)."""
    deck_card, card = entry
    if deck_card.tags:
        return any(is_tutor_tag(tag) for tag in deck_card.tags)
    # Sin etiquetas: cada frase "search your library for ..." que no hable de tierras.
    for sentence in SEARCH_LIBRARY.findall(card.oracle_text):
        if "land" not in sentence.lower():
            return True
    return False


def is_tutor_tag(tag: str) -> bool:
    """¿La etiqueta indica un tutor de verdad?

    No cuentan: "tutored by name" (Command Tower), "tutor-land-..." (ramp y
    fetchlands) ni "tutor-to-..." (solo dice adónde va la carta; Kodama's
    Reach la trae y es ramp).
    """
    if tag == "tutor":
        return True
    return tag.startswith("tutor-") and not tag.startswith(("tutor-land", "tutor-to-"))


def bracket_findings(entries: list[Entry]) -> dict[str, list[str]]:
    """Cartas relevantes para el bracket, agrupadas por tipo."""
    findings = {"game_changers": [], "tutores": [], "turnos_extra": [], "destruccion_tierras": []}
    for entry in entries:
        deck_card, card = entry
        if card.game_changer:
            findings["game_changers"].append(deck_card.name)
        if is_tutor(entry):
            findings["tutores"].append(deck_card.name)
        if EXTRA_TURN.search(card.oracle_text):
            findings["turnos_extra"].append(deck_card.name)
        if MASS_LAND_DESTRUCTION.search(card.oracle_text):
            findings["destruccion_tierras"].append(deck_card.name)
    return findings


def bracket_warnings(findings: dict[str, list[str]], target: int) -> list[str]:
    """Avisos de lo que podría romper el bracket objetivo."""
    warnings = []
    limit = MAX_GAME_CHANGERS.get(target)
    count = len(findings["game_changers"])
    if limit is not None and count > limit:
        warnings.append(f"{count} Game Changers; bracket {target} permite máximo {limit}.")
    if findings["destruccion_tierras"] and target <= 3:
        warnings.append(f"Destrucción masiva de tierras no está permitida en bracket {target}.")
    if findings["turnos_extra"] and target <= 3:
        warnings.append(f"Turnos extra: en bracket {target} no deben encadenarse.")
    if len(findings["tutores"]) > 2 and target <= 2:
        warnings.append(f"{len(findings['tutores'])} tutores; bracket {target} pide pocos.")
    return warnings


def combo_warnings(present: list[Combo], target: int) -> list[str]:
    """Avisos por combos de dos cartas ya presentes en el mazo."""
    two_card = [combo for combo in present if len(combo.cards) == 2]
    if not two_card or target >= 4:
        return []
    names = "; ".join(" + ".join(combo.cards) for combo in two_card)
    if target <= 2:
        return [f"Combos de dos cartas no permitidos en bracket {target}: {names}."]
    return [f"Combos de dos cartas en bracket 3: no deben armarse antes del turno 6: {names}."]
