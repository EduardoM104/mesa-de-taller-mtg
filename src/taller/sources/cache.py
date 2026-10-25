"""Caché con fecha para respuestas de APIs.

Cada respuesta se guarda como <clave>-<AAAA-MM-DD>.json. Si ya existe la
copia de hoy, se usa esa y no se vuelve a llamar a la fuente.
"""

import json
from datetime import date
from pathlib import Path

import httpx

# Raíz de la caché: data/cache/ (no se versiona).
CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache"

# Nos identificamos ante cada fuente, como pide CLAUDE.md.
USER_AGENT = "mesa-de-taller-mtg/0.1 (uso personal)"


def cache_path(source: str, key: str, day: date, cache_dir: Path = CACHE_DIR) -> Path:
    """Ruta del archivo de caché para una fuente, una clave y un día."""
    return cache_dir / source / f"{key}-{day.isoformat()}.json"


def get_json(url: str, source: str, key: str, cache_dir: Path = CACHE_DIR) -> dict:
    """Devuelve el JSON de `url` (GET), usando la copia de hoy si ya existe."""
    return fetch_cached("GET", url, None, source, key, cache_dir)


def post_json(url: str, body: dict, source: str, key: str, cache_dir: Path = CACHE_DIR) -> dict:
    """Envía `body` a `url` (POST) y devuelve el JSON, usando la copia de hoy si ya existe."""
    return fetch_cached("POST", url, body, source, key, cache_dir)


def fetch_cached(method: str, url: str, body: dict | None, source: str, key: str, cache_dir: Path) -> dict:
    """Parte común de get_json y post_json."""
    path = cache_path(source, key, date.today(), cache_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    response = httpx.request(method, url, json=body, headers=headers, timeout=60)
    response.raise_for_status()  # si la fuente responde con error, avisamos
    data = response.json()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
