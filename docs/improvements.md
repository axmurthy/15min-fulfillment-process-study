# Phase 6 - Improvements, Trade-offs, and Robustness

All numbers below are **simulation results under the assumptions in
`config.yaml`**. They describe how the modelled *system* behaves; they are not
measurements of any real operator. Reproduce with:

```
python -m gdsim.cli improve --reps 20
python -m gdsim.cli confirm --reps 30
python -m gdsim.cli sensitivity --reps 15
python -m gdsim.cli scenario-doe --reps 10
```

## Baseline vs alternatives (`results/improvements_summary.csv`)

| Alternative | What changes | service_level | P90 (min) | cost/completed (USD) | Verdict |
|---|---|---|---|---|---|
| baseline | - | 0.705 | 16.2 | 16.0 | typical order beats 15 min, tail doesn't |
| **faster_picking** | per-item pick time 0.35 -> 0.25 (better slotting/layout) | **0.795** | **14.8** | 15.9 | **best value**: meets P90, ~no extra cost |
| peak_staffing | pickers 3->4, couriers 8->12 | 0.785 | 15.1 | 22.3 | works, but +39% cost/order |
| dispatch_at_ready | reserve courier only when packed | 0.706 | 16.6 | 16.0 | no real change at this fleet size |
| wider_radius | radius 1.5 -> 2.0 km | 0.496 | 19.7 | 16.6 | **harmful**: coverage kills speed |

### Where each helps and where it fails
- **faster_picking helps** because, at baseline demand, the picking stage is part
  of the binding constraint; shaving per-item time lifts throughput and cuts the
  P90 tail at essentially no extra operating cost. It **fails** if picking is not
  the constraint (e.g., very few couriers), where it just moves the queue to
  delivery.
- **peak_staffing helps** service by adding capacity on both stages, but it is
  the **most expensive** option (idle labour in off-peak inflates
  cost-per-order). It **fails** the economics test unless demand is high enough to
  keep the extra staff busy.
- **dispatch_at_ready** frees couriers from idle reservation, but at 8 couriers
  delivery is not the pinch point, so it barely moves service. It would matter
  more when couriers are scarce.
- **wider_radius fails**: a 2 km radius lengthens every trip (and the return),
  pushing P90 to ~20 min and collapsing service to ~50%. **Coverage trades
  directly against speed** - the single clearest trade-off in the study.

## Capacity adds help until they move the bottleneck
The factorial DOE (`experiments/factorial_doe_summary.csv`) shows couriers have a
large positive effect until delivery stops being the constraint; past that,
adding couriers stops helping and picking becomes the limit. This is the
classic "adding capacity only moves the bottleneck" result, and it is why
`faster_picking` (attacking the *other* stage) is so effective at the baseline.

## Fresh-seed confirmation (`results/confirmation_summary.csv`)
Re-running the leaders on a **new seed stream** (not used to choose them)
reproduces the ranking, so the effect is not a seed artefact:

| Alternative | service_level (95% CI half-width) | P90 (min) | cost/completed |
|---|---|---|---|
| baseline | 0.676 (+/-0.030) | 16.7 | 15.6 |
| faster_picking | 0.788 (+/-0.022) | 14.7 | 15.5 |
| peak_staffing | 0.764 (+/-0.021) | 15.1 | 21.7 |

## Sensitivity to assumptions (`results/sensitivity.csv`)
One-factor-at-a-time sweeps show **which beliefs the conclusion depends on**:

| Assumption | Swept range | Effect on service_level | Conclusion sensitivity |
|---|---|---|---|
| AOV | $18 -> $32 | none (0.72 throughout) | **Insensitive** - AOV changes contribution only, not operations. |
| demand multiplier | 0.8 -> 1.3 | 0.72 -> **0.51** | **Sensitive** - the service story holds only up to ~1.0-1.1x assumed demand. |
| courier speed | 10 -> 20 km/h | 0.47 -> 0.78 | **Very sensitive** - congestion/rain (10 km/h) breaks the target. |
| basket size | 6 -> 10 items | 0.81 -> 0.58 | **Sensitive** - bigger baskets lengthen picking and erode service. |

> Note: `contribution_per_order` is constant across the operational sweeps because
> it is a per-order economic identity (retained revenue minus per-order variable
> cost); operational levers show up instead in `cost_per_completed`, completed
> volume, and `operating_profit_window`.

## Robustness across scenarios
The scenario DOE crosses the controllable factorial with demand (1.0/1.5) and
speed (15/10 km/h). The robust reading: the settings that keep service highest in
the **worst** cell (high demand + slow couriers) are the small-radius,
adequately-couriered ones - not the wide-radius ones, which are fragile exactly
when conditions get hard. (Analyse this yourself in Minitab Analysis 03.)

## Safety and honesty guardrails respected
- No alternative relies on **unsafe courier speeds** or **skipped breaks**; speed
  is an assumption capped at a conservative effective value, and "improvements"
  are layout, staffing, dispatch, and radius - not "ride faster."
- **Batching was not modelled** as an improvement, because doing it honestly
  requires representing delivery sequencing and the extra wait the first order
  incurs; claiming batching gains without that would overstate the benefit.
- No "universal optimum" is claimed. Every recommendation is conditional.
