# Analysis 01 - Graphical Summary of the Baseline

## The question
How does the baseline configuration behave, and how much does it vary from run to
run? Before any fancy modelling, a process engineer looks at the **distribution**
and the **variation**, not just an average.

## Why this method fits
A Graphical Summary shows the histogram, mean, median, standard deviation,
confidence interval, and a normality check all at once. It builds the habit of
asking "how spread out is this?" and "is the average even a sensible summary?"
before drawing conclusions.

## Data
- **File:** `results/baseline_replications.csv`
- **Observational unit:** one replication (20 rows).
- **Columns to focus on:** `service_level`, `otd_p90_min`, `completion_rate`,
  `courier_utilization`, `cost_per_completed_usd`.

## Steps (Minitab Web)
1. Import the CSV (see [overview](00_overview.md)).
2. In the top toolbar, click **STAT > Basic Statistics > Graphical Summary**.
3. A side panel opens. In the **Variables** box, double-click (or drag)
   `service_level` from the column list to add it. Click **OK**.
4. The output pane shows the summary: histogram, mean, median, StDev, the 95% CI
   for the mean, and the Anderson-Darling normality p-value.
5. Repeat for `otd_p90_min` and `cost_per_completed_usd` (run the command again
   with a different variable each time, or enter multiple variables at once).

## Assumption checks / what to look at
- **Is the mean representative?** If the histogram is skewed or the mean and
  median differ a lot, prefer the median and report the spread.
- **Normality (Anderson-Darling p):** you do **not** need normality to *describe*
  the baseline. You only care about it later if you build models that assume it.
  Note the p-value; don't act on it yet.
- **Simulation uncertainty:** the 95% CI for the mean is the run-to-run noise at
  fixed inputs. If it's wide, you need more replications before comparing options.

## Plain-English interpretation (what we expect)
In our runs the baseline lands around **service_level ~0.70**, **median
order-to-door ~12-13 min**, but **P90 ~16 min** - i.e., the *typical* order beats
15 minutes while the *slow tail* breaches it, mostly during the peak period. That
gap between median and P90 is the whole story: a "15-minute" promise is a
statement about the **tail**, not the average.

## Result
Across 20 baseline replications, mean `service_level` is about 0.70 (95% CI for
the mean roughly 0.66-0.75). That interval is **simulation noise at fixed
inputs**, not uncertainty about real Mission demand.

Median order-to-door is ~12 min (inside the promise) while P90 is ~16 min. The
typical order meets 15 minutes; the slow tail does not. A 15-minute service claim
is a statement about that tail.
