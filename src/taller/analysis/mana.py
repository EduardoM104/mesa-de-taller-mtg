"""Curva de maná y base de maná: tierras, fuentes por color y tierras giradas."""

import re

from taller.analysis.pairing import Entry, is_land

COLORS = ["W", "U", "B", "R", "G"]

# Tierras que entran giradas, y las que solo a veces (shocks, checklands...).
ENTERS_TAPPED = re.compile(r"enters (the battlefield )?tapped", re.IGNORECASE)
CONDITIONAL = re.compile(r"unless|if you don't|you may pay", re.IGNORECASE)


def deck_identity(entries: list[Entry]) -> list[str]:
    """Identidad de color del mazo: la suma de los colores de sus comandantes."""
    identity = set()
    for deck_card, card in entries:
        if deck_card.category == "Commander":
            identity.update(card.color_identity)
    return [color for color in COLORS if color in identity]


def land_count(entries: list[Entry]) -> int:
    """Número de tierras, contando copias."""
    return sum(deck_card.quantity for deck_card, card in entries if is_land(card))


def mana_curve(entries: list[Entry]) -> dict[int, int]:
    """Cuántas cartas hay por costo, sin tierras ni comandante. La llave 7 agrupa 7+."""
    curve = {cmc: 0 for cmc in range(8)}
    for deck_card, card in entries:
        if is_land(card) or deck_card.category == "Commander":
            continue
        curve[min(int(card.cmc), 7)] += deck_card.quantity
    return curve


def average_cmc(curve: dict[int, int]) -> float:
    """Costo promedio a partir de la curva (los 7+ cuentan como 7)."""
    total_cards = sum(curve.values())
    if total_cards == 0:
        return 0.0
    total_mana = sum(cmc * count for cmc, count in curve.items())
    return round(total_mana / total_cards, 2)


def color_sources(entries: list[Entry], identity: list[str]) -> dict[str, int]:
    """Cuántas tierras producen cada color del comandante, contando copias.

    Se limita a `identity` porque, por ejemplo, Command Tower "produce" los 5
    colores en Scryfall, pero en el mazo solo da los del comandante.
    """
    sources = {color: 0 for color in COLORS if color in identity}
    for deck_card, card in entries:
        if not is_land(card):
            continue
        for color in card.produced_mana:
            if color in sources:
                sources[color] += deck_card.quantity
    return sources


def tapped_lands(entries: list[Entry]) -> dict[str, list[str]]:
    """Tierras que entran giradas: {"siempre": [...], "a_veces": [...]}."""
    result = {"siempre": [], "a_veces": []}
    for deck_card, card in entries:
        if not is_land(card) or not ENTERS_TAPPED.search(card.oracle_text):
            continue
        kind = "a_veces" if CONDITIONAL.search(card.oracle_text) else "siempre"
        result[kind].append(deck_card.name)
    return result
