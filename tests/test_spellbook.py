"""Pruebas de Commander Spellbook, sin internet.

tests/fixtures/spellbook_combos.json es una respuesta reducida: un combo
"presente" (Mirkwood Bats + Plague of Vermin) y uno a una carta
(Aurelia + Helm of the Host).
"""

import json
from pathlib import Path

from taller.analysis.bracket import combo_warnings
from taller.sources.archidekt import Deck, DeckCard
from taller.sources.spellbook import deck_fingerprint, parse_combos, request_body

FIXTURE = Path(__file__).parent / "fixtures" / "spellbook_combos.json"


def make_deck(names):
    # El primer nombre es el comandante.
    cards = [
        DeckCard(name=name, quantity=1, scryfall_id="x", oracle_id=name,
                 category="Commander" if index == 0 else "Plan Cards")
        for index, name in enumerate(names)
    ]
    return Deck(archidekt_id=1, name="Prueba", updated_at="", commanders=cards[:1],
                mainboard=cards, maybeboard=[])


def load_combos():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    deck_names = {"Isshin, Two Heavens as One", "Aurelia, the Warleader", "Mirkwood Bats", "Plague of Vermin"}
    return parse_combos(raw, deck_names)


def test_missing_card_is_detected():
    combo = load_combos()["a_una_carta"][0]
    assert combo.missing == ["Helm of the Host"]
    assert "Infinite combat phases" in combo.results


def test_present_combo_has_no_missing_cards():
    combo = load_combos()["presentes"][0]
    assert combo.missing == []


def test_commander_is_not_sent_in_main():
    body = request_body(make_deck(["Isshin", "Sol Ring"]))
    assert body["commanders"] == [{"card": "Isshin"}]
    assert body["main"] == [{"card": "Sol Ring", "quantity": 1}]


def test_fingerprint_changes_when_list_changes():
    before = deck_fingerprint(make_deck(["Isshin", "Sol Ring"]))
    after = deck_fingerprint(make_deck(["Isshin", "Arcane Signet"]))
    assert before != after


def test_two_card_combo_warns_in_bracket_3():
    warnings = combo_warnings(load_combos()["presentes"], target=3)
    assert len(warnings) == 1
    assert "Mirkwood Bats + Plague of Vermin" in warnings[0]


def test_two_card_combo_is_fine_in_bracket_4():
    assert combo_warnings(load_combos()["presentes"], target=4) == []
