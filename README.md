# Capital Equipment Procurement Tracker & Vendor Tradeoff Analysis

A procurement tracking tool and weighted vendor decision matrix for the
capital equipment packages in a hypothetical lithium-refining pilot plant
project — the same process and schedule modeled in the two companion
repos, [`lithium-refining-mass-energy-balance`](../lithium-refining-mass-energy-balance)
and [`capital-project-stage-gate-scheduler`](../capital-project-stage-gate-scheduler).

## Why this project

"Conducting cost tradeoffs" and "supporting procurement and tracking of
capital equipment" are named directly in the job description. This project
builds both halves of that: (1) a procurement log that checks every PO's
promised delivery date against the schedule's need-by date and flags risk
automatically, and (2) a weighted decision matrix for choosing between
competing vendor quotes — with a sensitivity test on the weighting itself,
since "which vendor wins" often depends more on how you weight cost vs.
schedule vs. quality than on the raw numbers.

## Part 1 — Procurement tracker across 5 equipment packages

`data/equipment_procurement_log.csv` tracks the 5 long-lead packages for
the plant (acid roasting kiln, leaching/filtration tanks, lime
precipitation reactor, causticization reactor, and the crystallizer/
centrifuge/dryer package) against the need-by date the master schedule
requires (equipment must be on-site by the start of installation, task
`G3-5` in the companion scheduler project).

Running `src/procurement_tracker_dashboard.py` computes each package's
promised delivery date (PO date + vendor lead time) and flags:

| Package | Buffer | Flag |
|---|---|---|
| Acid Roasting Kiln | **-1 day** | **AT RISK** — promised delivery misses the need-by date |
| Causticization Reactor | +4 days | TIGHT (<5 day buffer) |
| Crystallizer-Centrifuge-Dryer Package | +4 days | TIGHT (<5 day buffer) |
| Leaching & Filtration Tanks | +12 days | OK |
| Lime Precipitation Reactor | +12 days | OK |

The kiln package is the one item the tool catches as genuinely late —
exactly the kind of one-day miss that's easy to lose in a spreadsheet but
matters when it's sitting on the schedule's critical path.

## Part 2 — Vendor decision matrix (crystallizer package deep-dive)

`data/vendor_quotes_crystallizer.csv` holds 3 competing quotes for the
crystallizer/centrifuge/dryer package. `src/vendor_decision_matrix.py`
scores each vendor on cost, lead time, technical fit, reference
performance, and warranty, using explicit, adjustable weights:

| Vendor | Cost | Lead time | Technical fit | References | Warranty | **Weighted score** |
|---|---|---|---|---|---|---|
| Nordic Separation Systems | $2.62M | 7 wks | 9.0 | 9.0 | 3 yr | **0.70** |
| Crystal Process Co | $2.45M | 8 wks | 8.5 | 8.0 | 2 yr | 0.62 |
| ThermoCryst Solutions | $2.18M | 12 wks | 7.0 | 6.5 | 1 yr | 0.30 |

**The tradeoff that matters:** ThermoCryst is $270K cheaper than Crystal
Process Co, but its 12-week lead time misses the schedule's 8-week
fabrication window by 4 weeks — a real schedule slip, not a rounding
error. The weight-sensitivity sweep (`outputs/weight_sensitivity.csv`)
tests whether the recommendation survives reasonable disagreement about
priorities:

| Weighting philosophy | Winner |
|---|---|
| Baseline (schedule-aware) | Nordic Separation Systems |
| Schedule-driven | Nordic Separation Systems |
| Quality-driven | Nordic Separation Systems |
| **Cost-driven** | **Crystal Process Co** |

Nordic wins under every weighting except a purely cost-driven one — a
robust recommendation, but the cost-driven flip is exactly the objection
a procurement/finance stakeholder would raise, so the model surfaces it
rather than hiding it.

## Repo structure

```
src/
  vendor_decision_matrix.py         # weighted scoring + weight-sensitivity test
  procurement_tracker_dashboard.py  # PO-date + lead-time vs. need-by-date risk flagging
data/
  equipment_procurement_log.csv     # 5-package procurement log
  vendor_quotes_crystallizer.csv    # 3 competing vendor quotes for the deep-dive
outputs/
  procurement_schedule_risk_report.csv / .png
  vendor_ranking.csv
  weight_sensitivity.csv
  vendor_decision_matrix.png
```

## Running it

```bash
pip install -r requirements.txt
python src/procurement_tracker_dashboard.py   # writes procurement_schedule_risk_report.csv/.png
python src/vendor_decision_matrix.py          # writes vendor_ranking.csv, weight_sensitivity.csv, vendor_decision_matrix.png
```

## Skills demonstrated (mapped to the job description)

- **Equipment Procurement** — tracking capital equipment packages against
  a schedule, with automatic risk flagging rather than manual date-checking.
- **Cost Tradeoffs** — an explicit, adjustable weighted decision model
  instead of a gut-feel vendor pick, plus a sensitivity test on the
  weighting assumptions themselves.
- **Vendor Relationships** — the underlying data model (cost, lead time,
  technical fit, references, warranty) mirrors what actually goes into an
  equipment sourcing recommendation memo.

## Disclaimer

Built as a self-directed portfolio project to demonstrate procurement and
cost-tradeoff analysis fundamentals. Vendor names, quotes, and dates are
illustrative and not based on any specific company's procurement data.
