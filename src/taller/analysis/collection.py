"""Cruza la colección física con un mazo: qué cartas ya tienes y dónde están."""

from taller.analysis.pairing import Entry
from taller.sources.archidekt import DeckCard
from taller.sources.scryfall import Card

Owned = dict[str, dict[str, int]]  # oracle_id → {binder: copias}


def location_text(binders: dict[str, int]) -> str:
    """{"Orzhov WB": 2, "Golgari - GB": 1} → "Orzhov WB ×2, Golgari - GB"."""
    return ", ".join(f"{binder} ×{copies}" if copies > 1 else binder for binder, copies in binders.items())


def with_location(name: str, oracle_id: str | None, owned: Owned) -> str:
    """Agrega dónde está la carta si la tienes: "Corpse Knight (la tienes: Orzhov WB)"."""
    if oracle_id not in owned:
        return name
    return f"{name} (la tienes: {location_text(owned[oracle_id])})"


def fitting_entries(cards: dict[str, Card], identity: list[str], exclude: set[str]) -> list[Entry]:
    """Cartas de la colección que caben en la identidad del mazo y no están en `exclude`.

    `cards` va de oracle_id a Card; `exclude` son oracle_ids (el mazo y su Maybeboard).
    Como no traen etiquetas de Tagger, sus roles se detectan por el texto.
    """
    entries = []
    for oracle_id, card in sorted(cards.items(), key=lambda item: item[1].name):
        if oracle_id in exclude or not set(card.color_identity) <= set(identity):
            continue
        deck_card = DeckCard(name=card.name, quantity=1, scryfall_id="", oracle_id=oracle_id,
                             category="Colección", tags=[])
        entries.append((deck_card, card))
    return entries
