"""La colección guardada en SQLite: tabla `collection` de data/taller.db."""

from datetime import datetime
from pathlib import Path

from taller.collection.manabox import CollectionCard
from taller.db import DB_PATH, connect

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS collection (
    name TEXT NOT NULL,
    oracle_id TEXT,
    scryfall_id TEXT NOT NULL,
    set_code TEXT,
    collector_number TEXT,
    finish TEXT,
    language TEXT,
    quantity INTEGER NOT NULL,
    binder TEXT NOT NULL,
    binder_type TEXT
)
"""

CREATE_META = "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"


def replace_collection(cards: list[CollectionCard], oracle_ids: dict[str, str],
                       source_name: str, db_path: Path = DB_PATH) -> None:
    """Borra la colección guardada y carga `cards` en su lugar.

    oracle_ids va de nombre en minúsculas a oracle_id; las cartas que no
    aparecen ahí se guardan con oracle_id vacío.
    """
    connection = connect(db_path)
    with connection:  # todo o nada: si algo falla, queda la colección anterior
        connection.execute(CREATE_TABLE)
        connection.execute("DELETE FROM collection")
        for card in cards:
            insert_card(connection, card, oracle_ids.get(card.name.lower()))
        connection.execute(CREATE_META)
        connection.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('collection_source', ?)", (source_name,)
        )
        connection.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('collection_imported_at', ?)",
            (datetime.now().isoformat(timespec="seconds"),),
        )
    connection.close()


def insert_card(connection, card: CollectionCard, oracle_id: str | None) -> None:
    connection.execute(
        "INSERT INTO collection VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (card.name, oracle_id, card.scryfall_id, card.set_code, card.collector_number,
         card.finish, card.language, card.quantity, card.binder, card.binder_type),
    )


def collection_size(db_path: Path = DB_PATH) -> int:
    """Total de cartas guardadas, contando copias."""
    connection = connect(db_path)
    connection.execute(CREATE_TABLE)
    row = connection.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM collection").fetchone()
    connection.close()
    return row["total"]


def owned_by_oracle(db_path: Path = DB_PATH) -> dict[str, dict[str, int]]:
    """Qué cartas tienes y dónde: {oracle_id: {binder: copias}}.

    Se ignoran los binders de tipo "list": en ManaBox son listas de deseos,
    no cartas que tengas.
    """
    connection = connect(db_path)
    connection.execute(CREATE_TABLE)
    rows = connection.execute(
        "SELECT oracle_id, binder, SUM(quantity) AS copies FROM collection "
        "WHERE oracle_id IS NOT NULL AND binder_type != 'list' "
        "GROUP BY oracle_id, binder ORDER BY binder"
    ).fetchall()
    connection.close()
    owned = {}
    for row in rows:
        owned.setdefault(row["oracle_id"], {})[row["binder"]] = row["copies"]
    return owned


def collection_info(db_path: Path = DB_PATH) -> dict | None:
    """Total de cartas, archivo y fecha de la última importación; None si no hay colección."""
    total = collection_size(db_path)
    if total == 0:
        return None
    connection = connect(db_path)
    rows = connection.execute("SELECT key, value FROM meta WHERE key LIKE 'collection_%'").fetchall()
    connection.close()
    meta = {row["key"]: row["value"] for row in rows}
    return {"total": total, "source": meta.get("collection_source"),
            "imported_at": meta.get("collection_imported_at")}
