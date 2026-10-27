"""Línea de comandos: `taller <comando>`.

Ejemplos:
    uv run taller analizar tokens-isshin
    uv run taller coleccion importar
"""

import re
from datetime import date
from pathlib import Path

import httpx
import typer

from taller.analysis.analyze import DeckAnalysis, analyze
from taller.analysis.compare import compare
from taller.analysis.compare_report import render_comparison
from taller.analysis.report import render, shopping_items
from taller.collection.manabox import count_by_binder, latest_csv, read_csv
from taller.collection.store import replace_collection
from taller.config import load_config, manabox_dir, ucp_profile
from taller.prices import yellow_rabbit
from taller.profiles import load_profile
from taller.sources.decklist import load_other_deck
from taller.sources.scryfall import find_cards_by_name, update_cards

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

app = typer.Typer(help="Mesa de taller para mazos de Commander.", no_args_is_help=True)
coleccion_app = typer.Typer(help="Colección física (exportaciones de ManaBox).", no_args_is_help=True)
app.add_typer(coleccion_app, name="coleccion")

# Opción compartida por los comandos: ignorar la copia de hoy de Archidekt.
REFRESH_OPTION = typer.Option(False, "--refrescar", help="Vuelve a descargar de Archidekt aunque haya copia de hoy.")


@app.callback()
def main() -> None:
    """Mesa de taller para mazos de Commander."""
    # Con un callback, typer siempre pide el nombre del subcomando
    # (taller analizar ..., taller comparar ...).


@app.command()
def analizar(slug: str, refrescar: bool = REFRESH_OPTION) -> None:
    """Analiza el mazo del perfil <slug> y escribe el reporte en reports/."""
    profile = load_profile(slug)
    typer.echo(f"Analizando {profile.nombre}...")
    analysis = analyze(profile, refresh=refrescar)
    add_store_prices(analysis, refresh=refrescar)
    report = render(analysis)

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{slug}-{date.today().isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    typer.echo(f"Reporte listo: {path}")


@app.command()
def comparar(slug: str, fuente: str, refrescar: bool = REFRESH_OPTION) -> None:
    """Compara tu mazo <slug> contra otro: una URL de Archidekt o un archivo .txt."""
    profile = load_profile(slug)
    typer.echo(f"Analizando {profile.nombre}...")
    own = analyze(profile, refresh=refrescar)
    other, unresolved = load_other_deck(fuente, refresh=refrescar)
    typer.echo(f"Comparando contra {other.name}...")
    report = render_comparison(compare(own, other, unresolved))

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{slug}-vs-{slugify(other.name)}-{date.today().isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    typer.echo(f"Reporte listo: {path}")


@coleccion_app.callback()
def coleccion() -> None:
    """Colección física (exportaciones de ManaBox)."""


@coleccion_app.command()
def importar(archivo: Path | None = typer.Argument(None, help="CSV de ManaBox; si no se da, el más reciente de la carpeta de config.toml.")) -> None:
    """Reemplaza la colección completa con un CSV de ManaBox."""
    path = archivo or latest_csv(manabox_dir(load_config()))
    typer.echo(f"Leyendo {path}...")
    cards = read_csv(path)

    update_cards()  # la tabla de Scryfall hace falta para buscar el oracle_id
    found = find_cards_by_name(sorted({card.name for card in cards}))
    oracle_ids = {name: card.oracle_id for name, card in found.items()}
    replace_collection(cards, oracle_ids, path.name)

    total = sum(card.quantity for card in cards)
    typer.echo(f"Colección reemplazada: {total} cartas en {len(cards)} filas.")
    for binder, count in count_by_binder(cards).items():
        typer.echo(f"  {binder}: {count}")
    unresolved = sorted({card.name for card in cards if card.name.lower() not in oracle_ids})
    if unresolved:
        typer.echo(f"Sin encontrar en Scryfall ({len(unresolved)}): {', '.join(unresolved)}")


def add_store_prices(analysis: DeckAnalysis, refresh: bool = False) -> None:
    """Consulta Yellow Rabbit para la lista de compra. Si no se puede, deja una nota."""
    names = [item.name for item in shopping_items(analysis)]
    if not names:
        return
    profile_url = ucp_profile()
    if not profile_url:
        analysis.store_note = "Sin precios de Yellow Rabbit: falta `perfil_ucp` en la sección [tiendas] de config.toml."
        return
    typer.echo(f"Consultando Yellow Rabbit ({len(names)} cartas)...")
    try:
        analysis.store_offers = yellow_rabbit.best_offers(names, profile_url, refresh=refresh)
    except httpx.HTTPError as error:
        analysis.store_note = f"Yellow Rabbit no respondió ({error}); usa las ligas de búsqueda."


def slugify(text: str) -> str:
    """Convierte un nombre en algo seguro para un archivo: "Isshin Makes Tokens!" → "isshin-makes-tokens"."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words)[:40] or "mazo"
