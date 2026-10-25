"""Pruebas de mazos ajenos (texto de Moxfield, URL de Archidekt) y de la comparación."""

import gzip
import json

from taller.analysis.compare import with_known_tags
from taller.cli import slugify
from taller.sources.archidekt import DeckCard
from taller.sources.decklist import ARCHIDEKT_URL, parse_text_list
from taller.sources.scryfall import build_card_table, find_cards_by_name

MOXFIELD_TEXT = """
Commander
1 Isshin, Two Heavens as One (NEO) 224

Deck
1 Sol Ring (CMM) 410 *F*
1x Hero of Bladehold
10 Plains

Sideboard:
1 Teferi's Protection
"""


def test_parse_text_list():
    assert parse_text_list(MOXFIELD_TEXT) == [
        (1, "Isshin, Two Heavens as One", True),
        (1, "Sol Ring", False),  # se quitan la edición, el número y la marca *F*
        (1, "Hero of Bladehold", False),  # acepta "1x"
        (10, "Plains", False),
    ]  # Teferi's Protection está en Sideboard: se ignora


def test_archidekt_url_is_detected():
    match = ARCHIDEKT_URL.search("https://archidekt.com/decks/3027185/isshin_makes_tokens")
    assert match.group(1) == "3027185"


def test_find_double_faced_card_by_front_name(tmp_path):
    # Algunas páginas exportan solo la cara frontal: "Brightclimb Pathway".
    bulk, db = tmp_path / "bulk.jsonl.gz", tmp_path / "test.db"
    pathway = {"oracle_id": "p", "name": "Brightclimb Pathway // Grimclimb Pathway",
               "layout": "modal_dfc", "type_line": "Land // Land", "prices": {}}
    with gzip.open(bulk, "wt", encoding="utf-8") as file:
        file.write(json.dumps(pathway) + "\n")
    build_card_table(bulk, db)

    found = find_cards_by_name(["brightclimb pathway"], db)
    assert found["brightclimb pathway"].oracle_id == "p"


def test_exact_name_wins_over_odd_double_faced(tmp_path):
    # Scryfall tiene cartas raras como "Plains // Plains" (reversibles): no deben ganarle a "Plains".
    bulk, db = tmp_path / "bulk.jsonl.gz", tmp_path / "test.db"
    odd = {"oracle_id": "odd", "name": "Plains // Plains", "layout": "reversible_card",
           "type_line": "Basic Land — Plains // Basic Land — Plains", "prices": {}}
    plains = {"oracle_id": "real", "name": "Plains", "layout": "normal",
              "type_line": "Basic Land — Plains", "prices": {}}
    with gzip.open(bulk, "wt", encoding="utf-8") as file:
        file.write(json.dumps(odd) + "\n" + json.dumps(plains) + "\n")
    build_card_table(bulk, db)

    assert find_cards_by_name(["Plains"], db)["plains"].oracle_id == "real"


def test_known_tags_are_copied():
    card = DeckCard(name="Sol Ring", quantity=1, scryfall_id="", oracle_id="sol", category="")
    assert with_known_tags(card, {"sol": ["adds multiple mana"]}).tags == ["adds multiple mana"]


def test_slugify():
    assert slugify("[1/32] Isshin Makes Alotta Tokens!") == "1-32-isshin-makes-alotta-tokens"
