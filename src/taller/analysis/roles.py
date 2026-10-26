"""Roles de las cartas: ramp, robo, removal, wipes, protección, tokens y cierre.

Fuente principal: las etiquetas de Scryfall Tagger que trae Archidekt.
Respaldo: reglas sobre el texto de la carta, para mazos sin etiquetas
(por ejemplo, una lista pegada de Moxfield). Una carta puede tener varios
roles. Las tierras no llevan rol: se analizan en la base de maná.
"""

import re

from taller.analysis.pairing import Entry, is_land

# Por cada rol:
#   tags: etiquetas que cuentan tal cual
#   prefixes: etiquetas que cuentan si empiezan así (ej. "removal-creature")
#   text: expresión regular para el respaldo sobre el texto de la carta
ROLES = {
    "ramp": {
        "tags": {
            "ramp", "land ramp", "mana dork", "adds multiple mana", "ritual", "cost reducer", "extra land",
            "utility mana rock", "repeatable treasures",
        },
        "prefixes": ("mana rock",),
        "text": r"\badd \{|search your library for .*land",
    },
    "robo": {
        "tags": {
            "draw engine", "pure draw", "repeatable pure draw", "burst draw", "card advantage", "wheel",
            "impulsive draw", "repeatable impulsive draw", "long term impulsive draw",
        },
        "prefixes": (),
        "text": r"\bdraws? (a|two|three|x|\d+) cards?",
    },
    "removal": {
        # Incluye counterspells: también son interacción.
        "tags": {"spot removal", "repeatable removal", "multi removal"},
        "prefixes": ("removal-", "counterspell"),
        "text": r"(destroy|exile) target|counter target|damage to (any target|target creature)",
    },
    "wipes": {
        "tags": {"sweeper", "board wipe"},  # ojo: "sweeper-graveyard" no es un wipe
        "prefixes": (),
        "text": r"(destroy|exile) all (creatures|nonland permanents)",
    },
    "protección": {
        "tags": {"gives indestructible", "gives hexproof", "gives protection", "gives player protection", "phasing"},
        "prefixes": ("protects-all", "protects-creature"),
        "text": r"(gain|have) (hexproof|indestructible|protection)",
    },
    "tokens": {
        "tags": {"repeatable creature tokens", "repeatable token generator", "multiple bodies", "token doubler", "token replacer", "copy-token"},
        "prefixes": (),
        "text": r"create .*tokens?",
    },
    "cierre": {
        "tags": {"anthem", "keyword anthem", "power boost to all", "extra combat phase", "group slug", "drain life"},
        "prefixes": (),
        "text": r"creatures you control get \+|additional combat|each opponent loses",
    },
}

# Rangos habituales en Commander para un mazo de 100 cartas: (mínimo, máximo).
# Son una referencia, no una regla: el perfil de cada mazo puede justificar otra cosa.
REFERENCES = {
    "ramp": (10, 12),
    "robo": (10, 12),
    "removal": (8, 10),
    "wipes": (2, 4),
    "protección": (3, 6),
}


def references_for(overrides: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int]]:
    """Rangos de referencia del mazo: los generales, cambiados por los del perfil."""
    unknown = set(overrides) - set(REFERENCES)
    if unknown:
        raise ValueError(f"Roles desconocidos en referencias: {', '.join(sorted(unknown))}")
    return {**REFERENCES, **overrides}


def matches_tags(tags: list[str], rule: dict) -> bool:
    """¿Alguna etiqueta de la carta corresponde a este rol?"""
    for tag in tags:
        if tag in rule["tags"] or tag.startswith(rule["prefixes"]):
            return True
    return False


def card_roles(entry: Entry) -> list[str]:
    """Roles de una carta. Usa etiquetas si las tiene; si no, el texto."""
    deck_card, card = entry
    if is_land(card):
        return []
    if deck_card.tags:
        return [role for role, rule in ROLES.items() if matches_tags(deck_card.tags, rule)]
    return [role for role, rule in ROLES.items() if re.search(rule["text"], card.oracle_text, re.IGNORECASE)]


def group_by_role(entries: list[Entry]) -> dict[str, list[str]]:
    """Devuelve {rol: [nombres de cartas]} para todo el mazo."""
    groups = {role: [] for role in ROLES}
    for entry in entries:
        for role in card_roles(entry):
            groups[role].append(entry[0].name)
    return groups
