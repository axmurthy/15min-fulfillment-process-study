"""Random inputs for the simulation.

Every sampler takes an explicit ``numpy.random.Generator`` so that all
randomness is reproducible and traceable to a single seed. We deliberately keep
the distribution *choices* visible and justified rather than hidden:

- Arrivals: non-homogeneous Poisson (piecewise-constant rate). The Poisson
  process is the standard memoryless model for independent arrivals; we make it
  non-homogeneous so demand can differ between off-peak and peak. We also expose
  a constant-rate and a deterministic option so the model can be stress-tested
  against alternative assumptions (the brief forbids assuming a distribution
  without justification -- so we TEST alternatives).
- Basket size: negative binomial, a count distribution that allows variance to
  exceed the mean (real baskets are over-dispersed). Mean and dispersion are
  configurable; dispersion -> infinity recovers Poisson.
- Processing / access times: gamma, parameterised by mean and coefficient of
  variation (CV). Gamma is non-negative and right-skewed, which matches service
  times better than a normal. CV = 0 collapses to a deterministic time (used by
  the hand-checkable verification cases).
"""
from __future__ import annotations

import numpy as np

from .config import DotDict


def arrival_times(cfg, rng: np.random.Generator) -> list[float]:
    """Generate accepted-order arrival instants (minutes) over the horizon.

    For "nhpp_piecewise" we generate a homogeneous Poisson process *within* each
    period at that period's rate. Because the rate is piecewise-constant and the
    Poisson process is memoryless, concatenating per-period homogeneous processes
    is an exact simulation of the non-homogeneous process.
    """
    process = cfg.arrivals.process
    # Scenario factor: scale every period's rate (defaults to 1.0 if absent).
    mult = float(cfg.arrivals.get("demand_multiplier", 1.0))
    times: list[float] = []

    if process in ("nhpp_piecewise", "poisson_constant"):
        periods = cfg.arrivals.periods
        if process == "poisson_constant":
            # Flatten to a single average rate across the whole horizon.
            total = sum(
                p.orders_per_min * (p.end_min - p.start_min) for p in periods
            )
            span = float(cfg.simulation.horizon_min)
            periods = [
                DotDict(start_min=0.0, end_min=span, orders_per_min=total / span)
            ]
        for p in periods:
            rate = float(p.orders_per_min) * mult
            if rate <= 0:
                continue
            t = float(p.start_min)
            end = float(p.end_min)
            while True:
                t += rng.exponential(1.0 / rate)
                if t >= end:
                    break
                times.append(t)

    elif process == "deterministic":
        # Fixed inter-arrival gaps per period (used for verification).
        for p in cfg.arrivals.periods:
            rate = float(p.orders_per_min)
            if rate <= 0:
                continue
            gap = 1.0 / rate
            t = float(p.start_min) + gap
            while t < float(p.end_min):
                times.append(t)
                t += gap
    else:  # pragma: no cover - guarded by config
        raise ValueError(f"unknown arrival process: {process}")

    times.sort()
    return times


def basket_size(cfg, rng: np.random.Generator) -> int:
    """Draw the number of items in an order."""
    dist = cfg.basket.distribution
    if dist == "neg_binomial":
        mu = float(cfg.basket.mean_items)
        k = float(cfg.basket.dispersion_k)
        p = k / (k + mu)
        draw = int(rng.negative_binomial(k, p))
    elif dist == "poisson":
        draw = int(rng.poisson(float(cfg.basket.mean_items)))
    else:  # pragma: no cover
        raise ValueError(f"unknown basket distribution: {dist}")
    return max(int(cfg.basket.min_items), draw)


def _gamma(mean: float, cv: float, rng: np.random.Generator) -> float:
    """Sample a gamma time with given mean and coefficient of variation."""
    if mean <= 0:
        return 0.0
    if cv <= 0:
        return float(mean)
    shape = 1.0 / (cv * cv)
    scale = mean * cv * cv
    return float(rng.gamma(shape, scale))


def pick_pack_time(cfg, items: int, rng: np.random.Generator) -> float:
    """Combined picking + packing time for one order (minutes)."""
    mean = (
        float(cfg.picking.setup_min)
        + float(cfg.picking.per_item_min) * items
        + float(cfg.picking.pack_min)
    )
    return _gamma(mean, float(cfg.picking.cv), rng)


def access_time(cfg, rng: np.random.Generator) -> float:
    """Building-access time at the customer (minutes)."""
    return _gamma(float(cfg.courier.access_min_mean), float(cfg.courier.access_cv), rng)


def customer_distance_km(cfg, rng: np.random.Generator) -> float:
    """Straight-line distance from MFC to customer, uniform over the service disk.

    For a uniform point in a disk of radius R, the distance has CDF (r/R)^2, so
    r = R * sqrt(U). This is a geometry-based routing *estimate*, not an observed
    delivery distance.
    """
    R = float(cfg.geography.service_radius_km)
    return R * float(np.sqrt(rng.uniform()))


def travel_time_min(distance_km: float, speed_kmh: float) -> float:
    """Convert a distance to travel minutes at a given (safe) speed."""
    if speed_kmh <= 0:
        raise ValueError("speed must be positive")
    return distance_km / speed_kmh * 60.0
