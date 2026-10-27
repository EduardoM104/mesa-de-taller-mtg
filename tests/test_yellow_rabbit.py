"""Pruebas de Yellow Rabbit con una respuesta real recortada, sin internet."""

import json
from pathlib import Path

import httpx
import pytest

from taller.prices.yellow_rabbit import best_offer, parse_products, same_card

FIXTURE = Path(__file__).parent / "fixtures" / "yellowrabbit_search.json"


def products():
    return parse_products(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_same_card_ignores_set_and_frame():
    assert same_card("Mentor of the Meek (Retro Frame) [Innistrad Remastered]", "Mentor of the Meek")
    assert not same_card("Monastery Mentor (Extended Art) [March of the Machine]", "Mentor of the Meek")


def test_same_card_accepts_front_face():
    assert same_card("Brightclimb Pathway [Zendikar Rising]", "Brightclimb Pathway // Grimclimb Pathway")


def test_same_card_accepts_alternate_name():
    title = "T'Challa's Protection - Teferi's Protection (Borderless) [Marvel Universe: Eternal-Legal]"
    assert same_card(title, "Teferi's Protection")


def test_best_offer_is_cheapest_available():
    # Innistrad Remastered NM: $15 en stock; Foundations NM: $20. Los HP y Damaged no cuentan.
    offer = best_offer("Mentor of the Meek", products())
    assert offer.price_mxn == 15
    assert offer.title == "Mentor of the Meek [Innistrad Remastered]"
    assert offer.condition.startswith("Near Mint")


def test_no_offer_when_card_is_missing():
    assert best_offer("Teferi's Protection", products()) is None


def test_store_error_is_reported():
    with pytest.raises(httpx.HTTPError):
        parse_products({"jsonrpc": "2.0", "id": 1, "error": {"code": -32001, "message": "UCP discovery failed"}})
