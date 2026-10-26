"""Pruebas de Archidekt y de la caché, sin usar internet.

tests/fixtures/archidekt_deck.json es una copia reducida del mazo Tokens real.
"""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from taller.sources.archidekt import parse_deck
from taller.sources.cache import cache_path, get_json

FIXTURE = Path(__file__).parent / "fixtures" / "archidekt_deck.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_commander_is_detected():
    deck = parse_deck(load_fixture())
    assert [card.name for card in deck.commanders] == ["Isshin, Two Heavens as One"]


def test_maybeboard_is_separated():
    deck = parse_deck(load_fixture())
    assert [card.name for card in deck.maybeboard] == ["Teferi's Protection"]
    assert "Teferi's Protection" not in [card.name for card in deck.mainboard]


def test_mainboard_includes_commander():
    # El comandante cuenta dentro de las 100 cartas, así que también va en mainboard.
    deck = parse_deck(load_fixture())
    mainboard_names = [card.name for card in deck.mainboard]
    assert "Isshin, Two Heavens as One" in mainboard_names


def test_card_count_includes_copies():
    # Comandante + 2 cartas + 2 Swamp = 5 (Teferi's Protection está en Maybeboard).
    deck = parse_deck(load_fixture())
    assert deck.card_count() == 5


def test_get_json_uses_todays_cache(tmp_path):
    # Si ya existe la copia de hoy, no debe tocar internet: la URL es falsa a propósito.
    path = cache_path("archidekt", "123", date.today(), cache_dir=tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text('{"ok": true}', encoding="utf-8")

    data = get_json("https://no-existe.invalid/", "archidekt", "123", cache_dir=tmp_path)
    assert data == {"ok": True}


def test_refresh_ignores_todays_cache(tmp_path):
    # Con refresh=True no debe usar la copia: intenta descargar y falla con la URL falsa.
    path = cache_path("archidekt", "123", date.today(), cache_dir=tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text('{"ok": true}', encoding="utf-8")

    with pytest.raises(httpx.HTTPError):
        get_json("https://no-existe.invalid/", "archidekt", "123", cache_dir=tmp_path, refresh=True)
