"""Pruebas de ejemplo de la Fase 0: confirman que el proyecto está bien instalado."""

import taller


def test_package_imports():
    # Si el paquete no estuviera instalado, el `import` de arriba ya habría fallado.
    assert taller.__name__ == "taller"


def test_main_prints_greeting(capsys):
    # capsys atrapa lo que se imprime en pantalla para poder revisarlo.
    taller.main()
    output = capsys.readouterr().out
    assert "Hello from taller!" in output
