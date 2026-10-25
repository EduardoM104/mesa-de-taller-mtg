"""Línea de comandos: `taller <comando>`.

Ejemplo: uv run taller analizar tokens-isshin
"""

from datetime import date
from pathlib import Path

import typer

from taller.analysis.analyze import analyze
from taller.analysis.report import render
from taller.profiles import load_profile

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
