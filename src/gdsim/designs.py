"""Designed-experiment definitions.

These are experiments on a MODEL, not field experiments. A factorial design lets
us estimate main effects AND interactions of the controllable factors with few
runs, which is exactly how a process engineer screens for critical parameters.

Controllable factors (things an operator can set):
    radius_km   -> geography.service_radius_km
    pickers     -> picking.n_pickers
    couriers    -> courier.n_couriers

Scenario factors (uncertain conditions we do NOT control, varied separately so we
can test robustness): demand level and travel speed.
"""
from __future__ import annotations

from itertools import product

from .experiment import Factor

CONTROLLABLE_FACTORS = [
    Factor("radius_km", "geography.service_radius_km"),
    Factor("pickers", "picking.n_pickers"),
    Factor("couriers", "courier.n_couriers"),
]

# Low / high levels for the 2^3 factorial, plus a centre point.
LEVELS = {
    "radius_km": {"low": 1.0, "high": 2.0, "center": 1.5},
    "pickers": {"low": 2, "high": 4, "center": 3},
    "couriers": {"low": 6, "high": 10, "center": 8},
}

SCENARIO_FACTORS = [
    Factor("demand_mult", "arrivals.demand_multiplier"),
    Factor("speed_kmh", "courier.speed_kmh"),
]

SCENARIO_LEVELS = {
    "demand_mult": {"baseline": 1.0, "high": 1.5},
    "speed_kmh": {"normal": 15.0, "slow": 10.0},  # 'slow' = congestion/rain
}


def factorial_2level(center: bool = True) -> list[dict]:
    """The 2^3 controllable design (8 corner points), optionally + 1 centre point."""
    corners = []
    for r, p, c in product(["low", "high"], repeat=3):
        corners.append(
            {
                "radius_km": LEVELS["radius_km"][r],
                "pickers": LEVELS["pickers"][p],
                "couriers": LEVELS["couriers"][c],
            }
        )
    if center:
        corners.append(
            {
                "radius_km": LEVELS["radius_km"]["center"],
                "pickers": LEVELS["pickers"]["center"],
                "couriers": LEVELS["couriers"]["center"],
            }
        )
    return corners


def scenario_grid() -> list[dict]:
    """All combinations of the scenario factors."""
    out = []
    for d, s in product(
        SCENARIO_LEVELS["demand_mult"].values(), SCENARIO_LEVELS["speed_kmh"].values()
    ):
        out.append({"demand_mult": d, "speed_kmh": s})
    return out


def crossed_design() -> tuple[list[Factor], list[dict]]:
    """Controllable factorial crossed with every scenario combination.

    Returns (factors, design_points) where each design point carries both
    controllable and scenario columns.
    """
    factors = CONTROLLABLE_FACTORS + SCENARIO_FACTORS
    points = []
    for ctrl in factorial_2level(center=False):
        for scen in scenario_grid():
            points.append({**ctrl, **scen})
    return factors, points
