"""Foto del análisis en datos simples (JSON) para la página web.

`taller analizar` la guarda junto al reporte Markdown: reports/<slug>-<fecha>.json.
Así la web dibuja barras, curva y tarjetas sin volver a consultar internet.
Las reglas (qué está bajo, qué sugerir) son las mismas del reporte: se reusan sus funciones.
"""

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from taller.analysis.analyze import DeckAnalysis
from taller.analysis.bracket import MAX_GAME_CHANGERS
from taller.analysis.collection import location_text
from taller.analysis.pairing import Entry
from taller.analysis.report import (
    ROLE_TITLES, collection_text, maybe_game_changers, nonland_without_role, roles_below,
    shopping_items, summary, theme_pieces, total_cost_lines, window_section,
)
from taller.analysis.roles import group_by_role
from taller.prices.shopping import total_usd, usd_to_mxn
from taller.prices.stores import search_links

MAX_NEAR_COMBOS = 10


def save_snapshot(analysis: DeckAnalysis, path: Path) -> None:
    """Escribe la foto del análisis como JSON."""
    path.write_text(json.dumps(snapshot(analysis), ensure_ascii=False, indent=1), encoding="utf-8")


def snapshot(analysis: DeckAnalysis) -> dict:
    """Todo lo que la página del mazo necesita, en diccionarios y listas."""
    return {
        "date": date.today().isoformat(),
        "header": header_data(analysis),
        # Las líneas del resumen y la ventana vienen del reporte, en Markdown.
        "summary": [line[2:] for line in summary(analysis) if line.startswith("- ")],
        "roles": roles_data(analysis),
        "mana": mana_data(analysis),
        "bracket": bracket_data(analysis),
        "combos": combos_data(analysis),
        "synergy": synergy_data(analysis),
        "suggestions": suggestions_data(analysis),
        "shopping": shopping_data(analysis),
        "window": [line[2:] for line in window_section(analysis) if line.startswith("- ")],
    }


# ---------- Ayudantes ----------


def card_refs(card_names: list[str], entries: list[Entry], analysis: DeckAnalysis) -> list[dict]:
    """[{"name": ..., "location": "Orzhov WB" o None}] según la colección."""
    oracle_by_name = {deck_card.name: deck_card.oracle_id for deck_card, _ in entries}
    refs = []
    for name in card_names:
        binders = analysis.owned.get(oracle_by_name.get(name))
        refs.append({"name": name, "location": location_text(binders) if binders else None})
    return refs


def role_state(count: int, reference: tuple[int, int] | None) -> str | None:
    """"bajo", "ok", "alto", o None si el rol no tiene referencia."""
    if reference is None:
        return None
    low, high = reference
    return "bajo" if count < low else "alto" if count > high else "ok"


# ---------- Secciones ----------


def header_data(analysis: DeckAnalysis) -> dict:
    profile, deck = analysis.profile, analysis.deck
    return {
        "nombre": profile.nombre,
        "comandante": profile.comandante,
        "bracket": profile.bracket,
        "ventana": profile.ventana_victoria,
        "tema": profile.tema,
        "archidekt_url": f"https://archidekt.com/decks/{deck.archidekt_id}",
        "editado": deck.updated_at[:10],
        "coleccion": collection_text(analysis.collection),
        "sincronizada": profile.lista_sincronizada,
        "cartas": deck.card_count(),
        "faltantes": analysis.missing,
    }


def roles_data(analysis: DeckAnalysis) -> list[dict]:
    rows = []
    for role, title in ROLE_TITLES.items():
        reference = analysis.references.get(role)
        count = len(analysis.roles[role])
        rows.append({
            "key": role, "title": title, "count": count,
            "low": reference[0] if reference else None,
            "high": reference[1] if reference else None,
            "state": role_state(count, reference),
            "cards": analysis.roles[role],
        })
    return rows


def mana_data(analysis: DeckAnalysis) -> dict:
    return {
        "lands": analysis.lands,
        "average": analysis.average_cmc,
        "ramp": len(analysis.roles["ramp"]),
        "curve": [{"label": "7+" if cmc == 7 else str(cmc), "count": count} for cmc, count in analysis.curve.items()],
        "identity": analysis.identity,
        "sources": analysis.sources,
        "tapped_always": analysis.tapped["siempre"],
        "tapped_sometimes": analysis.tapped["a_veces"],
    }


def bracket_data(analysis: DeckAnalysis) -> dict:
    findings = analysis.findings
    limit = MAX_GAME_CHANGERS.get(analysis.profile.bracket or 3)
    two_card = None
    if analysis.combos is not None:
        two_card = sum(1 for combo in analysis.combos["presentes"] if len(combo.cards) == 2)
    return {
        "target": analysis.profile.bracket,
        "game_changers": findings["game_changers"],
        "limit": limit,
        "tutors": findings["tutores"],
        "extra_turns": findings["turnos_extra"],
        "land_destruction": findings["destruccion_tierras"],
        "two_card_combos": two_card,
        "warnings": analysis.warnings,
    }


def combos_data(analysis: DeckAnalysis) -> dict | None:
    """None si Spellbook no respondió."""
    if analysis.combos is None:
        return None
    breaks_bracket = (analysis.profile.bracket or 3) <= 3
    near = sorted(analysis.combos["a_una_carta"], key=lambda combo: combo.popularity, reverse=True)
    return {
        "present": [{"cards": combo.cards, "result": combo.results[0]} for combo in analysis.combos["presentes"]],
        "near_total": len(near),
        "near": [{
            "missing": combo.missing, "cards": combo.cards, "result": combo.results[0],
            "two_card": breaks_bracket and len(combo.cards) == 2,
        } for combo in near[:MAX_NEAR_COMBOS]],
    }


def synergy_data(analysis: DeckAnalysis) -> dict:
    """Piezas del tema, lo que además empuja el plan (sin repetir) y lo que no tiene rol."""
    pieces = theme_pieces(analysis)
    tokens, closers = set(analysis.roles["tokens"]), set(analysis.roles["cierre"])
    others = sorted((tokens | closers) - set(pieces))
    return {
        "criteria": analysis.profile.tipos_tema + analysis.profile.etiquetas_tema,
        "pieces": pieces,
        "tokens": [name for name in others if name in tokens and name not in closers],
        "closers": [name for name in others if name in closers and name not in tokens],
        "both": [name for name in others if name in tokens and name in closers],
        "without_role": nonland_without_role(analysis),
    }


def suggestions_data(analysis: DeckAnalysis) -> list[dict]:
    """Cada sugerencia como tarjeta: tipo, título, detalle y grupos de cartas."""
    return (low_role_cards(analysis) + spare_role_cards(analysis) + game_changer_cards(analysis)
            + review_cards(analysis) + avoid_cards(analysis))


def suggestion(kind: str, title: str, detail: str, groups: list[dict]) -> dict:
    return {"kind": kind, "title": title, "detail": detail, "groups": [g for g in groups if g["cards"]]}


def low_role_cards(analysis: DeckAnalysis) -> list[dict]:
    collection_roles = group_by_role(analysis.collection_entries)
    cards = []
    for role in roles_below(analysis):
        low, high = analysis.references[role]
        maybe = card_refs(analysis.maybe_roles[role], analysis.maybe_entries, analysis)
        owned = card_refs(collection_roles[role], analysis.collection_entries, analysis)
        detail = f"Tienes {len(analysis.roles[role])}; la referencia es {low}–{high}."
        if not maybe and not owned:
            detail += " Nada en tu Maybeboard ni en tu colección cubre este rol."
        cards.append(suggestion("sube", f"Sube {ROLE_TITLES[role].lower()}", detail, [
            {"label": "En tu Maybeboard", "cards": maybe},
            {"label": "En tu colección (detectadas por texto, revisa que encajen)", "cards": owned},
        ]))
    return cards


def spare_role_cards(analysis: DeckAnalysis) -> list[dict]:
    cards = []
    for role, (low, high) in analysis.references.items():
        count = len(analysis.roles[role])
        if count > high:
            cards.append(suggestion("margen", f"{ROLE_TITLES[role]} tiene margen",
                                    f"Tienes {count}; la referencia es {low}–{high}. De aquí puedes liberar espacios.",
                                    [{"label": "Cartas del rol", "cards": card_refs(analysis.roles[role], analysis.entries, analysis)}]))
    return cards


def game_changer_cards(analysis: DeckAnalysis) -> list[dict]:
    limit = MAX_GAME_CHANGERS.get(analysis.profile.bracket or 3)
    used = len(analysis.findings["game_changers"])
    if not limit or used >= limit:
        return []
    maybe = card_refs(maybe_game_changers(analysis), analysis.maybe_entries, analysis)
    return [suggestion("gc", f"Te quedan {limit - used} espacio(s) de Game Changer",
                       f"En bracket {analysis.profile.bracket}; úsalos en consistencia (robo, protección, ramp).",
                       [{"label": "En tu Maybeboard", "cards": maybe}])]


def review_cards(analysis: DeckAnalysis) -> list[dict]:
    without_role = nonland_without_role(analysis)
    if not without_role:
        return []
    return [suggestion("revisa", "Revisa si empujan el plan",
                       "No se les detectó rol ni son piezas del tema: son candidatas a salir.",
                       [{"label": "Cartas", "cards": card_refs(without_role, analysis.entries, analysis)}])]


def avoid_cards(analysis: DeckAnalysis) -> list[dict]:
    if not analysis.combos or (analysis.profile.bracket or 3) > 3:
        return []
    risky = sorted({name for combo in analysis.combos["a_una_carta"] if len(combo.cards) == 2 for name in combo.missing})
    if not risky:
        return []
    return [suggestion("evita", "Evita agregar",
                       f"Completarían un combo de dos cartas y sacarían el mazo de bracket {analysis.profile.bracket}.",
                       [{"label": "Cartas", "cards": [{"name": name, "location": None} for name in risky]}])]


def shopping_data(analysis: DeckAnalysis) -> dict:
    rate, offers = analysis.exchange_rate, analysis.store_offers
    items = shopping_items(analysis)
    found = [offers[item.name] for item in items if offers and offers.get(item.name)]
    store_total = sum(offer.price_mxn for offer in found) if found else None
    reference_total = usd_to_mxn(total_usd(items), rate)
    return {
        "rate": rate,
        "prices_date": analysis.prices_date,
        "note": analysis.store_note,
        "checked": offers is not None,
        "items": [shopping_item(item, offers, rate) for item in items],
        "reference_total": reference_total,
        "store_total": store_total,
        "without_stock": len(items) - len(found) if offers is not None else 0,
        # Las líneas de envío vienen del reporte, en Markdown.
        "shipping": [line[2:] for line in total_cost_lines(analysis, store_total, reference_total) if line.startswith("- ")],
    }


def shopping_item(item, offers: dict | None, rate: float) -> dict:
    offer = offers.get(item.name) if offers else None
    return {
        "name": item.name,
        "reason": item.reason,
        "reference_mxn": usd_to_mxn(item.price_usd, rate) if item.price_usd is not None else None,
        "price_usd": item.price_usd,
        "offer": offer_data(offer) if offer else None,
        "links": search_links(item.name),
    }


def offer_data(offer) -> dict:
    data = asdict(offer)
    data["set"] = offer.title[offer.title.find("[") + 1:-1] if "[" in offer.title else ""
    data["condition"] = offer.condition.replace("Near Mint", "NM").replace("Lightly Played", "LP")
    return data
