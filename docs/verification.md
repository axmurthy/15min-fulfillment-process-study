# Phase 4 - Verification (and the limits of validation)

**Verification** answers "did we build the model right?" (does the code do what
we intended). **Validation** answers "did we build the right model?" (does it
match reality). This project can be **verified** but, because we have no observed
operational data, it **cannot be validated**. We are explicit about that.

## Software verification (automated: `pytest`)

Run: `.venv/bin/python -m pytest -q` (12 tests, all passing).

### 1. Hand-checkable cases ([`tests/test_verification.py`](../tests/test_verification.py))
With all randomness switched off (CV = 0, one order, abundant resources, radius
0), the order-to-door time must equal a pencil-and-paper identity:

```
order_to_door = pick_pack + load + travel_out + access
pick_pack     = setup + per_item * items + pack
travel_out    = distance / speed * 60
```

- `test_single_order_hand_check` asserts this identity exactly.
- `test_travel_scales_with_distance` confirms travel grows exactly as
  `distance / speed * 60` when the radius is non-zero.
- `test_reproducibility_same_seed` / `test_different_seed_differs` confirm the
  single-seed reproducibility and that distinct seeds give distinct draws.

### 2. Conservation checks ([`tests/test_conservation.py`](../tests/test_conservation.py))
- Every order ends in exactly one terminal state (no order is created and lost).
- State counts sum to the total; the in-window metric counts sum to `n_accepted`.
- `n_on_time <= n_completed`; completed orders have a monotonic timeline
  (`t_pick_start <= t_pack_end <= ... <= t_delivered`).

### 3. Extreme scenarios ([`tests/test_extremes.py`](../tests/test_extremes.py))
- **Zero demand** -> zero orders.
- **Saturation** (10x demand, 1 courier, 1 picker) -> service collapses below
  0.5, conservation still holds, no crash; the shortfall appears as
  lateness/cancellation/backlog, never as lost orders.
- **Monotonicity**: adding couriers does not increase mean wait-for-courier.
- **Stockouts** are counted and never start picking.

## Model documentation (for reproducibility)

| Item | Value / location |
|---|---|
| Initialization | Store starts empty; `_source` generates arrivals from t=0. |
| Warm-up | Orders accepted before `warmup_min` (30) excluded from metrics. |
| Run duration | `horizon_min` (240) per replication. |
| Unfinished orders | Counted as `unfulfilled_horizon` (not discarded). |
| Replications | `n_replications` independent runs via `SeedSequence.spawn`. |
| Reproducibility | Single master seed `meta.base_seed`; every draw traces to it. |

## Why validation is not possible here

We have no observed order-to-door times, pick rates, or courier GPS traces for
any real operator (those are proprietary; see `data/sources_register.csv`).
Therefore we **cannot** check the model's outputs against reality. Every result
is **conditional on the assumptions** in `config.yaml`. The Phase 7 pilot plan
lists exactly what a real operator would have to measure to validate the model.

A verified simulation with transparent assumptions is a legitimate
**process-design** tool: it tells us how the *system* behaves given its rules. It
is not evidence about any specific company's real performance, and we never
present it as such.
