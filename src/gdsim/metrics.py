"""Turn a replication's raw orders into the metrics defined in
docs/metrics_definitions.md.

Important definitional choices (so results are honest):
- The measured window is [warmup_min, horizon_min). We only score orders
  ACCEPTED inside this window, so start-up transients don't flatter the result.
- "service_level" (reliability) is on-time deliveries divided by ALL accepted
  orders in the window -- cancellations, stockouts, and unfinished orders count
  AGAINST it. We never compute reliability on completed orders only.
- Percentile delivery times are, by necessity, conditional on completion; we
  label them that way and always report them next to the completion rate so a
  fast-but-incomplete service cannot look good.
- Utilisation is productive busy time over staffed time. For couriers we report
  "active" utilisation (load+travel+access+return); idle reservation under
  assign_at_accept is therefore visible as low active utilisation, not hidden.
"""
from __future__ import annotations

import numpy as np

from .model import OrderState, RunResult


def _percentile(values, q):
    if len(values) == 0:
        return float("nan")
    return float(np.percentile(values, q))


def replication_metrics(result: RunResult, cfg) -> dict:
    warmup = float(cfg.simulation.warmup_min)
    horizon = float(cfg.simulation.horizon_min)
    window_min = horizon - warmup
    window_hr = window_min / 60.0
    target = float(cfg.simulation.target_min)

    # Orders accepted inside the measured window.
    in_window = [o for o in result.orders if warmup <= o.t_accept < horizon]
    n_accepted = len(in_window)

    completed = [o for o in in_window if o.state == OrderState.COMPLETED]
    cancelled = [o for o in in_window if o.state == OrderState.CANCELLED]
    stockout = [o for o in in_window if o.state == OrderState.UNFULFILLED_STOCKOUT]
    horizon_fail = [o for o in in_window if o.state == OrderState.UNFULFILLED_HORIZON]

    otd = [o.order_to_door_min for o in completed]
    on_time = [o for o in completed if o.order_to_door_min <= target]

    # Component times over completed orders (minutes).
    wait_picker = [
        (o.t_pick_start - o.t_accept) for o in completed if o.t_pick_start is not None
    ]
    pick_pack = [o.pick_pack_min for o in completed]
    # Time a packed order waited for a courier to actually be present to hand off.
    wait_courier = [
        (o.t_handoff_start - o.t_pack_end)
        for o in completed
        if o.t_handoff_start is not None and o.t_pack_end is not None
    ]

    # Utilisation: productive busy minutes over staffed minutes in the window.
    picker_busy = sum(o.pick_pack_min for o in in_window if o.t_pick_start is not None)
    courier_busy = sum(o.courier_active_min for o in in_window)
    picker_cap_min = int(cfg.picking.n_pickers) * window_min
    courier_cap_min = int(cfg.courier.n_couriers) * window_min

    def safe_div(a, b):
        return float(a / b) if b else float("nan")

    return {
        # --- counts / conservation ---
        "n_accepted": n_accepted,
        "n_completed": len(completed),
        "n_on_time": len(on_time),
        "n_cancelled": len(cancelled),
        "n_unfulfilled_stockout": len(stockout),
        "n_unfulfilled_horizon": len(horizon_fail),
        # --- reliability (failures count against) ---
        "service_level": safe_div(len(on_time), n_accepted),
        "completion_rate": safe_div(len(completed), n_accepted),
        "late_rate": safe_div(len(completed) - len(on_time), n_accepted),
        "cancel_rate": safe_div(len(cancelled), n_accepted),
        "unfulfilled_rate": safe_div(len(stockout) + len(horizon_fail), n_accepted),
        # --- delivery time distribution (conditional on completion) ---
        "otd_median_min": _percentile(otd, 50),
        "otd_p90_min": _percentile(otd, 90),
        "otd_p95_min": _percentile(otd, 95),
        "otd_mean_min": float(np.mean(otd)) if otd else float("nan"),
        # --- component waiting / processing (completed orders) ---
        "wait_picker_mean_min": float(np.mean(wait_picker)) if wait_picker else 0.0,
        "pick_pack_mean_min": float(np.mean(pick_pack)) if pick_pack else 0.0,
        "wait_courier_mean_min": float(np.mean(wait_courier)) if wait_courier else 0.0,
        # --- throughput & utilisation ---
        "throughput_per_hr": safe_div(len(completed), window_hr),
        "picker_utilization": safe_div(picker_busy, picker_cap_min),
        "courier_utilization": safe_div(courier_busy, courier_cap_min),
        # context
        "window_min": window_min,
    }
