"""Pruebas de la lectura y validación de perfiles."""

import pytest
from pydantic import ValidationError

from taller.profiles import load_profile


def write_profile(folder, slug, text):
    # Ayudante: escribe un YAML de prueba en una carpeta temporal.
    (folder / f"{slug}.yaml").write_text(text, encoding="utf-8")


def test_isshin_profile_loads():
    # El perfil real del repo debe ser válido.
    profile = load_profile("tokens-isshin")
    assert profile.comandante == "Isshin, Two Heavens as One"
    assert profile.archidekt_id == 26390360
    assert profile.lista_sincronizada is False


def test_missing_profile_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_profile("no-existe", profiles_dir=tmp_path)


def test_invalid_bracket_raises(tmp_path):
    write_profile(tmp_path, "malo", "slug: malo\nnombre: Malo\nestado: armado\nbracket: 7\n")
    with pytest.raises(ValidationError):
        load_profile("malo", profiles_dir=tmp_path)


def test_slug_must_match_filename(tmp_path):
    write_profile(tmp_path, "uno", "slug: otro\nnombre: Uno\nestado: armado\n")
    with pytest.raises(ValueError):
        load_profile("uno", profiles_dir=tmp_path)


def test_invalid_estado_raises(tmp_path):
    write_profile(tmp_path, "malo", "slug: malo\nnombre: Malo\nestado: terminado\n")
    with pytest.raises(ValidationError):
        load_profile("malo", profiles_dir=tmp_path)
