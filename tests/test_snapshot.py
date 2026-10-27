"""Pruebas de la foto del análisis (el JSON que usa la página web)."""

import json

from taller.analysis.snapshot import snapshot, synergy_data
from taller.web.app import role_scale

from helpers import make_entry
from test_report import ENTRIES, build_analysis


def test_snapshot_is_json():
    # Si algo no se puede guardar como JSON, json.dumps truena.
    assert json.loads(json.dumps(snapshot(build_analysis(ENTRIES))))["header"]["nombre"] == "Prueba"


def test_roles_have_state():
    roles = {role["key"]: role for role in snapshot(build_analysis(ENTRIES))["roles"]}
    assert roles["robo"]["state"] == "bajo"
    assert roles["tokens"]["state"] is None  # sin referencia


def test_synergy_does_not_repeat_theme_pieces():
    entries = ENTRIES + [make_entry("Goblin Rabblemaster", type_line="Creature",
                                    tags=["attack trigger", "repeatable creature tokens"])]
    data = synergy_data(build_analysis(entries))
    assert "Goblin Rabblemaster" in data["pieces"]
    assert "Goblin Rabblemaster" not in data["tokens"] + data["closers"] + data["both"]


def test_low_role_suggestion_says_where_the_card_is():
    maybe = [make_entry("Mentor of the Meek", type_line="Creature", tags=["repeatable pure draw"])]
    analysis = build_analysis(ENTRIES, maybe_entries=maybe)
    analysis.owned = {"Mentor of the Meek": {"Orzhov WB": 1}}
    draw = next(item for item in snapshot(analysis)["suggestions"] if item["title"] == "Sube robo")
    assert draw["groups"][0]["cards"] == [{"name": "Mentor of the Meek", "location": "Orzhov WB"}]


def test_role_scale_ignores_roles_without_reference():
    roles = [{"count": 7, "high": 12}, {"count": 23, "high": None}]
    assert role_scale(roles) == 12
