"""Ayudantes compartidos por las pruebas."""

from taller.sources.archidekt import DeckCard
from taller.sources.scryfall import Card


def make_entry(name, type_line="Artifact", text="", tags=None, cmc=2, category="Plan Cards",
               quantity=1, produced=None, identity=None, game_changer=False):
    # Arma la pareja (DeckCard, Card) con valores por defecto razonables.
    deck_card = DeckCard(name=name, quantity=quantity, scryfall_id="x", oracle_id=name,
                         category=category, tags=tags or [])
    card = Card(oracle_id=name, name=name, layout="normal", mana_cost="", cmc=cmc,
                type_line=type_line, oracle_text=text, colors=[], color_identity=identity or [],
                produced_mana=produced or [], keywords=[], game_changer=game_changer,
                price_usd=None, edhrec_rank=None)
    return deck_card, card
