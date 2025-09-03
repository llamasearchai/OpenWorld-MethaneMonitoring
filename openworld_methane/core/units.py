from __future__ import annotations

from typing import Literal

Unit = Literal["kg/h", "g/h", "m3/h"]

# Methane density at ~15C near sea level (approx)
METHANE_DENSITY_KG_PER_M3 = 0.656


def to_kg_per_h(value: float, unit: Unit) -> float:
    """Convert emission rate to kg/h.

    Args:
        value: The emission rate value.
        unit: The unit of the value.

    Returns:
        The value in kg/h.

    Raises:
        ValueError: If the unit is unsupported.
    """
    if unit == "kg/h":
        return float(value)
    if unit == "g/h":
        return float(value) / 1000.0
    if unit == "m3/h":
        return float(value) * METHANE_DENSITY_KG_PER_M3
    raise ValueError(f"Unsupported unit: {unit}")


def from_kg_per_h(value_kg_h: float, unit: Unit) -> float:
    """Convert emission rate from kg/h to the specified unit.

    Args:
        value_kg_h: The emission rate in kg/h.
        unit: The target unit.

    Returns:
        The value in the specified unit.

    Raises:
        ValueError: If the unit is unsupported.
    """
    if unit == "kg/h":
        return float(value_kg_h)
    if unit == "g/h":
        return float(value_kg_h) * 1000.0
    if unit == "m3/h":
        return float(value_kg_h) / METHANE_DENSITY_KG_PER_M3
    raise ValueError(f"Unsupported unit: {unit}")
