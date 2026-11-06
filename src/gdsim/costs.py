"""Cost and contribution accounting at the replication level.

Honesty guardrails baked in here:
- Labour is paid for STAFFED time, not just busy time: idle pickers/couriers and
  courier repositioning are all included in operating cost.
- "operating cost per completed order" includes a transparent facility-rent
  allocation; it is a cost-to-serve number, NOT a margin.
- "contribution per order" subtracts only variable costs from operator-RETAINED
  revenue. It is explicitly NOT profit (it ignores staffed labour + rent, which
  the operating-cost figures carry instead). We also keep operator-retained
  revenue distinct from AOV (grocery sales): the operator keeps a margin + fees
  + ad revenue, not the whole basket value.
"""
from __future__ import annotations


def retained_revenue_per_order(cfg) -> float:
    e = cfg.economics
    return (
        float(e.aov_usd) * float(e.product_margin_frac)
        + float(e.delivery_fee_usd)
        + float(e.ad_revenue_per_order_usd)
    )


def variable_cost_per_order(cfg) -> float:
    """Per-order variable cost (excludes staffed labour + rent)."""
    c = cfg.costs
    e = cfg.economics
    cost = float(c.packaging_per_order) + float(e.aov_usd) * float(e.shrink_frac)
    if c.courier_pay_model == "per_order":
        cost += float(c.courier_per_order)
    return cost


def cost_metrics(rep: dict, cfg) -> dict:
    """Given replication metrics (counts) + config, compute cost/economics."""
    window_min = float(rep["window_min"])
    window_hr = window_min / 60.0
    completed = int(rep["n_completed"])
    c = cfg.costs

    # Labour paid for the staffed window (idle time included).
    picker_cost = int(cfg.picking.n_pickers) * float(c.picker_wage_per_hr) * window_hr
    if c.courier_pay_model == "hourly":
        courier_cost = (
            int(cfg.courier.n_couriers) * float(c.courier_wage_per_hr) * window_hr
        )
    else:  # per_order -- only paid for completed deliveries
        courier_cost = float(c.courier_per_order) * completed

    # Facility rent allocated to the window by operating hours.
    rent_per_hr = float(c.mfc_rent_per_day) / float(c.operating_hours_per_day)
    rent_cost = rent_per_hr * window_hr

    packaging_cost = float(c.packaging_per_order) * completed
    operating_cost = picker_cost + courier_cost + rent_cost + packaging_cost

    retained = retained_revenue_per_order(cfg)
    var_cost = variable_cost_per_order(cfg)
    contribution = retained - var_cost  # per order; NOT profit

    total_retained_rev = retained * completed
    operating_profit = total_retained_rev - operating_cost  # over the window

    def safe_div(a, b):
        return float(a / b) if b else float("nan")

    return {
        "picker_cost_usd": picker_cost,
        "courier_cost_usd": courier_cost,
        "rent_cost_usd": rent_cost,
        "packaging_cost_usd": packaging_cost,
        "operating_cost_usd": operating_cost,
        "cost_per_completed_usd": safe_div(operating_cost, completed),
        "retained_rev_per_order_usd": retained,
        "variable_cost_per_order_usd": var_cost,
        "contribution_per_order_usd": contribution,
        "operating_profit_window_usd": operating_profit,
        "operating_profit_per_completed_usd": safe_div(operating_profit, completed),
    }
