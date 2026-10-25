"""Commander Spellbook: combos presentes en el mazo y a una carta de distancia.

Usa el endpoint público "find my combos": se le manda la lista y responde
qué combos están completos ("included") y a cuáles les falta una carta
("almostIncluded"). Los que requieren agregar colores se ignoran porque
salen de la identidad del comandante.
"""

import hashlib

from pydantic import BaseModel

from taller.sources.archidekt import Deck
from taller.sources.cache import post_json

API_URL = "https://backend.commanderspellbook.com/find-my-combos"


class Combo(BaseModel):
    """Un combo de Spellbook, con lo que necesita el reporte."""

    id: str
    cards: list[str]
    results: list[str]  # lo que produce, ej. "Infinite combat phases"
    prerequisites: str  # condiciones notables, ej. "Helm attached to Aurelia."
    popularity: int  # en cuántos mazos de la base de Spellbook aparece
    missing: list[str] = []  # cartas que no están en el mazo


def fetch_combos(deck: Deck) -> dict[str, list[Combo]]:
    """Consulta (o lee de caché) los combos del mazo."""
    body = request_body(deck)
    raw = post_json(API_URL, body, source="spellbook", key=deck_fingerprint(deck))
    deck_names = {card.name for card in deck.mainboard}
    return parse_combos(raw, deck_names)


def request_body(deck: Deck) -> dict:
    """Arma la lista en el formato que pide Spellbook."""
    commanders = [{"card": card.name} for card in deck.commanders]
    main = [
        {"card": card.name, "quantity": card.quantity}
        for card in deck.mainboard
        if card.category != "Commander"
    ]
    return {"commanders": commanders, "main": main}


def deck_fingerprint(deck: Deck) -> str:
    """Huella corta de la lista: cambia si cambia cualquier carta o cantidad.

    Sirve como clave de caché: misma lista y mismo día = misma respuesta.
    """
    lines = sorted(f"{card.quantity} {card.name}" for card in deck.mainboard)
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return f"{deck.archidekt_id}-{digest[:12]}"


def parse_combos(raw: dict, deck_names: set[str]) -> dict[str, list[Combo]]:
    """Convierte la respuesta en {"presentes": [...], "a_una_carta": [...]}."""
    results = raw["results"]
    return {
        "presentes": [to_combo(variant, deck_names) for variant in results["included"]],
        "a_una_carta": [to_combo(variant, deck_names) for variant in results["almostIncluded"]],
    }


def to_combo(variant: dict, deck_names: set[str]) -> Combo:
    """Convierte una variante de Spellbook en un Combo."""
    cards = [use["card"]["name"] for use in variant["uses"]]
    return Combo(
        id=variant["id"],
        cards=cards,
        results=[item["feature"]["name"] for item in variant["produces"]],
        prerequisites=variant.get("notablePrerequisites", ""),
        popularity=variant.get("popularity") or 0,
        missing=[name for name in cards if name not in deck_names],
    )
