"""Phase 4 -- extreme-scenario checks. The model must behave sensibly at the
boundaries, where the right answer is obvious.
"""
from __future__ import annotations

from gdsim.config import apply_overrides, load_config
from gdsim.metrics import replication_metrics
from gdsim.model import OrderState, run_once
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def _cfg():
    return load_config(CONFIG)


def test_zero_demand_produces_no_orders():
    cfg = apply_overrides(_cfg(), {"arrivals.demand_multiplier": 0.0})
    result = run_once(cfg, seed=1)
    assert len(result.orders) == 0
    m = replication_metrics(result, cfg)
    assert m["n_accepted"] == 0


def test_saturation_degrades_service_without_crashing():
    """Huge demand + a single courier: throughput is capacity-bound, service
    collapses, and the shortfall shows up as lateness/cancellation/unfinished --
    never as lost orders."""
    cfg = apply_overrides(
        _cfg(),
        {
            "arrivals.demand_multiplier": 10.0,
            "courier.n_couriers": 1,
            "picking.n_pickers": 1,
        },
    )
    result = run_once(cfg, seed=2)
    m = replication_metrics(result, cfg)
    assert m["n_accepted"] > 0
    assert m["service_level"] < 0.5  # cannot be reliable when massively overloaded
    assert m["completion_rate"] <= 1.0
    # conservation still holds under stress
    assert (
        m["n_completed"]
        + m["n_cancelled"]
        + m["n_unfulfilled_stockout"]
        + m["n_unfulfilled_horizon"]
        == m["n_accepted"]
    )


def test_more_couriers_cannot_worsen_courier_wait():
    """Monotonicity sanity check: adding couriers should not increase the mean
    wait-for-courier (holding demand fixed, same seed stream)."""
    base = apply_overrides(_cfg(), {"courier.n_couriers": 2})
    more = apply_overrides(_cfg(), {"courier.n_couriers": 8})
    mb = replication_metrics(run_once(base, seed=4), base)
    mm = replication_metrics(run_once(more, seed=4), more)
    assert mm["wait_courier_mean_min"] <= mb["wait_courier_mean_min"] + 1e-6


def test_stockout_orders_are_counted_not_dropped():
    cfg = apply_overrides(_cfg(), {"inventory.availability_prob": 0.5})
    result = run_once(cfg, seed=6)
    stockouts = [o for o in result.orders if o.state == OrderState.UNFULFILLED_STOCKOUT]
    assert len(stockouts) > 0
    # stockouts never start picking
    assert all(o.t_pick_start is None for o in stockouts)
