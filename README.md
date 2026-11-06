# 15-Minute Fulfillment Process Study

A **simulation-based process-design study** of a 15-minute grocery dark store
serving one Bay Area neighbourhood (San Francisco Mission District).

**Question:** under what operating conditions could that service be reliable
*and* economically viable?

This is a model of a process, not an empirical diagnosis of Blinkit, Zepto,
Gopuff, or any operator. No order-level company data is used or invented. Every
input is tagged Observed / Published / Assumption in
[`data/sources_register.csv`](data/sources_register.csv).

Guardrails used throughout:

- Population density is not order demand.
- Routing estimates are not observed delivery times.
- Grocery sales (AOV) are not revenue retained by the operator.
- Contribution is not profit; high utilisation is not good service.
- Failed orders are never dropped to flatter reliability.

## Findings (conditional on `config.yaml`)

- Baseline **median** order-to-door is ~12 min; **P90** is ~16 min. A 15-minute
  promise is a claim about the tail, not the typical order.
- **Critical parameters:** service radius and picker count. Courier count helps
  mainly when picking can keep up or trips are long (interactions).
- **Best-value change:** faster picking (layout/slotting) meets the P90 at
  essentially baseline cost. Widening the radius to 2 km collapsed on-time
  service from ~70% to ~50%.
- On a high-demand, slow-travel day, the setting that held up was **1 km, 4
  pickers, 10 couriers**. Wide-radius setups collapsed.
- Results are **sensitive** to demand, courier speed, and basket size, and
  **insensitive** to AOV (AOV moves contribution, not operations).
- Operational feasibility is plausible under those tight conditions. Fully loaded
  cost-to-serve still exceeds modelled retained revenue at baseline volume, so
  this is **not** a profitability claim.

Full write-up: [`docs/recommendation.md`](docs/recommendation.md).

## Reproduce

```bash
python3 -m venv .venv            # Python 3.11+ (tested on 3.14)
.venv/bin/python -m pip install -r requirements.txt

PYTHONPATH=src .venv/bin/python -m gdsim.cli baseline
PYTHONPATH=src .venv/bin/python -m gdsim.cli doe
PYTHONPATH=src .venv/bin/python -m gdsim.cli scenario-doe
PYTHONPATH=src .venv/bin/python -m gdsim.cli improve
PYTHONPATH=src .venv/bin/python -m gdsim.cli confirm
PYTHONPATH=src .venv/bin/python -m gdsim.cli sensitivity
PYTHONPATH=src .venv/bin/python -m gdsim.cli dashboard

.venv/bin/python -m pytest -q
```

Randomness comes from one master seed (`meta.base_seed` in
[`config.yaml`](config.yaml)). Replications use independent streams via
`numpy.random.SeedSequence.spawn`.

## Repository layout

| Path | Contents |
|---|---|
| [`docs/scope_memo.md`](docs/scope_memo.md) | Neighbourhood choice and data gaps |
| [`docs/process_map.md`](docs/process_map.md) | Order-to-door process and clock |
| [`docs/metrics_definitions.md`](docs/metrics_definitions.md) | Metric definitions (before calculation) |
| [`src/gdsim/`](src/gdsim) | Discrete-event simulation (SimPy) |
| [`tests/`](tests), [`docs/verification.md`](docs/verification.md) | Software verification (not real-world validation) |
| [`docs/minitab/`](docs/minitab) | How to analyse the exported CSVs in Minitab Web |
| [`docs/improvements.md`](docs/improvements.md) | Alternatives, costs, sensitivity |
| [`dashboard/`](dashboard) | Service-versus-cost figure |

## Minitab Web

Analyses were run in **Minitab Web**. Menu paths are in
[`docs/minitab/`](docs/minitab). Session files are not in the repo; import these
CSVs to recreate the work.

| Analysis | File |
|---|---|
| 01 Graphical summary | `results/baseline_replications.csv` |
| 02 Critical parameters (GLM) | `experiments/factorial_doe_corners.csv` |
| 03 Robustness | `experiments/scenario_doe_replications.csv` |
| 04 Alternatives (boxplot + One-Way) | `results/improvements_replications.csv` |

Web notes: **GRAPH > Boxplot > One variable, categorical**. Web typically has
**Create Factorial Design** but not **Define Custom**; Analysis 02 uses a general
linear model instead. One CSV row is one independent replication — not one order.

## Secrets

No API keys are required to run the simulation. If Census or mapping keys are
added later, put them in `.env` (gitignored).
