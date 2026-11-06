"""Phase 4 -- software VERIFICATION (is the model built right?), not real-world
validation (is it the right model of reality?). These are hand-checkable cases
where we can predict the answer with pencil and paper.
"""
from __future__ import annotations

import numpy as np

from gdsim.config import from_dict
from gdsim.model import OrderState, run_once


def _deterministic_single_order_cfg():
    """One order, no randomness anywhere, abundant resources.

    With cv=0 everywhere, inventory always available, and a single deterministic
    arrival, the order-to-door time is exactly:
        pick_pack + load + travel_out + access
    where pick_pack = setup + per_item*items + pack, and travel_out = dist/speed*60.
    """
    return from_dict(
        {
            "meta": {"base_seed": 1},
            "simulation": {
                "horizon_min": 1000,
                "warmup_min": 0,
                "n_replications": 1,
                "target_min": 15.0,
            },
            "arrivals": {
                "process": "deterministic",
                "demand_multiplier": 1.0,
                # one arrival at t=100 (gap=100 over [0,200) => a single arrival at 100)
                "periods": [
                    {"name": "x", "start_min": 0, "end_min": 150, "orders_per_min": 0.01}
                ],
            },
            "basket": {
                "distribution": "poisson",
                "mean_items": 5,
                "dispersion_k": 4,
                "min_items": 5,  # forces exactly 5 items (max(min, draw) with draw<=5 rare)
            },
            "inventory": {"availability_prob": 1.0},
            "picking": {
                "n_pickers": 5,
                "setup_min": 1.0,
                "per_item_min": 0.5,
                "pack_min": 2.0,
                "cv": 0.0,
            },
            "courier": {
                "n_couriers": 5,
                "dispatch_policy": "assign_at_accept",
                "speed_kmh": 12.0,
                "load_min": 1.0,
                "access_min_mean": 2.0,
                "access_cv": 0.0,
                "return_speed_kmh": 12.0,
            },
            "geography": {"service_radius_km": 0.0},  # distance exactly 0 => travel 0
            "patience": {"cancel_after_min": 1000.0},
        }
    )


def test_single_order_hand_check():
    cfg = _deterministic_single_order_cfg()
    # Force exactly 5 items by using min_items == mean and a seed; but to be exact,
    # set basket min_items high enough that max() pins it. We instead assert using
    # the actual drawn items so the arithmetic identity is what we verify.
    result = run_once(cfg, seed=cfg.meta.base_seed)
    orders = [o for o in result.orders if o.state == OrderState.COMPLETED]
    assert len(orders) == 1
    o = orders[0]

    expected_pick_pack = 1.0 + 0.5 * o.items + 2.0
    # radius 0 => distance 0 => travel 0; access deterministic 2.0; load 1.0
    expected_otd = expected_pick_pack + 1.0 + 0.0 + 2.0
    assert abs(o.pick_pack_min - expected_pick_pack) < 1e-9
    assert abs(o.order_to_door_min - expected_otd) < 1e-9


def test_travel_scales_with_distance():
    """At radius 0 travel is 0; set a fixed distance and check the clock grows."""
    cfg = _deterministic_single_order_cfg()
    result = run_once(cfg, seed=1)
    o0 = next(o for o in result.orders if o.state == OrderState.COMPLETED)
    otd_zero = o0.order_to_door_min

    cfg2 = from_dict(dict(cfg))
    cfg2["geography"]["service_radius_km"] = 2.0  # now distance in (0, 2]
    r2 = run_once(cfg2, seed=1)
    o2 = next(o for o in r2.orders if o.state == OrderState.COMPLETED)
    # Travel out = dist/12*60; must be strictly positive and match identity.
    expected = o2.pick_pack_min + 1.0 + (o2.distance_km / 12.0 * 60.0) + 2.0
    assert abs(o2.order_to_door_min - expected) < 1e-9
    assert o2.order_to_door_min > otd_zero


def test_reproducibility_same_seed():
    cfg = _deterministic_single_order_cfg()
    cfg["geography"]["service_radius_km"] = 1.5
    a = run_once(cfg, seed=42)
    b = run_once(cfg, seed=42)
    ta = [o.order_to_door_min for o in a.orders]
    tb = [o.order_to_door_min for o in b.orders]
    assert ta == tb


def test_different_seed_differs():
    cfg = _deterministic_single_order_cfg()
    cfg["geography"]["service_radius_km"] = 1.5
    cfg["basket"]["min_items"] = 1
    cfg["picking"]["cv"] = 0.3
    a = run_once(cfg, seed=1)
    b = run_once(cfg, seed=2)
    assert [o.pick_pack_min for o in a.orders] != [o.pick_pack_min for o in b.orders]
