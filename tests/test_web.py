"""Pruebas de la página web con el cliente de pruebas de FastAPI (sin abrir el navegador)."""

from fastapi.testclient import TestClient

from taller.web.app import app, latest_report

client = TestClient(app)


def test_home_lists_decks():
    response = client.get("/")
    assert response.status_code == 200
    assert "Tokens" in response.text
    assert "DragonSSSS!" in response.text


def test_unknown_deck_is_404():
    assert client.get("/mazos/no-existe").status_code == 404


def test_latest_report_ignores_comparisons(tmp_path):
    for name in ("tokens-isshin-2026-10-25.md", "tokens-isshin-2026-10-26.md",
                 "tokens-isshin-vs-otro-2026-10-27.md"):
        (tmp_path / name).write_text("# reporte", encoding="utf-8")
    assert latest_report("tokens-isshin", tmp_path).name == "tokens-isshin-2026-10-26.md"


def test_deck_page_shows_report():
    response = client.get("/mazos/tokens-isshin")
    assert response.status_code == 200
    assert "<table>" in response.text
