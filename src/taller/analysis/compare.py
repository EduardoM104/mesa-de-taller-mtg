"""Compara un mazo propio (ya analizado) contra un mazo ajeno.

Las listas en texto no traen etiquetas de Scryfall Tagger. Para que la
comparación sea justa, a las cartas ajenas que también están en tu mazo o
Maybeboard se les copian las etiquetas que ya conocemos; el resto se
clasifica con las reglas de texto.
"""

from dataclasses import dataclass

from taller.analysis import mana
from taller.analysis.analyze import DeckAnalysis
from taller.analysis.pairing import Entry, pair_cards
from taller.analysis.roles import REFERENCES, group_by_role
from taller.sources.archidekt import Deck, DeckCard
from taller.sources.scryfall import get_cards


@dataclass
class Comparison:
    """Todo lo que necesita el reporte de comparación."""

    own: DeckAnalysis
    other: Deck
    other_entries: list[Entry]
    other_roles: dict[str, list[str]]
    other_lands: int
    other_average_cmc: float
    unresolved: list[str]  # nombres de su lista que no se encontraron
    by_text: int  # cuántas de sus cartas se clasificaron solo por texto
    shared: int  # cartas en común, sin contar básicas
    only_mine: list[str]
    only_theirs: list[str]
    fills_gaps: dict[str, list[str]]  # rol bajo en tu mazo → sus cartas que lo cubren


def compare(own: DeckAnalysis, other: Deck, unresolved: list[str]) -> Comparison:
    """Compara tu mazo analizado contra el mazo ajeno."""
    known_tags = {deck_card.oracle_id: deck_card.tags for deck_card, _ in own.entries + own.maybe_entries}
    other_cards = [with_known_tags(deck_card, known_tags) for deck_card in other.mainboard]
    other_entries, missing = pair_cards(other_cards, get_cards([c.oracle_id for c in other_cards]))
    other_roles = group_by_role(other_entries)

    mine = {deck_card.oracle_id: deck_card.name for deck_card, card in own.entries if not is_basic(card)}
    theirs = {deck_card.oracle_id: deck_card.name for deck_card, card in other_entries if not is_basic(card)}
    only_theirs = sorted(name for oracle_id, name in theirs.items() if oracle_id not in mine)

    curve = mana.mana_curve(other_entries)
    return Comparison(
        own=own,
        other=other,
        other_entries=other_entries,
        other_roles=other_roles,
        other_lands=mana.land_count(other_entries),
        other_average_cmc=mana.average_cmc(curve),
        unresolved=unresolved + missing,
        by_text=sum(1 for deck_card, _ in other_entries if not deck_card.tags),
        shared=len(mine.keys() & theirs.keys()),
        only_mine=sorted(name for oracle_id, name in mine.items() if oracle_id not in theirs),
        only_theirs=only_theirs,
        fills_gaps=gaps_they_fill(own, other_roles, set(only_theirs)),
    )


def with_known_tags(deck_card: DeckCard, known_tags: dict[str, list[str]]) -> DeckCard:
    """Si la carta no trae etiquetas pero ya las conocemos, se las copia."""
    if deck_card.tags or deck_card.oracle_id not in known_tags:
        return deck_card
    return deck_card.model_copy(update={"tags": known_tags[deck_card.oracle_id]})


def is_basic(card) -> bool:
    """Las tierras básicas no se comparan: solo cambian las cantidades."""
    return card.type_line.startswith("Basic Land")


def gaps_they_fill(own: DeckAnalysis, other_roles: dict[str, list[str]], only_theirs: set[str]) -> dict[str, list[str]]:
    """Para cada rol en el que tu mazo está abajo, sus cartas (que tú no tienes) que lo cubren."""
    gaps = {}
    for role, (low, _) in REFERENCES.items():
        if len(own.roles[role]) < low:
            gaps[role] = [name for name in other_roles[role] if name in only_theirs]
    return gaps
