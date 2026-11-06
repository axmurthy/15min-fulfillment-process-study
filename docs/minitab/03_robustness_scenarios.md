# Analysis 03 - Robustness across uncertain scenarios

## The question
Our demand and travel-speed assumptions are uncertain. **Which controllable
settings keep service high even when demand is high and couriers are slow?** A
setting that only works in the good scenario is not a real recommendation.

## Why this method fits
We cross the controllable factorial with **scenario factors** (demand multiplier,
courier speed). By putting the scenario factors in the model, we can see whether a
controllable factor's benefit **survives** the bad scenario - i.e., we look for
control x scenario interactions. This separates a robust improvement from a
fragile one.

## Data
- **File:** `experiments/scenario_doe_replications.csv`
- **Observational unit:** one replication. 8 controllable corner points x 4
  scenarios (demand_mult 1.0/1.5 x speed 15/10) x ~10 replications.
- **Controllable factors:** `radius_km`, `pickers`, `couriers`.
- **Scenario factors:** `demand_mult`, `speed_kmh`.
- **Response:** `service_level` (repeat for `otd_p90_min`).

## Steps (Minitab Web)
Because this mixes controllable and scenario factors, the cleanest tool is a
General Linear Model (it handles all five factors and their interactions without
needing a formal DOE object).

1. Import the CSV (see [overview](00_overview.md)).
2. **STAT > ANOVA > General Linear Model > Fit General Linear Model**.
3. In the side panel, set **Responses** to `service_level`.
4. Under **Factors**, add `radius_km`, `pickers`, `couriers`, `demand_mult`,
   `speed_kmh`. (For a first pass, enter all five as **Factors** so you get
   level-mean comparisons. You can switch some to **Covariates** later if you
   prefer slopes.)
5. Click **Model...** and add the 2-way interaction terms you care about:
   `couriers*demand_mult`, `radius_km*speed_kmh`, `pickers*demand_mult`. Click
   **OK**.
6. Click **Graphs...** and tick **Four in one** residual plots. Click **OK**,
   then **OK** again to run.
7. For interaction visuals: **STAT > ANOVA > General Linear Model > Factorial
   Plots** (or **STAT > ANOVA > Interaction Plot**). Select the pairs
   `couriers*demand_mult` and `radius_km*speed_kmh`. Click **OK**.

## Assumption checks
- **Residuals:** as in Analysis 02, watch for non-constant variance on the
  bounded `service_level`; `otd_p90_min` is often better behaved.
- **Balance:** the design is balanced (equal replications per cell), which keeps
  the ANOVA interpretation clean.
- **Scenario factors are NOT controllable:** interpret their main effects as
  "the world got harder," not as a lever you can pull.

## Plain-English interpretation (what we expect)
- A strong **demand_mult** main effect (service drops when demand rises) and a
  **speed** effect (slower couriers -> worse service, worse at larger radius).
- The useful part is the **interactions**: if `couriers*demand_mult` is large,
  extra couriers matter most exactly when demand is high - so staffing to the
  peak is the robust move. If `radius_km*speed_kmh` is large, a wide radius is
  especially dangerous when couriers are slow (congestion/rain) - so a smaller
  radius is the robust hedge.
- **Robust recommendation logic:** pick the controllable settings whose benefit
  holds in the *worst* scenario cell, not the average.

## Result
Radius × speed: the two speed lines spread at 2 km — a wide radius is fragile
when couriers are slow. Couriers × demand: extra riders help more when demand is
high, but only if picking keeps up.

In the worst cell (demand 1.5×, speed 10 km/h), **1 km + 4 pickers + 10
couriers** held service around 0.66. The same 1 km with only 2 pickers fell to
~0.18 even with 10 couriers. All 2 km setups in that cell were ~0.06-0.15.
Wide radius can look acceptable on a good day and fail when conditions are bad.
