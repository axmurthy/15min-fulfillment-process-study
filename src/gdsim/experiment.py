"""Run replications and designed experiments.

Independence of replications is the whole point of exporting replication-level
data for Minitab: each row of the exported CSV is ONE independent simulation run
(its own random-number stream via SeedSequence.spawn). Orders sharing a queue
within a run are NOT independent and are therefore never exported as separate
experimental units -- they are collapsed into that run's summary metrics first.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import costs as cost_mod
from . import metrics as metric_mod
from .config import apply_overrides
from .model import run_once


def _child_seeds(base_seed: int, n: int) -> list[np.random.SeedSequence]:
    """n independent seed streams derived from one master seed (reproducible)."""
    return np.random.SeedSequence(base_seed).spawn(n)


def run_scenario(
    cfg,
    n_reps: int | None = None,
    base_seed: int | None = None,
    factor_cols: dict | None = None,
) -> pd.DataFrame:
    """Run n independent replications of one configuration.

    Returns a DataFrame with one row per replication (the independent unit),
    combining service metrics and cost metrics, plus any factor columns passed in.
    """
    n_reps = int(n_reps if n_reps is not None else cfg.simulation.n_replications)
    base_seed = int(base_seed if base_seed is not None else cfg.meta.base_seed)
    factor_cols = factor_cols or {}

    rows = []
    for rep, seed_seq in enumerate(_child_seeds(base_seed, n_reps)):
        result = run_once(cfg, seed_seq)
        rep_m = metric_mod.replication_metrics(result, cfg)
        cost_m = cost_mod.cost_metrics(rep_m, cfg)
        row = {"replication": rep, **factor_cols, **rep_m, **cost_m}
        rows.append(row)
    return pd.DataFrame(rows)


@dataclass
class Factor:
    """A controllable or scenario factor in a designed experiment."""
    name: str          # short label used as a CSV column (e.g. "radius_km")
    dotted_key: str    # config path it overrides (e.g. "geography.service_radius_km")


def run_design(
    cfg,
    factors: list[Factor],
    design_points: list[dict],
    n_reps: int | None = None,
    base_seed: int | None = None,
) -> pd.DataFrame:
    """Run a designed experiment.

    design_points: list of dicts mapping factor.name -> level value.
    Every design point gets its OWN independent set of replications (fresh seed
    stream offset by the point index) so points are not accidentally correlated.
    Output: one row per (design point, replication).
    """
    n_reps = int(n_reps if n_reps is not None else cfg.simulation.n_replications)
    base_seed = int(base_seed if base_seed is not None else cfg.meta.base_seed)
    name_to_key = {f.name: f.dotted_key for f in factors}

    frames = []
    for idx, point in enumerate(design_points):
        overrides = {name_to_key[name]: lvl for name, lvl in point.items()}
        cfg_point = apply_overrides(cfg, overrides)
        df = run_scenario(
            cfg_point,
            n_reps=n_reps,
            base_seed=base_seed + 1000 * (idx + 1),  # distinct stream per point
            factor_cols={"design_point": idx, **point},
        )
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def summarize(df: pd.DataFrame, by: list[str], metrics: list[str]) -> pd.DataFrame:
    """Point-level summary: mean, std, and a 95% CI half-width for the MEAN of
    each metric across replications (this is SIMULATION uncertainty -- distinct
    from uncertainty in the input assumptions, which sensitivity analysis covers).
    """
    out = []
    for keys, grp in df.groupby(by):
        keys = keys if isinstance(keys, tuple) else (keys,)
        rec = dict(zip(by, keys))
        n = len(grp)
        for m in metrics:
            vals = grp[m].to_numpy(dtype=float)
            mean = float(np.nanmean(vals))
            std = float(np.nanstd(vals, ddof=1)) if n > 1 else 0.0
            half = 1.96 * std / np.sqrt(n) if n > 1 else 0.0
            rec[f"{m}_mean"] = mean
            rec[f"{m}_std"] = std
            rec[f"{m}_ci95_halfwidth"] = half
        rec["n_reps"] = n
        out.append(rec)
    return pd.DataFrame(out)
