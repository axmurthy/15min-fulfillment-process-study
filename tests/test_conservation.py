"""Phase 4 -- conservation checks: no order is created and then lost. Every
accepted order must end in exactly one terminal state.
"""
from __future__ import annotations

from gdsim.config import load_config
from gdsim.model import OrderState, run_once
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def test_every_order_has_terminal_state():
    cfg = load_config(CONFIG)
    result = run_once(cfg, seed=7)
    terminal = {
        OrderState.COMPLETED,
        OrderState.CANCELLED,
        OrderState.UNFULFILLED_STOCKOUT,
        OrderState.UNFULFILLED_HORIZON,
    }
    assert all(o.state in terminal for o in result.orders)
    assert all(o.state != OrderState.PENDING for o in result.orders)


def test_state_counts_sum_to_total():
    cfg = load_config(CONFIG)
    result = run_once(cfg, seed=11)
    total = len(result.orders)
    counts = {s: 0 for s in OrderState}
    for o in result.orders:
        counts[o.state] += 1
    accounted = (
        counts[OrderState.COMPLETED]
        + counts[OrderState.CANCELLED]
        + counts[OrderState.UNFULFILLED_STOCKOUT]
        + counts[OrderState.UNFULFILLED_HORIZON]
    )
    assert accounted == total
    assert counts[OrderState.PENDING] == 0


def test_metrics_counts_are_consistent():
    """Within the measured window, the metric counts must also add up."""
    from gdsim.metrics import replication_metrics

    cfg = load_config(CONFIG)
    result = run_once(cfg, seed=3)
    m = replication_metrics(result, cfg)
    assert (
        m["n_completed"]
        + m["n_cancelled"]
        + m["n_unfulfilled_stockout"]
        + m["n_unfulfilled_horizon"]
        == m["n_accepted"]
    )
    assert m["n_on_time"] <= m["n_completed"]


def test_completed_orders_have_full_timeline():
    cfg = load_config(CONFIG)
    result = run_once(cfg, seed=5)
    for o in result.orders:
        if o.state == OrderState.COMPLETED:
            assert o.t_pick_start is not None
            assert o.t_pack_end >= o.t_pick_start
            assert o.t_delivered >= o.t_handoff_start
            assert o.order_to_door_min > 0
