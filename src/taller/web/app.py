"""Página web de la mesa de taller (Fase 4).

Se arranca con `uv run taller web` y se abre en http://127.0.0.1:8000.
Cómo funciona: FastAPI recibe la petición, Python arma los datos y Jinja2
los acomoda en las plantillas HTML de templates/. El diseño vive en
static/style.css.
"""

import json
import re
from pathlib import Path

import markdown
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from taller.analysis.report import COLOR_NAMES
from taller.profiles import PROFILES_DIR, list_profiles, load_profile

WEB_DIR = Path(__file__).resolve().parent
REPORTS_DIR = Path(__file__).resolve().parents[3] / "reports"
# Un slug válido: minúsculas, números y guiones (evita rutas raras en la URL).
SLUG = re.compile(r"^[a-z0-9-]+$")

app = FastAPI(title="Mesa de taller")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Portada: una tarjeta por mazo."""
    decks = [{"profile": profile, "report": latest_report(profile.slug)} for profile in list_profiles()]
    return templates.TemplateResponse(request, "home.html", {"decks": decks})


@app.get("/mazos/{slug}", response_class=HTMLResponse)
def deck_page(request: Request, slug: str):
    """Página de un mazo: la diseñada si hay datos (.json); si no, el reporte Markdown."""
    if not SLUG.match(slug) or not (PROFILES_DIR / f"{slug}.yaml").exists():
        raise HTTPException(status_code=404, detail="No existe ese mazo")
    profile = load_profile(slug)
    data_file = latest_report(slug, suffix=".json")
    if data_file:
        data = json.loads(data_file.read_text(encoding="utf-8"))
        return templates.TemplateResponse(request, "deck.html", {
            "profile": profile, "data": data, "scale": role_scale(data["roles"]),
            "curve_max": max(bar["count"] for bar in data["mana"]["curve"]) or 1,
        })
    report = latest_report(slug)
    report_html = render_markdown(report.read_text(encoding="utf-8")) if report else None
    return templates.TemplateResponse(request, "deck_markdown.html", {
        "profile": profile, "report": report, "report_html": report_html,
    })


def latest_report(slug: str, reports_dir: Path = REPORTS_DIR, suffix: str = ".md") -> Path | None:
    """El reporte (o sus datos .json) más reciente del mazo, sin las comparaciones "-vs-"."""
    pattern = re.compile(rf"^{re.escape(slug)}-\d{{4}}-\d{{2}}-\d{{2}}{re.escape(suffix)}$")
    reports = sorted(path for path in reports_dir.glob(f"{slug}-*{suffix}") if pattern.match(path.name))
    return reports[-1] if reports else None


def role_scale(roles: list[dict]) -> int:
    """El número que ocupa toda la barra: el mayor entre conteos y máximos de referencia.

    Solo cuentan los roles con referencia; tokens y cierre van aparte (son el plan).
    """
    return max((max(role["count"], role["high"]) for role in roles if role["high"]), default=1)


def render_markdown(text: str) -> str:
    """Convierte el reporte Markdown a HTML (con tablas)."""
    return markdown.markdown(text, extensions=["tables"])


def markdown_inline(text: str) -> str:
    """Una línea Markdown (negritas, ligas) a HTML, sin el párrafo que la envuelve."""
    html = markdown.markdown(text)
    return html.removeprefix("<p>").removesuffix("</p>")


def report_date(report: Path) -> str:
    """"tokens-isshin-2026-10-26.md" → "2026-10-26"."""
    return report.stem[-10:]


templates.env.filters["report_date"] = report_date
templates.env.filters["md"] = markdown_inline
templates.env.globals["COLOR_NAMES"] = COLOR_NAMES
