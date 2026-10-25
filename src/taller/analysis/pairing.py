"""Junta cada carta del mazo (Archidekt) con sus datos de Scryfall."""

from taller.sources.archidekt import DeckCard
from taller.sources.scryfall import Card

# Una carta del mazo junto con sus datos: (carta de Archidekt, carta de Scryfall).
Entry = tuple[DeckCard, Card]


def pair_cards(deck_cards: list[DeckCard], cards: dict[str, Card]) -> tuple[list[Entry], list[str]]:
    """Devuelve las parejas y los nombres que no se encontraron en Scryfall."""
    entries, missing = [], []
    for deck_card in deck_cards:
        card = cards.get(deck_card.oracle_id)
        if card is None:
            missing.append(deck_card.name)
        else:
            entries.append((deck_card, card))
    return entries, missing


def is_land(card: Card) -> bool:
    """¿Es tierra? Se mira solo la cara frontal: "Instant // Land" cuenta como hechizo."""
    front_type = card.type_line.split(" // ")[0]
    return "Land" in front_type
