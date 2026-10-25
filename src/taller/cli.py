"""Línea de comandos: `taller <comando>`.

Ejemplo: uv run taller analizar tokens-isshin
"""

import re
from datetime import date
from pathlib import Path

import typer

from taller.analysis.analyze import analyze
from taller.analysis.compare import compare
from taller.analysis.compare_report import render_comparison
from taller.analysis.report import render
from taller.profiles import load_profile
from taller.sources.decklist import load_other_deck

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

app = typer.Typer(help="Mesa de taller para mazos de Commander.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Mesa de taller para mazos de Commander."""
    # Con un callback, typer siempre pide el nombre del subcomando
    # (taller analizar ...), aunque por ahora solo haya uno.


@app.command()
def analizar(slug: str) -> None:
    """Analiza el mazo del perfil <slug> y escribe el reporte en reports/."""
    profile = load_profile(slug)
    typer.echo(f"Analizando {profile.nombre}...")
    report = render(analyze(profile))

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{slug}-{date.today().isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    typer.echo(f"Reporte listo: {path}")


@app.command()
def comparar(slug: str, fuente: str) -> None:
    """Compara tu mazo <slug> contra otro: una URL de Archidekt o un archivo .txt."""
    profile = load_profile(slug)
    typer.echo(f"Analizando {profile.nombre}...")
    own = analyze(profile)
    other, unresolved = load_other_deck(fuente)
    typer.echo(f"Comparando contra {other.name}...")
    report = render_comparison(compare(own, other, unresolved))

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{slug}-vs-{slugify(other.name)}-{date.today().isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    typer.echo(f"Reporte listo: {path}")


def slugify(text: str) -> str:
    """Convierte un nombre en algo seguro para un archivo: "Isshin Makes Tokens!" → "isshin-makes-tokens"."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words)[:40] or "mazo"
