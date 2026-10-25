"""Pruebas de Scryfall sin internet: armamos un bulk falso de 3 cartas."""

import gzip
import json
from datetime import date

from taller.sources.scryfall import build_card_table, cards_date, get_cards, to_card

ISSHIN = {
    "oracle_id": "isshin-id",
    "name": "Isshin, Two Heavens as One",
    "layout": "normal",
    "mana_cost": "{R}{W}{B}",
    "cmc": 3.0,
    "type_line": "Legendary Creature — Human Samurai",
    "oracle_text": "If a creature attacking causes a triggered ability...",
    "colors": ["B", "R", "W"],
    "color_identity": ["B", "R", "W"],
    "game_changer": False,
    "prices": {"usd": "3.65"},
}

# Carta de dos caras: el texto viene dentro de card_faces y no tiene precio.
PATHWAY = {
    "oracle_id": "pathway-id",
    "name": "Brightclimb Pathway // Grimclimb Pathway",
    "layout": "modal_dfc",
    "cmc": 0.0,
    "type_line": "Land // Land",
    "color_identity": ["B", "W"],
    "produced_mana": ["B", "W"],
    "card_faces": [
        {"name": "Brightclimb Pathway", "mana_cost": "", "oracle_text": "{T}: Add {W}."},
        {"name": "Grimclimb Pathway", "mana_cost": "", "oracle_text": "{T}: Add {B}."},
    ],
    "prices": {"usd": None},
}

# Algunas cartas especiales no traen oracle_id: deben ignorarse.
NO_ORACLE = {"name": "Carta rara", "layout": "reversible_card"}


def write_bulk(path, cards):
    with gzip.open(path, "wt", encoding="utf-8") as file:
        for card in cards:
            file.write(json.dumps(card) + "\n")


def test_double_faced_text_is_joined():
    card = to_card(PATHWAY)
    assert card.oracle_text == "{T}: Add {W}.\n//\n{T}: Add {B}."
    assert card.price_usd is None


def test_price_is_converted_to_number():
    assert to_card(ISSHIN).price_usd == 3.65


def test_build_and_query_table(tmp_path):
    bulk = tmp_path / "bulk.jsonl.gz"
    db = tmp_path / "test.db"
    write_bulk(bulk, [ISSHIN, PATHWAY, NO_ORACLE])

    assert build_card_table(bulk, db) == 2  # la carta sin oracle_id se salta
    assert cards_date(db) == date.today().isoformat()

    cards = get_cards(["isshin-id", "no-existe"], db)
    assert list(cards) == ["isshin-id"]
    assert cards["isshin-id"].colors == ["B", "R", "W"]  # la lista sobrevive al guardado
