"""Configuración local: config.toml en la raíz del proyecto.

config.toml no se versiona porque guarda rutas de esta Mac.
Para crearlo, copia config.example.toml y ajusta las rutas.
"""

import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.toml"
DEFAULT_EXCHANGE_RATE = 18.0  # pesos por dólar, si config.toml no dice otra cosa


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Lee config.toml y lo devuelve como diccionario."""
    if not path.exists():
        raise FileNotFoundError(
            f"No encontré {path}. Copia config.example.toml como config.toml y ajusta las rutas."
        )
    with path.open("rb") as file:  # tomllib pide el archivo en modo binario
        return tomllib.load(file)


def manabox_dir(config: dict) -> Path:
    """Carpeta donde ManaBox deja sus exportaciones CSV."""
    folder = config.get("coleccion", {}).get("carpeta_manabox")
    if not folder:
        raise KeyError("Falta carpeta_manabox en la sección [coleccion] de config.toml")
    # Path maneja bien los espacios del nombre; nunca la pasamos por la terminal.
    return Path(folder).expanduser()


def exchange_rate(path: Path = CONFIG_PATH) -> float:
    """Tipo de cambio para convertir USD a MXN; 18 si no hay config.toml o no lo define."""
    if not path.exists():
        return DEFAULT_EXCHANGE_RATE
    return float(load_config(path).get("precios", {}).get("tipo_de_cambio", DEFAULT_EXCHANGE_RATE))
