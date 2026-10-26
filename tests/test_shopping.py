"""Pruebas de la lista de compra y la conversión a pesos."""

from taller.config import exchange_rate
from taller.prices.shopping import shopping_list, total_usd, usd_to_mxn
from taller.prices.stores import search_links

from helpers import make_entry


def priced(name, usd):
    deck_card, card = make_entry(name)
    card.price_usd = usd
    return deck_card, card


MAYBE = [priced("Mentor of the Meek", 4.72), priced("Rhystic Study", 30.0), priced("Caesar", None),
         priced("Night's Whisper", 0.5)]


def test_usd_to_mxn_rounds_to_peso():
    assert usd_to_mxn(4.72, 18) == 85


def test_exchange_rate_defaults_to_18(tmp_path):
    assert exchange_rate(tmp_path / "no-existe.toml") == 18.0
    config_file = tmp_path / "config.toml"
    config_file.write_text("[precios]\ntipo_de_cambio = 19.5\n")
    assert exchange_rate(config_file) == 19.5


def test_shopping_list_sorted_cheapest_first_without_price_last():
    items = shopping_list({"robo": ["Mentor of the Meek", "Rhystic Study", "Caesar", "Night's Whisper"]}, MAYBE, {})
    assert [item.name for item in items] == ["Night's Whisper", "Mentor of the Meek", "Rhystic Study", "Caesar"]


def test_shopping_list_skips_cards_you_own():
    items = shopping_list({"robo": ["Mentor of the Meek", "Night's Whisper"]}, MAYBE,
                          {"Night's Whisper": {"Mono negro": 1}})
    assert [item.name for item in items] == ["Mentor of the Meek"]


def test_card_with_two_reasons_appears_once():
    items = shopping_list({"robo": ["Rhystic Study"], "Game Changer": ["Rhystic Study"]}, MAYBE, {})
    assert len(items) == 1
    assert items[0].reason == "robo, Game Changer"


def test_total_ignores_cards_without_price():
    items = shopping_list({"robo": ["Mentor of the Meek", "Caesar"]}, MAYBE, {})
    assert total_usd(items) == 4.72


def test_search_links_encode_card_name():
    links = search_links("Teferi's Protection")
    assert links["Yellow Rabbit"] == "https://yellowrabbit.mx/search?q=Teferi%27s+Protection"
    assert links["TCG Wolf"] == "https://www.tcgwolf.com/buscar?q=Teferi%27s+Protection"
