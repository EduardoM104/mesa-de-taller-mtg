"""Lista de compra: las cartas sugeridas que no tienes, con su precio de referencia en MXN.

El precio de referencia es el de Scryfall (viene de TCGplayer, en USD) para
la impresión que Scryfall usa como referencia; no siempre es la más barata.
"""

from dataclasses import dataclass

from taller.analysis.pairing import Entry


@dataclass
class ShoppingItem:
    name: str
    reason: str  # por qué se sugiere: el rol que cubre, o "Game Changer"
    price_usd: float | None


def usd_to_mxn(usd: float, rate: float) -> int:
    """Convierte a pesos y redondea al peso: 4.72 USD × 18 → 85."""
    return round(usd * rate)


def shopping_list(candidates: dict[str, list[str]], maybe_entries: list[Entry],
                  owned: dict) -> list[ShoppingItem]:
    """Cartas sugeridas del Maybeboard que no tienes, de la más barata a la más cara.

    `candidates` va de motivo a nombres de cartas (ej. {"robo": ["Mentor of the Meek"]}).
    Una carta que aparece en varios motivos sale una sola vez, con todos ellos.
    """
    by_name = {deck_card.name: (deck_card, card) for deck_card, card in maybe_entries}
    reasons = {}
    for reason, card_names in candidates.items():
        for name in card_names:
            reasons.setdefault(name, []).append(reason)

    items = []
    for name, card_reasons in reasons.items():
        deck_card, card = by_name[name]
        if deck_card.oracle_id in owned:
            continue
        items.append(ShoppingItem(name=name, reason=", ".join(card_reasons), price_usd=card.price_usd))
    # Sin precio al final; entre las demás, de la más barata a la más cara.
    return sorted(items, key=lambda item: (item.price_usd is None, item.price_usd or 0, item.name))


def total_usd(items: list[ShoppingItem]) -> float:
    """Suma de los precios conocidos (las cartas sin precio no cuentan)."""
    return sum(item.price_usd for item in items if item.price_usd is not None)
