from __future__ import annotations

UNIT_ALIASES = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
}


class UnitNormalizationError(ValueError):
    pass


def normalize_unit(unit: str) -> str:
    key = unit.strip().lower()
    if key not in UNIT_ALIASES:
        raise UnitNormalizationError(f"Unsupported unit: {unit}")
    return UNIT_ALIASES[key]


def to_grams(amount: float, unit: str) -> float:
    normalized_unit = normalize_unit(unit)
    if normalized_unit == "g":
        return amount
    if normalized_unit == "ml":
        return amount
    raise UnitNormalizationError(f"Unsupported unit: {unit}")
