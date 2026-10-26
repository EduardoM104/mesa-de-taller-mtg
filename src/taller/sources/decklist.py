"""Mazos ajenos: una URL de Archidekt o un texto exportado (Moxfield, Arena, etc.).

Formato de texto que se acepta, una carta por línea:

    1 Sol Ring
    1x Sol Ring
    1 Sol Ring (CMM) 410
    1 Sol Ring (CMM) 410 *F*

Las líneas sin número ("Commander", "Deck", "Sideboard:") marcan secciones.
Se ignoran Sideboard y Maybeboard. Las cartas de la sección Commander se
marcan como comandante.
"""

import re
from pathlib import Path

from taller.sources.archidekt import Deck, DeckCard, fetch_deck
from taller.sources.scryfall import find_cards_by_name

ARCHIDEKT_URL = re.compile(r"archidekt\.com/decks/(\d+)")
# cantidad, nombre y, opcionalmente, (EDICIÓN) número y marcas como *F*
CARD_LINE = re.compile(r"^(\d+)x?\s+(.+?)(\s+\([A-Za-z0-9]+\)\s+\S+)?(\s+\*\w+\*)*$")
SKIPPED_SECTIONS = {"sideboard", "maybeboard", "considering", "tokens"}


def load_other_deck(source: str, refresh: bool = False) -> tuple[Deck, list[str]]:
    """Carga un mazo ajeno desde una URL de Archidekt o un archivo de texto.

    Devuelve el mazo y los nombres que no se encontraron en Scryfall.
    """
    match = ARCHIDEKT_URL.search(source)
    if match:
        return fetch_deck(int(match.group(1)), refresh=refresh), []
    path = Path(source)
    return deck_from_text(path.read_text(encoding="utf-8"), name=path.stem)


def parse_text_list(text: str) -> list[tuple[int, str, bool]]:
    """Lee el texto y devuelve [(cantidad, nombre, es_comandante)]."""
    cards = []
    section = "deck"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        match = CARD_LINE.match(line)
        if match is None:
            # Una línea sin número es el título de una sección.
            section = line.rstrip(":").lower()
            continue
        if section in SKIPPED_SECTIONS:
            continue
        cards.append((int(match.group(1)), match.group(2), section == "commander"))
    return cards


def deck_from_text(text: str, name: str) -> tuple[Deck, list[str]]:
    """Convierte un texto en un Deck, buscando cada carta en Scryfall por nombre."""
    lines = parse_text_list(text)
    found = find_cards_by_name([card_name for _, card_name, _ in lines])

    mainboard, commanders, unresolved = [], [], []
    for quantity, card_name, is_commander in lines:
        card = found.get(card_name.lower())
        if card is None:
            unresolved.append(card_name)
            continue
        deck_card = DeckCard(
            name=card.name,
            quantity=quantity,
            scryfall_id="",
            oracle_id=card.oracle_id,
            category="Commander" if is_commander else "",
        )
        mainboard.append(deck_card)
        if is_commander:
            commanders.append(deck_card)

    deck = Deck(archidekt_id=0, name=name, updated_at="", commanders=commanders,
                mainboard=mainboard, maybeboard=[])
    return deck, unresolved
