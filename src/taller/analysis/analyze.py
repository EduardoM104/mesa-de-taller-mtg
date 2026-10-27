"""Junta todas las piezas del análisis de un mazo en un solo objeto.

Orden: perfil → Archidekt → Scryfall → roles, maná y bracket → Spellbook → colección.
Si Spellbook falla, el análisis sigue sin combos (regla de CLAUDE.md:
si una fuente falla, el resto debe seguir funcionando).
"""

import re
from dataclasses import dataclass, field

import httpx

from taller.analysis import bracket, mana
from taller.analysis.collection import Owned, fitting_entries
from taller.analysis.pairing import Entry, pair_cards
from taller.analysis.roles import REFERENCES, group_by_role, references_for
from taller.collection.store import collection_info, owned_by_oracle
from taller.config import DEFAULT_EXCHANGE_RATE, exchange_rate
from taller.profiles import DeckProfile
from taller.sources.archidekt import Deck, fetch_deck
from taller.sources.scryfall import cards_date, get_cards, update_cards
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
    # Rangos por rol: los generales, o los del perfil si los define.
    references: dict[str, tuple[int, int]] = field(default_factory=lambda: dict(REFERENCES))
    # Colección: dónde está cada carta que tienes, y las que caben en el mazo sin estar en él.
    owned: Owned = field(default_factory=dict)
    collection_entries: list[Entry] = field(default_factory=list)
    collection: dict | None = None  # total, archivo y fecha; None si no hay colección
    # Precios: tipo de cambio de config.toml y fecha de los precios de Scryfall.
    exchange_rate: float = DEFAULT_EXCHANGE_RATE
    prices_date: str | None = None
    # Ofertas de Yellow Rabbit para la lista de compra; None si no se consultó.
    store_offers: dict | None = None
    store_note: str = ""  # por qué no hay precios de tienda, si no los hay


def analyze(profile: DeckProfile, refresh: bool = False) -> DeckAnalysis:
    """Analiza el mazo del perfil y devuelve un DeckAnalysis.

    Con refresh=True se vuelve a descargar el mazo de Archidekt.
    """
    if profile.archidekt_id is None:
        raise ValueError(f"El perfil '{profile.slug}' no tiene archidekt_id")

    update_cards()
    deck = fetch_deck(profile.archidekt_id, refresh=refresh)
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
    owned = owned_by_oracle()
    in_deck = set(all_ids)
    collection_entries = fitting_entries(get_cards(list(owned)), identity, in_deck) if owned else []
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
        references=references_for(profile.referencias),
        owned=owned,
        collection_entries=collection_entries,
        collection=collection_info(),
        exchange_rate=exchange_rate(),
        prices_date=cards_date(),
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
