"""Envío por tienda: cuánto cuesta y desde qué monto es gratis.

Las reglas viven en config.toml, sección [envios], porque son datos de
Martín (ej. en Yellow Rabbit recoge en sucursal) y cambian con el tiempo.
"""

from dataclasses import dataclass

# Clave en config.toml → nombre de la tienda en el reporte.
STORE_KEYS = {"yellow_rabbit": "Yellow Rabbit", "tcg_wolf": "TCG Wolf"}


@dataclass
class ShippingRule:
    cost: float  # MXN
    free_from: float  # a partir de este subtotal el envío es gratis; 0 = nunca
    note: str = ""


def shipping_rules(config: dict) -> dict[str, ShippingRule]:
    """Lee [envios] de config.toml: {"TCG Wolf": ShippingRule(...)}."""
    rules = {}
    for key, values in config.get("envios", {}).items():
        store = STORE_KEYS.get(key, key)
        rules[store] = ShippingRule(cost=values.get("costo", 0), free_from=values.get("gratis_desde", 0),
                                    note=values.get("nota", ""))
    return rules


def shipping_cost(subtotal: float, rule: ShippingRule) -> float:
    """Envío que pagarías por una compra de `subtotal` pesos."""
    if rule.free_from and subtotal >= rule.free_from:
        return 0
    return rule.cost


def missing_for_free(subtotal: float, rule: ShippingRule) -> float:
    """Cuánto falta para el envío gratis (0 si ya llegas o si nunca es gratis)."""
    if not rule.free_from or rule.cost == 0:
        return 0
    return max(rule.free_from - subtotal, 0)
