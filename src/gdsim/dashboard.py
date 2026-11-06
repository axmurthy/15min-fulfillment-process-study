"""A simple static dashboard: service vs cost trade-offs.

Deliberately minimal (matplotlib PNG, no web app). It reads the CSVs produced by
the `improve` and `doe` commands and renders three panels:
  1. Service level vs cost per completed order, per improvement alternative.
  2. The same trade-off across the factorial design points (coloured by couriers).
  3. P90 delivery time vs courier utilisation (speed vs labour-use tension).

Run the analyses first:
    python -m gdsim.cli improve
    python -m gdsim.cli doe
    python -m gdsim.cli dashboard
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
EXPERIMENTS = ROOT / "experiments"
OUT_DIR = ROOT / "dashboard"


def build_dashboard() -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        "15-min grocery delivery -- service vs cost trade-offs (simulation study)",
        fontsize=13,
    )

    # Panel 1: improvement alternatives
    ax = axes[0]
    imp_path = RESULTS / "improvements_summary.csv"
    if imp_path.exists():
        imp = pd.read_csv(imp_path)
        ax.errorbar(
            imp["cost_per_completed_usd_mean"],
            imp["service_level_mean"],
            xerr=imp["cost_per_completed_usd_ci95_halfwidth"],
            yerr=imp["service_level_ci95_halfwidth"],
            fmt="o",
            capsize=3,
        )
        for _, r in imp.iterrows():
            ax.annotate(
                r["alternative"],
                (r["cost_per_completed_usd_mean"], r["service_level_mean"]),
                textcoords="offset points",
                xytext=(6, 4),
                fontsize=8,
            )
        ax.set_xlabel("operating cost per completed order (USD)")
        ax.set_ylabel("service level (on-time / accepted)")
        ax.set_title("Alternatives (95% CI bars = simulation uncertainty)")
    else:
        ax.text(0.5, 0.5, "run: gdsim.cli improve", ha="center")

    # Panel 2: factorial design trade-off
    ax = axes[1]
    doe_path = EXPERIMENTS / "factorial_doe_summary.csv"
    if doe_path.exists():
        doe = pd.read_csv(doe_path)
        sc = ax.scatter(
            doe["cost_per_completed_usd_mean"],
            doe["service_level_mean"],
            c=doe["couriers"],
            s=60,
            cmap="viridis",
        )
        ax.set_xlabel("operating cost per completed order (USD)")
        ax.set_ylabel("service level")
        ax.set_title("Factorial design points")
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label("couriers")
    else:
        ax.text(0.5, 0.5, "run: gdsim.cli doe", ha="center")

    # Panel 3: speed vs labour utilisation
    ax = axes[2]
    if doe_path.exists():
        doe = pd.read_csv(doe_path)
        sc = ax.scatter(
            doe["courier_utilization_mean"],
            doe["otd_p90_min_mean"],
            c=doe["radius_km"],
            s=60,
            cmap="plasma",
        )
        ax.axhline(15.0, color="red", ls="--", lw=1, label="15-min target")
        ax.set_xlabel("courier utilisation")
        ax.set_ylabel("P90 delivery time (min)")
        ax.set_title("Speed vs labour utilisation")
        ax.legend(fontsize=8)
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label("radius (km)")
    else:
        ax.text(0.5, 0.5, "run: gdsim.cli doe", ha="center")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = OUT_DIR / "service_vs_cost_dashboard.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Dashboard written -> {out}")
    return out
