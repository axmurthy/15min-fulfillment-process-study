# Data Dictionary - exported CSVs

**Observational unit for every row: one independent simulation replication.**
Orders that shared a queue within a run are collapsed into that run's metrics
first; individual orders are never exported as separate rows (they are not
independent and must not be treated as experimental replicates).

Files:
- `results/baseline_replications.csv` - baseline config, one row per replication.
- `experiments/factorial_doe_replications.csv` - 2^3 (+centre) controllable DOE.
- `experiments/factorial_doe_summary.csv` - point-level means + 95% CI half-widths.
- `experiments/scenario_doe_replications.csv` - controllable DOE x scenario grid.
- `results/improvements_replications.csv` - baseline vs named alternatives.

## Identifier / factor columns

| Column | Meaning |
|---|---|
| `replication` | Replication index within a design point (0-based). |
| `design_point` | Design-point index (DOE files). |
| `radius_km` | Service radius (controllable factor), km. |
| `pickers` | Picker count (controllable factor). |
| `couriers` | Courier count (controllable factor). |
| `demand_mult` | Scenario: arrival-rate multiplier (scenario DOE only). |
| `speed_kmh` | Scenario: courier speed, km/h (scenario DOE only). |
| `alternative` | Improvement name (improvements file only). |

## Count columns

| Column | Meaning |
|---|---|
| `n_accepted` | Orders accepted in the measured window. |
| `n_completed` | Delivered. |
| `n_on_time` | Delivered within the 15-min target. |
| `n_cancelled` | Abandoned before pickup. |
| `n_unfulfilled_stockout` | Not fulfillable (inventory). |
| `n_unfulfilled_horizon` | Unfinished at the horizon (backlog). |

## Response columns (use these as DOE responses)

| Column | Meaning | Units |
|---|---|---|
| `service_level` | on-time / accepted (headline reliability) | fraction 0-1 |
| `completion_rate` | completed / accepted | fraction |
| `late_rate`, `cancel_rate`, `unfulfilled_rate` | failure breakdown / accepted | fraction |
| `otd_median_min`, `otd_p90_min`, `otd_p95_min`, `otd_mean_min` | delivery-time distribution (completed orders) | minutes |
| `wait_picker_mean_min`, `pick_pack_mean_min`, `wait_courier_mean_min` | component times | minutes |
| `throughput_per_hr` | completed per hour | orders/hr |
| `picker_utilization`, `courier_utilization` | busy / staffed | fraction |
| `window_min` | measured window length | minutes |
| `picker_cost_usd`, `courier_cost_usd`, `rent_cost_usd`, `packaging_cost_usd` | cost components over the window | USD |
| `operating_cost_usd` | total operating cost over the window | USD |
| `cost_per_completed_usd` | operating cost / completed | USD/order |
| `retained_rev_per_order_usd` | operator-retained revenue per order | USD/order |
| `variable_cost_per_order_usd` | per-order variable cost | USD/order |
| `contribution_per_order_usd` | retained_rev - variable_cost (NOT profit) | USD/order |
| `operating_profit_window_usd` | retained_rev x completed - operating_cost | USD |
| `operating_profit_per_completed_usd` | operating profit / completed | USD/order |

## Summary-file columns

For each metric `M`, the summary files add `M_mean`, `M_std`, and
`M_ci95_halfwidth` (half-width of the 95% confidence interval for the **mean**
across replications = simulation uncertainty), plus `n_reps`.
