# Analysis 04 - Comparing improvement alternatives

## The question
Do the targeted improvements (`wider_radius`, `peak_staffing`, `faster_picking`,
`dispatch_at_ready`) actually beat the `baseline`, or are the differences just
simulation noise? And what does each cost?

## Why this method fits
We have one categorical grouping (`alternative`) with independent replications in
each group. **One-way ANOVA** tests whether the group means differ; **Tukey**
pairwise comparisons tell us *which* alternatives differ while controlling the
family-wise error rate (so we don't fool ourselves by making many comparisons).

## Data
- **File:** `results/improvements_replications.csv`
- **Observational unit:** one replication (~20 per alternative).
- **Grouping:** `alternative` (text).
- **Responses:** `service_level`, `otd_p90_min`, `cost_per_completed_usd`.

## Steps (Minitab Web)
1. Import the CSV (see [overview](00_overview.md)).
2. First, **see** it: **GRAPH > Boxplot > One variable, categorical**.
   Variable = `service_level`, categorical variable = `alternative`. Click **OK**.
   Repeat for `otd_p90_min` and `cost_per_completed_usd`.
   (Web does not have desktop's "One Y With Groups"; "One variable" with no
   category mixes all alternatives together.)
3. **STAT > ANOVA > One-Way**.
4. In the side panel, set **Response** to `service_level` and **Factor** to
   `alternative`.
5. Click **Comparisons...** and tick **Tukey**. Click **OK**. Then click
   **Graphs...** and tick the **Four in one** residual plots and the **Interval
   plot**. Click **OK**, then **OK** again to run.
6. Repeat the One-Way ANOVA for `otd_p90_min` and `cost_per_completed_usd`.

## Assumption checks
- **Equal variances:** One-Way ANOVA assumes similar spread across groups. Check
  the residual-vs-fits plot, or run **STAT > ANOVA > Test for Equal Variances**.
  If variances differ a lot, use the **Welch's** option (available inside the
  One-Way dialog's **Options...** button) or compare with **Games-Howell**
  instead of Tukey.
- **Independence:** satisfied by construction - replications are independent.
- **Normality:** ANOVA is fairly robust with ~20 per group; check the residual
  normal plot but don't over-react to a small deviation.

## Plain-English interpretation (what we found)
From our runs (means across replications):

| Alternative | service_level | P90 (min) | cost/completed (USD) |
|---|---|---|---|
| baseline | 0.705 | 16.2 | 16.0 |
| faster_picking | **0.795** | **14.8** | 15.9 |
| peak_staffing | 0.785 | 15.1 | **22.3** |
| dispatch_at_ready | 0.706 | 16.6 | 16.0 |
| wider_radius | **0.496** | 19.7 | 16.6 |

Reading this like an engineer:
- **faster_picking** (better slotting/layout, lower per-item time) gives the best
  service *and* meets the 15-min P90, at essentially baseline cost - the best
  value lever, because at these settings picking is part of the binding
  constraint.
- **peak_staffing** also meets the target but is the most expensive - it buys
  service with labour; use it only when demand genuinely needs it.
- **dispatch_at_ready** barely moves service here - it frees reserved couriers but
  at this fleet size it isn't the binding constraint.
- **wider_radius** is actively **harmful**: extending coverage lengthens travel,
  collapsing service to ~50% and blowing past the P90 target. Coverage trades
  directly against speed.

Use Tukey to confirm which of these differences survive simulation noise (the
baseline vs dispatch_at_ready difference almost certainly does **not**).

## Result
`dispatch_at_ready` is indistinguishable from baseline (dispatch was not the
bottleneck at this fleet size). `faster_picking` is the recommended change:
higher service, P90 under 15 min, cost unchanged. `peak_staffing` is the
alternative when picking is already as fast as it can get and rush-hour labour
is the remaining constraint — it works, at ~39% higher cost per completed order.
`wider_radius` is harmful: longer trips push the tail past the promise.
