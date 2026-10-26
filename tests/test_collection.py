"""Pruebas de la colección: config, lectura del CSV de ManaBox y guardado, sin internet."""

import os

import pytest

from taller.collection.manabox import count_by_binder, latest_csv, read_csv
from taller.collection.store import collection_size, replace_collection
from taller.config import load_config, manabox_dir

HEADER = (
    "Binder Name,Binder Type,Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,"
    "ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,Signed,Condition,Language,Proxy,"
    "Purchase price currency,Added\n"
)
# Dos filas reales del CSV de Martín; la primera tiene una coma dentro del nombre.
ROWS = (
    'Golgari - GB,binder,"Jarad, Golgari Lich Lord",TDC,Tarkir: Dragonstorm Commander,293,normal,'
    "mythic,1,104707,6870b355-e53d-4fa2-887b-0f0445bcd9c5,4.99,false,false,false,near_mint,en,"
    "false,USD,2026-10-23T19:17:15.518Z\n"
    "Orzhov WB,binder,Beckon Apparition,UMA,Ultimate Masters,211,normal,common,2,43310,"
    "396bdd5f-2aad-48ba-a4b1-f2b2365a1a53,0.29,false,false,false,near_mint,en,false,USD,"
    "2026-10-26T00:20:38.732Z\n"
)


def write_csv(path, rows=ROWS):
    path.write_text(HEADER + rows, encoding="utf-8")
    return path


def test_config_reads_folder_with_spaces(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[coleccion]\ncarpeta_manabox = "/Users/yo/Documents/MTG Archive"\n')
    assert str(manabox_dir(load_config(config_file))) == "/Users/yo/Documents/MTG Archive"


def test_missing_config_explains_what_to_do(tmp_path):
    with pytest.raises(FileNotFoundError, match="config.example.toml"):
        load_config(tmp_path / "config.toml")


def test_read_csv_parses_rows(tmp_path):
    cards = read_csv(write_csv(tmp_path / "ManaBox_Collection.csv"))
    assert [card.name for card in cards] == ["Jarad, Golgari Lich Lord", "Beckon Apparition"]
    assert cards[1].quantity == 2
    assert cards[1].binder == "Orzhov WB"


def test_count_by_binder_includes_copies(tmp_path):
    cards = read_csv(write_csv(tmp_path / "ManaBox_Collection.csv"))
    assert count_by_binder(cards) == {"Golgari - GB": 1, "Orzhov WB": 2}


def test_latest_csv_picks_newest(tmp_path):
    old = write_csv(tmp_path / "viejo.csv")
    new = write_csv(tmp_path / "nuevo.csv")
    os.utime(old, (1_000_000, 1_000_000))  # fecha de modificación antigua a propósito
    assert latest_csv(tmp_path) == new


def test_latest_csv_fails_on_empty_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        latest_csv(tmp_path)


def test_reading_does_not_touch_the_folder(tmp_path):
    # La carpeta de ManaBox es de solo lectura: nada debe cambiar después de leerla.
    path = write_csv(tmp_path / "ManaBox_Collection.csv")
    before = {(p.name, p.stat().st_mtime) for p in tmp_path.iterdir()}
    read_csv(latest_csv(tmp_path))
    after = {(p.name, p.stat().st_mtime) for p in tmp_path.iterdir()}
    assert before == after


def test_import_replaces_whole_collection(tmp_path):
    db_path = tmp_path / "taller.db"
    cards = read_csv(write_csv(tmp_path / "a.csv"))
    replace_collection(cards, {}, "a.csv", db_path)
    assert collection_size(db_path) == 3

    # Segunda importación con una sola carta: la anterior desaparece, no se suma.
    replace_collection(cards[:1], {}, "b.csv", db_path)
    assert collection_size(db_path) == 1
