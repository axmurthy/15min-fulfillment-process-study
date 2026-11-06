# Analysis 02 - Factorial DOE: which parameters are critical?

## The question
Of the three things the operator can set - **service radius**, **picker count**,
**courier count** - which critically drive the service level and the P90 delivery
time, and do they **interact** (does the effect of one depend on another)?

## Why this method fits
A 2-level factorial design estimates every **main effect** and every
**interaction** with few runs, and it does so efficiently because it varies all
factors at once. It is the standard tool for screening critical process
parameters.

## Data
- **File:** `experiments/factorial_doe_replications.csv`
- **Observational unit:** one replication. There are 8 corner points + 1 centre
  point, each with ~15 replications (the replicates give an honest error estimate).
- **Factors:** `radius_km` (1.0, 2.0), `pickers` (2, 4), `couriers` (6, 10).
  The centre point is `radius_km=1.5, pickers=3, couriers=8`.
- **Responses:** start with `service_level`; repeat for `otd_p90_min`.

## Steps (Minitab Web)

**Do not use Create Factorial Design.** That generates a blank experiment plan.
Your design is already in the CSV. Minitab Web often has no **Define Custom
Factorial Design**, so we analyze with a **General Linear Model** instead. It
answers the same question (which factors and interactions matter) using the ANOVA
table rather than a DOE Pareto chart.

### A. Import the 2-level (corners-only) file
1. Import `experiments/factorial_doe_corners.csv` (see [overview](00_overview.md)).
   This is the factorial file with the centre point already removed: **120 rows**,
   `radius_km` is only 1.0 or 2.0, `pickers` 2 or 4, `couriers` 6 or 10.
2. Confirm those columns plus `service_level` and `otd_p90_min` are numeric.

   If you already imported `factorial_doe_replications.csv` (135 rows), do **not**
   use “between 1 and 2” — that often keeps only one endpoint (60 rows). Either
   switch to the corners file, or subset with **OR**: `radius_km = 1 OR radius_km = 2`
   (120 rows). The 15 centre-point rows (`radius_km=1.5`) are a curvature check,
   not a third factor level.

### B. Fit the model
2. **STAT > ANOVA > General Linear Model > Fit General Linear Model**.
3. **Responses:** `service_level`.
4. **Factors:** `radius_km`, `pickers`, `couriers`.
5. Click **Model...**. Include the three main effects and the three 2-way
   interactions (`radius_km*pickers`, `radius_km*couriers`, `pickers*couriers`).
   Click **OK**.
6. Click **Graphs...** and tick **Four in one** residual plots. Click **OK**,
   then **OK** to run.

### C. Visualize the effects
7. **STAT > ANOVA > Main Effects Plot**. Response = `service_level`. Factors =
   `radius_km`, `pickers`, `couriers`. Click **OK**.
8. **STAT > ANOVA > Interaction Plot**. Response = `service_level`. Factors =
   the same three. Click **OK**.

### D. Repeat for the tail
9. Repeat B and C with response = `otd_p90_min`.

If your Web menus differ (e.g. **STAT > ANOVA > Fit General Linear Model**
without the extra submenu, or **GRAPH** instead of **STAT** for the plots), use
the closest match. Do not start a new design.

## Assumption checks (the diagnostics that matter here)
- **Residual plots (four-in-one):** residuals should scatter randomly around 0
  with roughly constant spread. A funnel shape (variance grows with the fitted
  value) is common for a bounded fraction like `service_level`.
  - Fix if needed: re-run the analysis on `otd_p90_min` (a continuous minute
    value usually behaves better), or analyse a transformed response.
- **Centre point / curvature:** because we added a centre point, Minitab reports a
  curvature test. A significant curvature term warns that the response is **not
  linear** between the levels - so don't extrapolate; the true response bends.
- **Replicates = real error:** the replication rows give Minitab an honest
  estimate of pure error, so effect significance is meaningful (not pseudo-
  replication from correlated orders).

## Plain-English interpretation (what we expect)
From our runs you should see, for `service_level` and `otd_p90_min`:
- **Pickers**: large, helpful main effect (more pickers -> better service).
- **Couriers**: smaller main effect; helpful mainly through interactions, until
  delivery is no longer the bottleneck.
- **Radius**: **harmful** - a bigger radius lengthens travel, pushing P90 up and
  service down. This is the key counter-intuitive result: "more coverage" is not
  free; it trades directly against speed.
- **Interactions**: expect a radius x couriers interaction - extra couriers help
  more when the radius (and so travel time) is large. Read the interaction plot:
  **non-parallel lines = interaction**.

**Result:** the critical parameters are **service radius** and **picker count**
(largest F-values on both `service_level` and `otd_p90_min`). Courier count is
smaller as a main effect and shows up through interactions: extra couriers help
when the radius is large or when there are enough pickers, and they do almost
nothing if picking is the bottleneck. The centre-point mean (service_level ~0.69)
is better than the average of the eight corners (~0.50), so the response is not
a straight line between the low and high levels.
