"""Pruebas del reporte con un análisis armado a mano, sin internet."""

from taller.analysis import bracket, mana
from taller.analysis.analyze import DeckAnalysis, target_turn
from taller.analysis.report import has_theme_type, nonland_without_role, render
from taller.analysis.roles import group_by_role
from taller.profiles import DeckProfile
from taller.sources.archidekt import Deck

from helpers import make_entry


def build_analysis(entries, maybe_entries=(), sincronizada=False, combos=None):
    # Ayudante: calcula un DeckAnalysis igual que analyze(), pero con cartas dadas.
    profile = DeckProfile(slug="prueba", nombre="Prueba", estado="armado", bracket=3,
                          ventana_victoria="turno 5", lista_sincronizada=sincronizada,
                          etiquetas_tema=["attack trigger"])
    deck_cards = [deck_card for deck_card, _ in entries]
    deck = Deck(archidekt_id=1, name="Prueba", updated_at="2026-10-25T00:00:00Z",
                commanders=deck_cards[:1], mainboard=deck_cards, maybeboard=[])
    curve = mana.mana_curve(entries)
    identity = mana.deck_identity(entries)
    findings = bracket.bracket_findings(entries)
    return DeckAnalysis(
        profile=profile, deck=deck, entries=entries, maybe_entries=list(maybe_entries), missing=[],
        roles=group_by_role(entries), maybe_roles=group_by_role(list(maybe_entries)),
        lands=mana.land_count(entries), curve=curve, average_cmc=mana.average_cmc(curve),
        identity=identity, sources=mana.color_sources(entries, identity),
        tapped=mana.tapped_lands(entries), findings=findings,
        warnings=bracket.bracket_warnings(findings, 3), combos=combos,
    )


ENTRIES = [
    make_entry("Isshin, Two Heavens as One", type_line="Legendary Creature", cmc=3,
               category="Commander", identity=["W", "B", "R"]),
    make_entry("Sol Ring", tags=["adds multiple mana"], cmc=1),
    make_entry("Hero of Bladehold", type_line="Creature", tags=["attack trigger"], cmc=4),
    make_entry("Random Rock", cmc=3),
]


def test_target_turn():
    assert target_turn("turno 5") == 5
    assert target_turn("turno 7-9") == 7
    assert target_turn("") is None


def test_unsynced_list_warns():
    assert "no está confirmada contra el mazo físico" in render(build_analysis(ENTRIES))
    assert "no está confirmada" not in render(build_analysis(ENTRIES, sincronizada=True))


def test_all_sections_present():
    report = render(build_analysis(ENTRIES))
    for number in range(1, 9):
        assert f"## {number}." in report


def test_theme_pieces_are_not_candidates_to_cut():
    # Hero tiene la etiqueta del tema; Random Rock no tiene ni rol ni tema.
    assert nonland_without_role(build_analysis(ENTRIES)) == ["Random Rock"]


def test_maybeboard_fills_missing_role():
    maybe = [make_entry("Mentor of the Meek", type_line="Creature", tags=["repeatable pure draw"])]
    report = render(build_analysis(ENTRIES, maybe_entries=maybe))
    assert "En tu Maybeboard: Mentor of the Meek" in report


def test_missing_spellbook_is_reported():
    report = render(build_analysis(ENTRIES, combos=None))
    assert "Spellbook no respondió" in report


def test_theme_type_matches_creature_subtype():
    assert has_theme_type("Creature — Dragon", ["Dragon"]) is True
    assert has_theme_type("Legendary Creature — Elder Dragon", ["Dragon"]) is True
    assert has_theme_type("Creature — Dragonfly", ["Dragon"]) is False  # palabra completa, no un pedazo


def test_tutors_are_not_candidates_to_cut():
    entries = ENTRIES + [make_entry("Worldly Tutor", type_line="Instant", tags=["tutor-creature"])]
    assert "Worldly Tutor" not in nonland_without_role(build_analysis(entries))


def test_suggestions_show_where_you_have_the_card():
    # Robo está abajo; Mentor está en el Maybeboard y en tu colección, en Orzhov WB.
    maybe = [make_entry("Mentor of the Meek", type_line="Creature", tags=["repeatable pure draw"])]
    analysis = build_analysis(ENTRIES, maybe_entries=maybe)
    analysis.owned = {"Mentor of the Meek": {"Orzhov WB": 1}}
    assert "Mentor of the Meek (la tienes: Orzhov WB)" in render(analysis)


def test_collection_cards_fill_low_roles():
    owned_card = make_entry("Night's Whisper", type_line="Sorcery", text="You draw two cards and you lose 2 life.")
    analysis = build_analysis(ENTRIES)
    analysis.owned = {"Night's Whisper": {"Mono negro": 2}}
    analysis.collection_entries = [owned_card]
    assert "En tu colección (detectadas por texto, revisa que encajen): Night's Whisper (la tienes: Mono negro ×2)" \
        in render(analysis)


def test_header_says_when_collection_is_missing():
    assert "sin importar" in render(build_analysis(ENTRIES))
