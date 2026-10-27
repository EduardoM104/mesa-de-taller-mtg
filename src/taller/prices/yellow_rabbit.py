"""Yellow Rabbit: precios en MXN por su canal oficial para agentes (UCP).

La tienda pide que los agentes se identifiquen con un perfil público
(un JSON publicado en internet). Su dirección va en config.toml, en
[tiendas] perfil_ucp. Solo se usa la búsqueda del catálogo: nada de
carritos ni compras.
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import date

import httpx

from taller.sources.cache import CACHE_DIR, USER_AGENT, cache_path

MCP_URL = "https://yellowrabbit.mx/api/ucp/mcp"
PAUSE_SECONDS = 1  # espera entre consultas a la tienda
# Condiciones que aceptamos: cartas para jugar, no la más cara.
CONDITIONS = ("Near Mint", "Lightly Played")


@dataclass
class Offer:
    """La copia más barata disponible de una carta en la tienda."""

    title: str  # ej. "Mentor of the Meek [Innistrad Remastered]"
    condition: str  # ej. "Near Mint Foil"
    price_mxn: float
    url: str


def best_offers(card_names: list[str], profile_url: str, refresh: bool = False) -> dict[str, Offer | None]:
    """Para cada carta, su oferta más barata en stock (None si no hay)."""
    return {name: best_offer(name, search(name, profile_url, refresh)) for name in card_names}


def search(card_name: str, profile_url: str, refresh: bool = False) -> list[dict]:
    """Busca la carta en el catálogo (o lee la copia de hoy) y devuelve los productos."""
    path = cache_path("yellowrabbit", cache_key(card_name), date.today(), CACHE_DIR)
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))

    time.sleep(PAUSE_SECONDS)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/event-stream"}
    response = httpx.post(MCP_URL, json=request_body(card_name, profile_url), headers=headers, timeout=30)
    response.raise_for_status()
    products = parse_products(response.json())

    # Solo se guardan respuestas buenas: un error no debe quedarse todo el día en caché.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(products, ensure_ascii=False), encoding="utf-8")
    return products


def request_body(card_name: str, profile_url: str) -> dict:
    """Llamada MCP a search_catalog, identificándonos con el perfil."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_catalog",
            "arguments": {
                "meta": {"ucp-agent": {"profile": profile_url}},
                # Entre comillas, la búsqueda trae solo esa carta y no otras parecidas.
                "catalog": {"query": f'"{card_name}"', "context": {"address_country": "MX", "currency": "MXN"}},
            },
        },
    }


def parse_products(raw: dict) -> list[dict]:
    """Saca la lista de productos; si la tienda respondió con error, lo avisa."""
    if "error" in raw:
        raise httpx.HTTPError(f"Yellow Rabbit respondió con error: {raw['error'].get('message')}")
    result = raw["result"]
    if result.get("isError"):
        raise httpx.HTTPError("Yellow Rabbit no pudo hacer la búsqueda")
    return result["structuredContent"]["products"]


def best_offer(card_name: str, products: list[dict]) -> Offer | None:
    """La variante más barata, en stock y en buena condición, de esa carta exacta."""
    offers = []
    for product in products:
        if not same_card(product["title"], card_name):
            continue
        for variant in product["variants"]:
            if variant["availability"]["available"] and variant["title"].startswith(CONDITIONS):
                offers.append(Offer(
                    title=product["title"],
                    condition=variant["title"],
                    price_mxn=variant["price"]["amount"] / 100,  # viene en centavos
                    url=product["url"],
                ))
    return min(offers, key=lambda offer: offer.price_mxn, default=None)


def same_card(product_title: str, card_name: str) -> bool:
    """¿El producto es esa carta? Quita el set "[...]" y variantes como "(Retro Frame)".

    Acepta también el nombre alterno de colaboraciones:
    "T'Challa's Protection - Teferi's Protection" es Teferi's Protection.
    """
    base = re.sub(r"\s*[\[(].*?[\])]", "", product_title).strip().lower()
    base = base.split(" - ")[-1]
    wanted = card_name.lower()
    front_face = wanted.split(" // ")[0]
    return base in (wanted, front_face)


def cache_key(card_name: str) -> str:
    """Nombre seguro para el archivo de caché: "Teferi's Protection" → "teferi-s-protection"."""
    return "-".join(re.findall(r"[a-z0-9]+", card_name.lower()))
