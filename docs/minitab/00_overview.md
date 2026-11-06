# Minitab analysis (overview)

These are experiments **on a simulation model**, not field experiments. They
do not prove a real-world effect. They are the statistical workflow used to
screen critical parameters and read service-versus-cost trade-offs.

## Environment: Minitab Web

Menu paths below are for **Minitab Web** (`app.minitab.com`). Methods match the
desktop app; layout differs:

- **Data lives in projects.** You upload CSVs into a project rather than opening
  a file from disk.
- **Menus run along the top toolbar:** `STAT`, `GRAPH`, `DOE`, etc. Click a
  toolbar heading to expand it, then follow the sub-menus exactly as written.
- **Dialogs appear as side panels** (not pop-up windows). Fill them in and click
  the blue **OK** / **Submit** button at the bottom of the panel.
- **Output appears in the output pane** (right side). You can scroll, export, or
  screenshot from there. Session graphs are **not** stored in this repo: the
  CSVs in `results/` and `experiments/` plus these guides are the reproducible
  Minitab record. Import the CSV and re-run the menus to recreate the plots.

## The four analyses

| # | File | Question | Method |
|---|---|---|---|
| [01](01_graphical_summary.md) | `results/baseline_replications.csv` | How does the baseline behave, and how much does it vary run-to-run? | Graphical Summary + descriptive stats |
| [02](02_factorial_doe.md) | `experiments/factorial_doe_corners.csv` | Which controllable factors (radius, pickers, couriers) critically drive service, and do they interact? | GLM on the 2-level corners (Web has no Define Custom Factorial Design) |
| [03](03_robustness_scenarios.md) | `experiments/scenario_doe_replications.csv` | Which settings keep service high even under high demand / slow travel? | Factorial with scenario terms (robustness) |
| [04](04_compare_alternatives.md) | `results/improvements_replications.csv` | Do the targeted improvements beat the baseline, beyond simulation noise? | One-way ANOVA + Tukey comparisons |

## The golden rule for every import

**One row = one independent replication.** That is the experimental unit. Do not
split a row into per-order data and treat those orders as replicates: orders in
the same run share a queue and are correlated. The Python exporter already
collapses each run to one row.

## How to import a CSV into Minitab Web

1. Open your project in Minitab Web (`app.minitab.com`).
2. In the **data pane** (the spreadsheet area), click the **Open** icon or go to
   **File > Open Worksheet**.
3. Click **Browse** (or drag-and-drop), select your CSV, then click **Open**.
4. Minitab shows a preview - confirm the first row is read as **column names**
   (the header row, not data) and numeric columns are detected as numeric.
   Click **OK**.
5. Check the worksheet: factor columns (`radius_km`, `pickers`, `couriers`)
   should be numeric; `alternative` is text. If a numeric column was imported as
   text, right-click the column header > **Format Column** > **Numeric**.

## What we will NOT do (and why)

- **No capability analysis (Cp/Cpk) / Six Sigma scores.** The responses here are
  simulation summaries, not a stable, normally-distributed quality characteristic
  with a two-sided spec. Capability math would be false precision.
- **No claim of a single global optimum.** We report where each setting helps and
  where it fails.
