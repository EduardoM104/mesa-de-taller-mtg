"""Tiendas mexicanas: ligas de búsqueda para revisar precios a mano.

TCG Wolf protege sus páginas con un reto de Cloudflare y prohíbe /api/ en
robots.txt, así que no se automatiza (misma regla que Moxfield). Yellow
Rabbit se automatizará por su canal oficial (UCP) en un paso aparte.
"""

from urllib.parse import quote_plus

SEARCH_URLS = {
    "Yellow Rabbit": "https://yellowrabbit.mx/search?q={query}",
    "TCG Wolf": "https://www.tcgwolf.com/buscar?q={query}",
}


def search_links(card_name: str) -> dict[str, str]:
    """Liga de búsqueda de la carta en cada tienda: {"TCG Wolf": "https://..."}."""
    query = quote_plus(card_name)
    return {store: url.format(query=query) for store, url in SEARCH_URLS.items()}
