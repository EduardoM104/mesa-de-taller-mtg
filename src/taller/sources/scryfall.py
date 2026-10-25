"""Scryfall: datos de cartas a partir del bulk data diario "Oracle Cards".

El archivo trae una carta por cada oracle_id (una por carta, sin importar la
edición). Se descarga máximo una vez al día y se guarda en la tabla `cards`
de SQLite, solo con los campos que usa el análisis.
"""

import gzip
import json
from datetime import date
from pathlib import Path

import httpx
from pydantic import BaseModel

from taller.db import DB_PATH, connect
from taller.sources.cache import CACHE_DIR, USER_AGENT, get_json

BULK_INFO_URL = "https://api.scryfall.com/bulk-data/oracle-cards"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}


class Card(BaseModel):
    """Una carta con los datos que necesita el análisis."""

    oracle_id: str
    name: str
    layout: str
    mana_cost: str
    cmc: float
    type_line: str
    oracle_text: str
    colors: list[str]
    color_identity: list[str]
    produced_mana: list[str]
    keywords: list[str]
    game_changer: bool
    price_usd: float | None
    edhrec_rank: int | None


# ---------- Descarga ----------


def download_bulk(cache_dir: Path = CACHE_DIR) -> Path:
    """Descarga el bulk de hoy si no existe y devuelve su ruta."""
    path = cache_dir / "scryfall" / f"oracle-cards-{date.today().isoformat()}.jsonl.gz"
    if path.exists():
        return path

    info = get_json(BULK_INFO_URL, source="scryfall", key="bulk-oracle-cards", cache_dir=cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Se descarga a un archivo temporal y se renombra al final: si la descarga
    # se corta, no queda un archivo a medias con el nombre bueno.
    partial = path.with_suffix(".part")
    with httpx.stream("GET", info["jsonl_download_uri"], headers=HEADERS, timeout=120) as response:
        response.raise_for_status()
        with partial.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
    partial.rename(path)
    return path


# ---------- Conversión ----------


def to_card(raw: dict) -> Card:
    """Convierte una carta cruda de Scryfall en un Card.

    Las cartas de dos caras (modal_dfc, transform, etc.) guardan el costo y
    el texto en `card_faces`; aquí se juntan en un solo valor.
    """
    faces = raw.get("card_faces") or []
    mana_cost = raw.get("mana_cost") or (faces[0].get("mana_cost", "") if faces else "")
    if faces and not raw.get("oracle_text"):
        oracle_text = "\n//\n".join(face.get("oracle_text", "") for face in faces)
    else:
        oracle_text = raw.get("oracle_text", "")

    price = raw.get("prices", {}).get("usd")
    return Card(
        oracle_id=raw["oracle_id"],
        name=raw["name"],
        layout=raw["layout"],
        mana_cost=mana_cost,
        cmc=raw.get("cmc", 0),
        type_line=raw.get("type_line", ""),
        oracle_text=oracle_text,
        colors=raw.get("colors") or [],
        color_identity=raw.get("color_identity") or [],
        produced_mana=raw.get("produced_mana") or [],
        keywords=raw.get("keywords") or [],
        game_changer=raw.get("game_changer", False),
        price_usd=float(price) if price else None,
        edhrec_rank=raw.get("edhrec_rank"),
    )


# ---------- Base de datos ----------

# Las listas (colores, keywords...) se guardan como texto JSON.
LIST_FIELDS = {"colors", "color_identity", "produced_mana", "keywords"}

CREATE_TABLE = """
CREATE TABLE cards (
    oracle_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    layout TEXT, mana_cost TEXT, cmc REAL, type_line TEXT, oracle_text TEXT,
    colors TEXT, color_identity TEXT, produced_mana TEXT, keywords TEXT,
    game_changer INTEGER, price_usd REAL, edhrec_rank INTEGER
)
"""

# Tabla pequeña de datos sueltos, como la fecha de la última carga.
CREATE_META = "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"


def build_card_table(bulk_path: Path, db_path: Path = DB_PATH) -> int:
    """Reemplaza la tabla `cards` con el contenido del bulk. Devuelve cuántas cartas cargó."""
    connection = connect(db_path)
    with connection:  # todo o nada: si algo falla, no queda la tabla a medias
        connection.execute("DROP TABLE IF EXISTS cards")
        connection.execute(CREATE_TABLE)
        count = 0
        with gzip.open(bulk_path, "rt", encoding="utf-8") as file:
            for line in file:
                raw = json.loads(line)
                if "oracle_id" not in raw:  # algunas cartas especiales no tienen
                    continue
                insert_card(connection, to_card(raw))
                count += 1
        # Anotamos la fecha de carga para no repetirla el mismo día.
        connection.execute(CREATE_META)
        connection.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('cards_date', ?)",
            (date.today().isoformat(),),
        )
    connection.close()
    return count


def cards_date(db_path: Path = DB_PATH) -> str | None:
    """Fecha (AAAA-MM-DD) de la última carga de cartas, o None si nunca se ha hecho."""
    connection = connect(db_path)
    connection.execute(CREATE_META)
    row = connection.execute("SELECT value FROM meta WHERE key = 'cards_date'").fetchone()
    connection.close()
    return row["value"] if row else None


def update_cards(db_path: Path = DB_PATH) -> None:
    """Descarga el bulk y recarga la tabla, solo si no se ha hecho hoy."""
    if cards_date(db_path) == date.today().isoformat():
        return
    build_card_table(download_bulk(), db_path)


def insert_card(connection, card: Card) -> None:
    """Inserta una carta en la tabla `cards`."""
    row = card.model_dump()
    for field in LIST_FIELDS:
        row[field] = json.dumps(row[field])
    columns = ", ".join(row)
    placeholders = ", ".join(f":{name}" for name in row)
    connection.execute(f"INSERT OR REPLACE INTO cards ({columns}) VALUES ({placeholders})", row)


def get_cards(oracle_ids: list[str], db_path: Path = DB_PATH) -> dict[str, Card]:
    """Busca cartas por oracle_id. Devuelve {oracle_id: Card}; las que no estén, se omiten."""
    connection = connect(db_path)
    placeholders = ", ".join("?" for _ in oracle_ids)
    rows = connection.execute(
        f"SELECT * FROM cards WHERE oracle_id IN ({placeholders})", oracle_ids
    ).fetchall()
    connection.close()
    return {row["oracle_id"]: row_to_card(row) for row in rows}


def find_cards_by_name(names: list[str], db_path: Path = DB_PATH) -> dict[str, Card]:
    """Busca cartas por nombre, sin importar mayúsculas. Devuelve {nombre en minúsculas: Card}.

    Para cartas de dos caras acepta el nombre completo ("A // B") o solo
    el de la cara frontal ("A"), que es como las exportan algunas páginas.
    """
    connection = connect(db_path)
    found = {}
    for name in names:
        # Primero el nombre exacto: así "Plains" no cae en una carta rara "Plains // Plains".
        row = connection.execute(
            "SELECT * FROM cards WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if row is None:
            row = connection.execute(
                "SELECT * FROM cards WHERE name LIKE ? AND layout NOT IN ('art_series', 'reversible_card')",
                (f"{name} // %",),
            ).fetchone()
        if row is not None:
            found[name.lower()] = row_to_card(row)
    connection.close()
    return found


def row_to_card(row) -> Card:
    """Convierte una fila de SQLite de vuelta en un Card."""
    data = dict(row)
    for field in LIST_FIELDS:
        data[field] = json.loads(data[field])
    return Card.model_validate(data)
