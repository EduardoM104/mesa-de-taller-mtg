"""Lectura de las exportaciones CSV de ManaBox.

La carpeta de ManaBox es de solo lectura para el taller: aquí solo se
listan archivos y se abren en modo lectura. Nunca escribir, mover ni borrar ahí.
"""

import csv
from collections import Counter
from pathlib import Path

from pydantic import BaseModel


class CollectionCard(BaseModel):
    """Una fila del CSV: una impresión de una carta en un binder."""

    name: str
    scryfall_id: str  # id de la impresión, no el oracle_id
    set_code: str
    collector_number: str
    finish: str  # normal, foil o etched
    language: str
    quantity: int
    binder: str  # el binder es la ubicación física: la caja
    binder_type: str  # binder, deck o list, según ManaBox


def latest_csv(folder: Path) -> Path:
    """El CSV modificado más recientemente de la carpeta."""
    csv_files = [path for path in folder.glob("*.csv") if path.is_file()]
    if not csv_files:
        raise FileNotFoundError(f"No hay archivos .csv en {folder}")
    return max(csv_files, key=lambda path: path.stat().st_mtime)


def read_csv(path: Path) -> list[CollectionCard]:
    """Lee el CSV de ManaBox (solo lectura) y devuelve sus filas."""
    # utf-8-sig ignora la marca BOM que a veces trae al inicio un CSV exportado.
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [to_collection_card(row) for row in csv.DictReader(file)]


def to_collection_card(row: dict) -> CollectionCard:
    """Convierte una fila del CSV (columnas con los nombres de ManaBox)."""
    return CollectionCard(
        name=row["Name"],
        scryfall_id=row["Scryfall ID"],
        set_code=row["Set code"],
        collector_number=row["Collector number"],
        finish=row["Foil"],
        language=row["Language"],
        quantity=int(row["Quantity"]),
        binder=row["Binder Name"],
        binder_type=row["Binder Type"],
    )


def count_by_binder(cards: list[CollectionCard]) -> dict[str, int]:
    """Cuántas cartas (con copias) hay en cada binder, ordenado por nombre."""
    counts = Counter()
    for card in cards:
        counts[card.binder] += card.quantity
    return dict(sorted(counts.items()))
