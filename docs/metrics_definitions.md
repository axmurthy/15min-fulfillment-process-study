# Phase 2 - Metric Definitions (defined BEFORE calculating)

All metrics are computed per **replication** (one independent simulation run) over
the measured window `[warmup_min, horizon_min)`. The observational unit for every
exported row is therefore **one replication**, never one order. Code:
[`src/gdsim/metrics.py`](../src/gdsim/metrics.py), [`src/gdsim/costs.py`](../src/gdsim/costs.py).

## Counts (conservation)

| Metric | Definition |
|---|---|
| `n_accepted` | Orders accepted inside the window. |
| `n_completed` | Delivered. |
| `n_on_time` | Delivered with `order_to_door <= target_min`. |
| `n_cancelled` | Abandoned before pickup. |
| `n_unfulfilled_stockout` | Not fulfillable (inventory). |
| `n_unfulfilled_horizon` | Unfinished at the horizon (backlog). |

Identity (checked by a test): `n_completed + n_cancelled + n_unfulfilled_stockout + n_unfulfilled_horizon = n_accepted`.

## Reliability (failures count against)

| Metric | Formula | Note |
|---|---|---|
| `service_level` | `n_on_time / n_accepted` | **The headline reliability number.** On-time deliveries over *all* accepted orders. Cancellations/stockouts/backlog reduce it. |
| `completion_rate` | `n_completed / n_accepted` | How many ever got delivered at all. |
| `late_rate` | `(n_completed - n_on_time) / n_accepted` | Delivered but past target. |
| `cancel_rate` | `n_cancelled / n_accepted` | |
| `unfulfilled_rate` | `(stockout + horizon) / n_accepted` | |

> Why not "on-time / completed"? Because dividing by completed hides the orders
> that failed. A service that cancels everything it can't deliver fast would look
> perfect. We divide by **accepted**.

## Delivery-time distribution (conditional on completion)

| Metric | Definition |
|---|---|
| `otd_median_min` | Median order-to-door time of **completed** orders. |
| `otd_p90_min`, `otd_p95_min` | 90th / 95th percentile (the tail customers actually feel). |
| `otd_mean_min` | Mean (reported, but the tail matters more for a speed promise). |

> These are **conditional on completion** (you can only time orders that
> finished). We always report them next to `completion_rate` so a
> fast-but-incomplete service cannot look good in isolation.

## Component waiting / processing (completed orders)

`wait_picker_mean_min`, `pick_pack_mean_min`, `wait_courier_mean_min` decompose
where the time goes, so we can see **which stage** drives the clock.

## Throughput and utilisation

| Metric | Definition | Interpretation trap avoided |
|---|---|---|
| `throughput_per_hr` | `n_completed / window_hours` | |
| `picker_utilization` | picker busy minutes / (pickers x window) | Busy = actual pick+pack time. |
| `courier_utilization` | courier **active** minutes / (couriers x window) | Active = load+travel+access+return. Idle reservation under `assign_at_accept` shows up as **low** active utilisation, not hidden work. |

> **High utilisation is not good service.** A fully-utilised courier fleet means
> long queues. We always read utilisation *against* service level and P90 time.

## Cost and economics

| Metric | Definition | Honesty guardrail |
|---|---|---|
| `operating_cost_usd` | picker labour + courier labour + rent allocation + packaging, over the window | Labour is paid for **staffed** time (idle + repositioning included), not just busy time. |
| `cost_per_completed_usd` | `operating_cost / n_completed` | A cost-to-serve, **not** a margin. |
| `retained_rev_per_order_usd` | `AOV x margin + delivery_fee + ad_revenue` | Operator-retained revenue, **not** AOV (grocery sales). |
| `variable_cost_per_order_usd` | packaging + shrink (+ per-order courier pay if gig) | |
| `contribution_per_order_usd` | `retained_rev - variable_cost` | **Contribution is NOT profit.** It excludes staffed labour + rent, which the operating-cost metrics carry. |
| `operating_profit_window_usd` | `retained_rev x n_completed - operating_cost` | The honest "does the window pay for itself" number. |

## What we deliberately do NOT compute

- **No capability indices (Cp/Cpk) or Six Sigma scores.** Order-to-door time is
  not a normally-distributed quality characteristic from a stable process with a
  two-sided spec; forcing capability math here would be false precision.
- **No single "optimal" configuration.** We report trade-offs and conditional
  recommendations.

## Simulation uncertainty vs assumption uncertainty

- **Simulation uncertainty**: scatter of a metric across replications at fixed
  inputs. Quantified by the 95% CI half-width in the `*_summary.csv` files
  (`summarize()` in [`experiment.py`](../src/gdsim/experiment.py)).
- **Assumption uncertainty**: how much results move when we change the *inputs*
  (demand, speed, costs). Quantified by the scenario DOE and Phase 6 sensitivity.

These are reported **separately** and never added together.
