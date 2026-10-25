"""Perfiles de mazo: leen y validan los YAML de decks/profiles/.

Cada perfil describe el objetivo de un mazo. Todo análisis se mide contra él.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

# Carpeta donde viven los perfiles, relativa a la raíz del proyecto.
PROFILES_DIR = Path(__file__).resolve().parents[2] / "decks" / "profiles"


class DeckProfile(BaseModel):
    """Un perfil de mazo. Los nombres de campo coinciden con las claves del YAML."""

    slug: str
    archidekt_id: int | None = None
    nombre: str
    comandante: str = ""
    # Los brackets oficiales de Commander van del 1 al 5.
    bracket: int | None = Field(default=None, ge=1, le=5)
    bracket_teorico: int | None = Field(default=None, ge=1, le=5)
    estado: Literal["armado", "en_construccion", "archivado"]
    lista_sincronizada: bool = False
    tema: str = ""
    plan_de_victoria: str = ""
    ventana_victoria: str = ""
    restricciones: list[str] = []
    presupuesto_mxn: float | None = None
    notas: str = ""


def load_profile(slug: str, profiles_dir: Path = PROFILES_DIR) -> DeckProfile:
    """Lee decks/profiles/<slug>.yaml y lo convierte en un DeckProfile validado."""
    path = profiles_dir / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No existe el perfil '{slug}' en {profiles_dir}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    profile = DeckProfile.model_validate(data)

    # El slug dentro del archivo debe coincidir con el nombre del archivo.
    if profile.slug != slug:
        raise ValueError(f"El archivo {path.name} dice slug '{profile.slug}'")
    return profile
