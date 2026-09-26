"""
Weighted Vendor Decision Matrix — Crystallizer-Centrifuge-Dryer Package
=========================================================================

Compares 3 vendor quotes for the crystallizer/centrifuge/dryer package
(the final unit operation in the lithium-refining process modeled in the
companion `lithium-refining-mass-energy-balance` project) across cost,
schedule, technical fit, reference performance, and warranty terms.

This is the kind of tradeoff analysis a Project Engineer runs to support a
sourcing recommendation: no single vendor wins on every criterion, so the
decision comes down to how the weights are set — and whether that decision
is *robust* to reasonable disagreement about those weights.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)

# Weights reflect what matters most for a long-lead, process-critical
# package on a schedule with almost no float (see the companion scheduler
# project: this package sits on the critical path with only a few days of
# buffer), so schedule risk is weighted close to cost.
WEIGHTS = {
    "cost": 0.30,
    "lead_time": 0.25,
    "technical_fit": 0.25,
    "reference_performance": 0.15,
    "warranty_years": 0.05,
}

NEED_BY_LEAD_TIME_WEEKS = 8.0  # the fabrication window the master schedule allows (G3-2 -> G3-5)


def normalize(series: pd.Series, higher_is_better: bool) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([1.0] * len(series), index=series.index)
    norm = (series - lo) / (hi - lo)
    return norm if higher_is_better else 1 - norm


def score_vendors(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    scored = df.copy()
    scored["cost_score"] = normalize(df["capital_cost_usd"], higher_is_better=False)
    scored["lead_time_score"] = normalize(df["lead_time_weeks"], higher_is_better=False)
    scored["technical_fit_norm"] = normalize(df["technical_fit_score"], higher_is_better=True)
    scored["reference_norm"] = normalize(df["reference_performance_score"], higher_is_better=True)
    scored["warranty_norm"] = normalize(df["warranty_years"], higher_is_better=True)

    scored["weighted_total"] = (
        scored["cost_score"] * weights["cost"]
        + scored["lead_time_score"] * weights["lead_time"]
        + scored["technical_fit_norm"] * weights["technical_fit"]
        + scored["reference_norm"] * weights["reference_performance"]
        + scored["warranty_norm"] * weights["warranty_years"]
    )
    scored["schedule_risk_days"] = (NEED_BY_LEAD_TIME_WEEKS - df["lead_time_weeks"]) * 7
    return scored.sort_values("weighted_total", ascending=False)


def weight_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Re-run the ranking under a few alternative weighting philosophies to
    test how robust the recommendation is."""
    scenarios = {
        "Baseline (schedule-aware)": WEIGHTS,
        "Cost-driven": {"cost": 0.50, "lead_time": 0.15, "technical_fit": 0.20,
                        "reference_performance": 0.10, "warranty_years": 0.05},
        "Schedule-driven": {"cost": 0.15, "lead_time": 0.45, "technical_fit": 0.20,
                             "reference_performance": 0.15, "warranty_years": 0.05},
        "Quality-driven": {"cost": 0.15, "lead_time": 0.15, "technical_fit": 0.35,
                            "reference_performance": 0.30, "warranty_years": 0.05},
    }
    rows = []
    for scenario_name, weights in scenarios.items():
        ranked = score_vendors(df, weights)
        winner = ranked.iloc[0]
        rows.append({
            "scenario": scenario_name,
            "top_vendor": winner["vendor"],
            "top_score": round(winner["weighted_total"], 3),
        })
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(os.path.join(DATA, "vendor_quotes_crystallizer.csv"))
    ranked = score_vendors(df, WEIGHTS)

    report_cols = ["vendor", "capital_cost_usd", "lead_time_weeks", "schedule_risk_days",
                   "technical_fit_score", "reference_performance_score", "warranty_years",
                   "weighted_total"]
    ranked[report_cols].to_csv(os.path.join(OUT, "vendor_ranking.csv"), index=False)

    sensitivity = weight_sensitivity(df)
    sensitivity.to_csv(os.path.join(OUT, "weight_sensitivity.csv"), index=False)

    # --- Chart: weighted score breakdown by vendor ---
    fig, ax = plt.subplots(figsize=(8, 5))
    components = ["cost_score", "lead_time_score", "technical_fit_norm", "reference_norm", "warranty_norm"]
    labels = ["Cost", "Lead time", "Technical fit", "References", "Warranty"]
    weight_vals = [WEIGHTS["cost"], WEIGHTS["lead_time"], WEIGHTS["technical_fit"],
                   WEIGHTS["reference_performance"], WEIGHTS["warranty_years"]]

    bottom = pd.Series([0.0] * len(ranked), index=ranked.index)
    colors = ["#0C4DA2", "#3E8E41", "#D9A400", "#B02E0C", "#7A4FA3"]
    for comp, label, w, color in zip(components, labels, weight_vals, colors):
        contrib = ranked[comp] * w
        ax.bar(ranked["vendor"], contrib, bottom=bottom, label=f"{label} ({w:.0%})", color=color)
        bottom += contrib

    ax.set_ylabel("Weighted decision score (0-1)")
    ax.set_title("Vendor Decision Matrix — Crystallizer/Centrifuge/Dryer Package")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
    for i, total in enumerate(ranked["weighted_total"]):
        ax.text(i, total + 0.01, f"{total:.2f}", ha="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "vendor_decision_matrix.png"), dpi=150)

    print("=== Vendor Ranking (baseline weights) ===")
    print(ranked[report_cols].to_string(index=False))
    print()
    print("=== Weight Sensitivity (does the winner change?) ===")
    print(sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
