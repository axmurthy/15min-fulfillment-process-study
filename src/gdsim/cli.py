"""Command-line entry point.

Examples (run from the repo root with the venv active):
    python -m gdsim.cli baseline
    python -m gdsim.cli doe --reps 15
    python -m gdsim.cli scenario-doe --reps 10
    python -m gdsim.cli improve --reps 20
    python -m gdsim.cli dashboard
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import designs
from .config import apply_overrides, load_config
from .experiment import run_design, run_scenario, summarize

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
EXPERIMENTS = ROOT / "experiments"


def _ensure_dirs() -> None:
    RESULTS.mkdir(exist_ok=True)
    EXPERIMENTS.mkdir(exist_ok=True)


def cmd_baseline(args) -> None:
    cfg = load_config(args.config)
    df = run_scenario(cfg, n_reps=args.reps)
    _ensure_dirs()
    out = RESULTS / "baseline_replications.csv"
    df.to_csv(out, index=False)
    key = [
        "service_level",
        "completion_rate",
        "otd_median_min",
        "otd_p90_min",
        "picker_utilization",
        "courier_utilization",
        "cost_per_completed_usd",
        "contribution_per_order_usd",
    ]
    print(f"Baseline: {len(df)} replications -> {out}")
    print(df[key].describe().loc[["mean", "std", "min", "max"]].round(3).to_string())


def cmd_doe(args) -> None:
    cfg = load_config(args.config)
    factors = designs.CONTROLLABLE_FACTORS
    points = designs.factorial_2level(center=True)
    df = run_design(cfg, factors, points, n_reps=args.reps)
    _ensure_dirs()
    rep_out = EXPERIMENTS / "factorial_doe_replications.csv"
    df.to_csv(rep_out, index=False)

    by = ["design_point", "radius_km", "pickers", "couriers"]
    metrics = [
        "service_level",
        "otd_p90_min",
        "courier_utilization",
        "cost_per_completed_usd",
    ]
    summ = summarize(df, by=by, metrics=metrics)
    summ_out = EXPERIMENTS / "factorial_doe_summary.csv"
    summ.to_csv(summ_out, index=False)
    corners = df[df["radius_km"].isin([1.0, 2.0])].copy()
    corners_out = EXPERIMENTS / "factorial_doe_corners.csv"
    corners.to_csv(corners_out, index=False)
    print(f"Factorial DOE: {len(points)} points x {args.reps} reps -> {rep_out}")
    print(f"Point-level summary -> {summ_out}")
    print(f"2-level corners only ({len(corners)} rows) -> {corners_out}")


def cmd_scenario_doe(args) -> None:
    cfg = load_config(args.config)
    factors, points = designs.crossed_design()
    df = run_design(cfg, factors, points, n_reps=args.reps)
    _ensure_dirs()
    out = EXPERIMENTS / "scenario_doe_replications.csv"
    df.to_csv(out, index=False)
    print(
        f"Scenario DOE: {len(points)} points "
        f"(8 controllable x {len(designs.scenario_grid())} scenarios) "
        f"x {args.reps} reps -> {out}"
    )


# Named improvement alternatives for Phase 6 (baseline vs targeted changes).
IMPROVEMENTS = {
    "baseline": {},
    "wider_radius": {"geography.service_radius_km": 2.0},
    "peak_staffing": {"picking.n_pickers": 4, "courier.n_couriers": 12},
    "faster_picking": {"picking.per_item_min": 0.25},  # better layout/slotting
    "dispatch_at_ready": {"courier.dispatch_policy": "assign_at_ready"},
}


def cmd_improve(args) -> None:
    cfg = load_config(args.config)
    _ensure_dirs()
    frames = []
    for name, ov in IMPROVEMENTS.items():
        cfg_v = apply_overrides(cfg, ov) if ov else cfg
        df = run_scenario(cfg_v, n_reps=args.reps, factor_cols={"alternative": name})
        frames.append(df)
    allm = pd.concat(frames, ignore_index=True)
    out = RESULTS / "improvements_replications.csv"
    allm.to_csv(out, index=False)

    metrics = [
        "service_level",
        "otd_p90_min",
        "courier_utilization",
        "picker_utilization",
        "cost_per_completed_usd",
        "contribution_per_order_usd",
    ]
    summ = summarize(allm, by=["alternative"], metrics=metrics)
    summ_out = RESULTS / "improvements_summary.csv"
    summ.to_csv(summ_out, index=False)
    print(f"Improvements -> {out}")
    show = ["alternative"] + [f"{m}_mean" for m in ["service_level", "otd_p90_min", "cost_per_completed_usd"]]
    print(summ[show].round(3).to_string(index=False))


def cmd_confirm(args) -> None:
    """Confirm promising settings with FRESH random seeds (not the ones used to
    pick them). If an effect only exists on the original seed stream, it isn't
    real. We re-run baseline + the leading alternatives on a new base seed."""
    cfg = load_config(args.config)
    fresh = int(cfg.meta.base_seed) + 999_999  # a seed stream not used elsewhere
    pick = ["baseline", "faster_picking", "peak_staffing"]
    frames = []
    for name in pick:
        cfg_v = apply_overrides(cfg, IMPROVEMENTS[name]) if IMPROVEMENTS[name] else cfg
        df = run_scenario(
            cfg_v, n_reps=args.reps, base_seed=fresh, factor_cols={"alternative": name}
        )
        frames.append(df)
    allm = pd.concat(frames, ignore_index=True)
    _ensure_dirs()
    out = RESULTS / "confirmation_replications.csv"
    allm.to_csv(out, index=False)
    summ = summarize(
        allm, by=["alternative"], metrics=["service_level", "otd_p90_min", "cost_per_completed_usd"]
    )
    summ.to_csv(RESULTS / "confirmation_summary.csv", index=False)
    print(f"Confirmation (fresh seed {fresh}) -> {out}")
    cols = ["alternative", "service_level_mean", "service_level_ci95_halfwidth",
            "otd_p90_min_mean", "cost_per_completed_usd_mean"]
    print(summ[cols].round(3).to_string(index=False))


def cmd_sensitivity(args) -> None:
    """One-factor-at-a-time sensitivity on key ASSUMPTIONS (not controllables),
    to show which input beliefs the conclusion depends on."""
    cfg = load_config(args.config)
    sweeps = {
        "aov_usd": [("economics.aov_usd", v) for v in (18.0, 25.0, 32.0)],
        "demand_multiplier": [("arrivals.demand_multiplier", v) for v in (0.8, 1.0, 1.3)],
        "speed_kmh": [("courier.speed_kmh", v) for v in (10.0, 15.0, 20.0)],
        "mean_items": [("basket.mean_items", v) for v in (6.0, 8.0, 10.0)],
    }
    rows = []
    for param, levels in sweeps.items():
        for dotted, val in levels:
            cfg_v = apply_overrides(cfg, {dotted: val})
            df = run_scenario(cfg_v, n_reps=args.reps)
            rows.append(
                {
                    "parameter": param,
                    "level": val,
                    "service_level": df["service_level"].mean(),
                    "otd_p90_min": df["otd_p90_min"].mean(),
                    "cost_per_completed_usd": df["cost_per_completed_usd"].mean(),
                    "contribution_per_order_usd": df["contribution_per_order_usd"].mean(),
                }
            )
    out_df = pd.DataFrame(rows)
    _ensure_dirs()
    out = RESULTS / "sensitivity.csv"
    out_df.to_csv(out, index=False)
    print(f"Sensitivity -> {out}")
    print(out_df.round(3).to_string(index=False))


def cmd_dashboard(args) -> None:
    from .dashboard import build_dashboard

    build_dashboard()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="15-min grocery delivery DES")
    p.add_argument("--config", default=str(ROOT / "config.yaml"))
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("baseline", help="run the baseline configuration")
    b.add_argument("--reps", type=int, default=None)
    b.set_defaults(func=cmd_baseline)

    d = sub.add_parser("doe", help="2^3 controllable factorial (+centre)")
    d.add_argument("--reps", type=int, default=15)
    d.set_defaults(func=cmd_doe)

    s = sub.add_parser("scenario-doe", help="controllable factorial x scenarios")
    s.add_argument("--reps", type=int, default=10)
    s.set_defaults(func=cmd_scenario_doe)

    i = sub.add_parser("improve", help="baseline vs targeted alternatives")
    i.add_argument("--reps", type=int, default=20)
    i.set_defaults(func=cmd_improve)

    cf = sub.add_parser("confirm", help="re-run leading settings on fresh seeds")
    cf.add_argument("--reps", type=int, default=30)
    cf.set_defaults(func=cmd_confirm)

    se = sub.add_parser("sensitivity", help="OFAT sensitivity on key assumptions")
    se.add_argument("--reps", type=int, default=15)
    se.set_defaults(func=cmd_sensitivity)

    dash = sub.add_parser("dashboard", help="build the service-vs-cost dashboard")
    dash.set_defaults(func=cmd_dashboard)

    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
