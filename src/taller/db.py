"""Base de datos local en SQLite: data/taller.db (no se versiona)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "taller.db"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Abre la base de datos, creando la carpeta si hace falta."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    # Permite leer columnas por nombre: row["name"] en lugar de row[0].
    connection.row_factory = sqlite3.Row
    return connection
