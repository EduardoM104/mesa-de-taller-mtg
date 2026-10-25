"""Junta todas las piezas del análisis de un mazo en un solo objeto.

Orden: perfil → Archidekt → Scryfall → roles, maná y bracket → Spellbook.
Si Spellbook falla, el análisis sigue sin combos (regla de CLAUDE.md:
si una fuente falla, el resto debe seguir funcionando).
"""

import re
from dataclasses import dataclass

import httpx

from taller.analysis import bracket, mana
from taller.analysis.pairing import Entry, pair_cards
from taller.analysis.roles import group_by_role
from taller.profiles import DeckProfile
from taller.sources.archidekt import Deck, fetch_deck
from taller.sources.scryfall import get_cards, update_cards
from taller.sources.spellbook import Combo, fetch_combos


@dataclass
class DeckAnalysis:
    """Todo lo que necesita el reporte de un mazo."""

    profile: DeckProfile
    deck: Deck
    entries: list[Entry]  # mazo principal con datos de Scryfall
    maybe_entries: list[Entry]  # Maybeboard con datos de Scryfall
    missing: list[str]  # cartas que no se encontraron en Scryfall
    roles: dict[str, list[str]]
    maybe_roles: dict[str, list[str]]
    lands: int
    curve: dict[int, int]
    average_cmc: float
    identity: list[str]
    sources: dict[str, int]
    tapped: dict[str, list[str]]
    findings: dict[str, list[str]]
    warnings: list[str]
    combos: dict[str, list[Combo]] | None  # None si Spellbook no respondió


def analyze(profile: DeckProfile) -> DeckAnalysis:
    """Analiza el mazo del perfil y devuelve un DeckAnalysis."""
    if profile.archidekt_id is None:
        raise ValueError(f"El perfil '{profile.slug}' no tiene archidekt_id")

    update_cards()
    deck = fetch_deck(profile.archidekt_id)
    all_ids = [card.oracle_id for card in deck.mainboard + deck.maybeboard]
    cards = get_cards(all_ids)
    entries, missing = pair_cards(deck.mainboard, cards)
    maybe_entries, _ = pair_cards(deck.maybeboard, cards)

    combos = safe_fetch_combos(deck)
    findings = bracket.bracket_findings(entries)
    warnings = bracket.bracket_warnings(findings, profile.bracket or 3)
    if combos is not None:
        warnings += bracket.combo_warnings(combos["presentes"], profile.bracket or 3)

    curve = mana.mana_curve(entries)
    identity = mana.deck_identity(entries)
    return DeckAnalysis(
        profile=profile,
        deck=deck,
        entries=entries,
        maybe_entries=maybe_entries,
        missing=missing,
        roles=group_by_role(entries),
        maybe_roles=group_by_role(maybe_entries),
        lands=mana.land_count(entries),
        curve=curve,
        average_cmc=mana.average_cmc(curve),
        identity=identity,
        sources=mana.color_sources(entries, identity),
        tapped=mana.tapped_lands(entries),
        findings=findings,
        warnings=warnings,
        combos=combos,
    )


def safe_fetch_combos(deck: Deck) -> dict[str, list[Combo]] | None:
    """Consulta Spellbook; si falla la conexión, devuelve None en lugar de tronar."""
    try:
        return fetch_combos(deck)
    except httpx.HTTPError:
        return None


def target_turn(window: str) -> int | None:
    """Saca el primer número de la ventana: "turno 5" → 5, "turno 7-9" → 7."""
    match = re.search(r"\d+", window)
    return int(match.group()) if match else None
