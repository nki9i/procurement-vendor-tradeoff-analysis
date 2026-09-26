"""
Capital Equipment Procurement Tracker
=======================================

Reads the multi-package procurement log (data/equipment_procurement_log.csv)
and, for each PO, computes the promised delivery date from PO date + vendor
lead time, compares it against the need-by date the master project schedule
requires, and flags schedule risk — the core loop of "tracking of capital
equipment across the project" called out in the job description.
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)


def main():
    df = pd.read_csv(os.path.join(DATA, "equipment_procurement_log.csv"), parse_dates=["po_date", "need_by_date"])

    df["promised_delivery_date"] = df["po_date"] + pd.to_timedelta(df["lead_time_weeks"] * 7, unit="D")
    df["schedule_buffer_days"] = (df["need_by_date"] - df["promised_delivery_date"]).dt.days
    df["risk_flag"] = df["schedule_buffer_days"].apply(
        lambda d: "AT RISK - promised delivery misses need-by date" if d < 0
        else ("TIGHT - <5 day buffer" if d < 5 else "OK")
    )

    report_cols = ["equipment_id", "package", "selected_vendor", "po_date", "lead_time_weeks",
                   "promised_delivery_date", "need_by_date", "schedule_buffer_days", "risk_flag", "status"]
    df[report_cols].to_csv(os.path.join(OUT, "procurement_schedule_risk_report.csv"), index=False)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    colors = {"OK": "#3E8E41", "TIGHT - <5 day buffer": "#D9A400",
              "AT RISK - promised delivery misses need-by date": "#B02E0C"}
    bar_colors = [colors[r] for r in df["risk_flag"]]
    ax.barh(df["package"], df["schedule_buffer_days"], color=bar_colors)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Schedule buffer (days) — negative means promised delivery misses the need-by date")
    ax.set_title("Equipment Procurement Schedule Risk")
    for i, (buf, pkg) in enumerate(zip(df["schedule_buffer_days"], df["package"])):
        ax.text(buf + (1 if buf >= 0 else -1), i, f"{buf:+d}d", va="center",
                ha="left" if buf >= 0 else "right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "procurement_schedule_risk.png"), dpi=150)

    print("=== Procurement Schedule Risk Report ===")
    print(df[report_cols].to_string(index=False))
    at_risk = df[df["schedule_buffer_days"] < 0]
    if len(at_risk):
        print(f"\n{len(at_risk)} package(s) at risk of missing the need-by date:")
        for _, row in at_risk.iterrows():
            print(f"  - {row['package']} ({row['selected_vendor']}): "
                  f"{abs(row['schedule_buffer_days'])} days late vs. need-by {row['need_by_date'].date()}")
    else:
        print("\nAll packages currently forecast to meet their need-by dates.")


if __name__ == "__main__":
    main()
