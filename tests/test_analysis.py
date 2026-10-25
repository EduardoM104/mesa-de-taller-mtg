"""Pruebas del análisis (roles, maná, bracket) con cartas armadas a mano."""

from taller.analysis import bracket, mana
from taller.analysis.roles import card_roles
from taller.sources.archidekt import DeckCard
from taller.sources.scryfall import Card


def make_entry(name, type_line="Artifact", text="", tags=None, cmc=2, category="Plan Cards",
               quantity=1, produced=None, identity=None, game_changer=False):
    # Ayudante: arma la pareja (DeckCard, Card) con valores por defecto razonables.
    deck_card = DeckCard(name=name, quantity=quantity, scryfall_id="x", oracle_id=name,
                         category=category, tags=tags or [])
    card = Card(oracle_id=name, name=name, layout="normal", mana_cost="", cmc=cmc,
                type_line=type_line, oracle_text=text, colors=[], color_identity=identity or [],
                produced_mana=produced or [], keywords=[], game_changer=game_changer,
                price_usd=None, edhrec_rank=None)
    return deck_card, card


# ---------- Roles ----------


def test_roles_from_tags():
    signet = make_entry("Boros Signet", tags=["mana rock", "activated ability"])
    assert card_roles(signet) == ["ramp"]


def test_roles_fallback_to_text_without_tags():
    # Sin etiquetas (ej. mazo de Moxfield), se usa el texto.
    divination = make_entry("Divination", type_line="Sorcery", text="Draw two cards.")
    assert card_roles(divination) == ["robo"]


def test_lands_have_no_roles():
    triome = make_entry("Savai Triome", type_line="Land — Mountain Plains Forest", tags=["pure draw"])
    assert card_roles(triome) == []


def test_graveyard_sweeper_is_not_a_wipe():
    kaya = make_entry("Kaya", tags=["sweeper-graveyard", "token doubler"])
    assert card_roles(kaya) == ["tokens"]


# ---------- Maná ----------


def test_curve_skips_lands_and_commander():
    entries = [
        make_entry("Isshin", cmc=3, category="Commander"),
        make_entry("Mountain", type_line="Basic Land — Mountain", cmc=0, quantity=5),
        make_entry("Sol Ring", cmc=1),
        make_entry("Big Thing", cmc=9),
    ]
    curve = mana.mana_curve(entries)
    assert curve[1] == 1 and curve[7] == 1  # 9 cae en la cubeta "7+"
    assert sum(curve.values()) == 2


def test_average_cmc():
    # Dos cartas de 1 y dos de 3: (1 + 1 + 3 + 3) / 4 = 2.0
    assert mana.average_cmc({1: 2, 3: 2}) == 2.0


def test_average_cmc_of_empty_curve_is_zero():
    # Sin cartas no se puede dividir entre cero: la función devuelve 0.0.
    assert mana.average_cmc({}) == 0.0


def test_color_sources_respect_identity():
    tower = make_entry("Command Tower", type_line="Land", produced=["W", "U", "B", "R", "G"])
    assert mana.color_sources([tower], ["W", "B", "R"]) == {"W": 1, "B": 1, "R": 1}


def test_tapped_lands_always_vs_sometimes():
    triome = make_entry("Triome", type_line="Land", text="This land enters tapped.")
    shock = make_entry("Shock", type_line="Land",
                       text="As this land enters, you may pay 2 life. If you don't, it enters tapped.")
    assert mana.tapped_lands([triome, shock]) == {"siempre": ["Triome"], "a_veces": ["Shock"]}


# ---------- Bracket ----------


def test_tutored_by_name_is_not_a_tutor():
    tower = make_entry("Command Tower", type_line="Land", tags=["tutored by name"])
    assert bracket.is_tutor(tower) is False


def test_searching_for_a_land_is_not_a_tutor():
    cultivate = make_entry("Cultivate", type_line="Sorcery",
                           text="Search your library for up to two basic land cards.")
    assert bracket.is_tutor(cultivate) is False


def test_too_many_game_changers_warns():
    entries = [make_entry(f"GC {n}", game_changer=True) for n in range(4)]
    findings = bracket.bracket_findings(entries)
    assert bracket.bracket_warnings(findings, target=3) == [
        "4 Game Changers; bracket 3 permite máximo 3."
    ]
