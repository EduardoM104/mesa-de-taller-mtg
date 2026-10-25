"""Archidekt: trae los mazos de Martín desde el endpoint público.

Archidekt es la fuente de verdad de los mazos. Cada carta trae una lista de
categorías; la primera es la principal y decide si la carta cuenta para el
mazo (por ejemplo, "Maybeboard" tiene includedInDeck = false).
"""

from pydantic import BaseModel

from taller.sources.cache import get_json

API_URL = "https://archidekt.com/api/decks/{deck_id}/"


class DeckCard(BaseModel):
    """Una carta del mazo, con lo mínimo para cruzarla con Scryfall."""

    name: str
    quantity: int
    scryfall_id: str  # id de la impresión elegida en Archidekt
    oracle_id: str  # id de la carta sin importar la edición
    category: str  # categoría principal en Archidekt ("" si no tiene)
    tags: list[str] = []  # etiquetas de Scryfall Tagger que trae Archidekt (oTags)


class Deck(BaseModel):
    """Un mazo ya separado en comandantes, mazo principal y Maybeboard."""

    archidekt_id: int
    name: str
    updated_at: str
    commanders: list[DeckCard]
    mainboard: list[DeckCard]  # incluye a los comandantes
    maybeboard: list[DeckCard]

    def card_count(self) -> int:
        """Total de cartas del mazo principal, contando copias."""
        return sum(card.quantity for card in self.mainboard)


def fetch_deck(deck_id: int) -> Deck:
    """Descarga (o lee de caché) el mazo y lo convierte en un Deck."""
    raw = get_json(API_URL.format(deck_id=deck_id), source="archidekt", key=str(deck_id))
    return parse_deck(raw)


def parse_deck(raw: dict) -> Deck:
    """Convierte la respuesta cruda de Archidekt en un Deck."""
    # Qué categorías cuentan para el mazo, según la configuración del mazo.
    included = {cat["name"]: cat["includedInDeck"] for cat in raw["categories"]}

    commanders, mainboard, maybeboard = [], [], []
    for entry in raw["cards"]:
        card = to_deck_card(entry)
        if included.get(card.category, True):
            mainboard.append(card)
            if card.category == "Commander":
                commanders.append(card)
        else:
            maybeboard.append(card)

    return Deck(
        archidekt_id=raw["id"],
        name=raw["name"],
        updated_at=raw["updatedAt"],
        commanders=commanders,
        mainboard=mainboard,
        maybeboard=maybeboard,
    )


def to_deck_card(entry: dict) -> DeckCard:
    """Convierte una entrada de carta de Archidekt en un DeckCard."""
    categories = entry.get("categories") or []
    oracle = entry["card"]["oracleCard"]
    return DeckCard(
        name=oracle["name"],
        quantity=entry["quantity"],
        scryfall_id=entry["card"]["uid"],
        oracle_id=oracle["uid"],
        category=categories[0] if categories else "",
        tags=oracle.get("oTags") or [],
    )
