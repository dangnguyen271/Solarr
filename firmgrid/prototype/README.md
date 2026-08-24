# FirmGrid Prototype

The working MVP for the Asian Hackathon for Green Future 2026 (Track 1).
A digital twin of one Hanoi 400 kVA distribution feeder — driven by **12
months of real Hanoi weather** (Open-Meteo archive, Jul 2025 – Jun 2026,
cached in `data/hanoi_weather.csv`) — plus a congestion/surplus forecasting
layer, a fair headroom auction, mobility demand steering, a hash-chained
settlement ledger, and a Tier-2 "firm block" simulator for data-centre DPPAs.
**The demo is fully offline: the weather cache ships with the repo; re-fetch
with `python fetch_data.py` only if you want fresher data.**

## Run

```bash
python3 -m venv ../.venv                       # once
../.venv/bin/pip install -r requirements.txt   # once
./run.sh                                       # → http://localhost:8501
```

## Verify (do this before any demo)

```bash
../.venv/bin/python selftest.py    # must print: ALL CHECKS PASSED
```

Checks: the twin produces realistic curtailment; GridMind F1 > 0.6 on held-out
days; the demo day breaches at baseline and never with FirmGrid ON; energy is
recovered; the fraud bid is blocked; the ledger chain verifies; the storm
scenario never does worse than baseline.

## What each tab demonstrates (the decisions, not the dashboard)

The first tab is the intelligence layer's own console; the rest are one per stakeholder:

| Tab | Stakeholder & decision |
|---|---|
| 🛰 GridMind Ops | The intelligence layer itself: a live **energy-routing network** (every kW from roof → transformer → stations / homes / upstream grid, per 15-min window), probabilistic surplus forecast with P10–P90 band + overload-risk strip, the window's order book (offer/cleared/fill/status per seller), hash-stamped settlement feed, and scenario controls (window, cloud cover, demand steering). |
| ⚡ Grid operator (EVN) | When and how little to curtail: animated feeder maps (today vs FirmGrid), unmanaged/managed gauges, whole-day chart, storm-front stress test, Sankey, auction log. |
| 🏠 Solar households | Earn passively, fairly: per-family receipt & chart, fairness bound, ledger check, "try to cheat" Sentinel demo. |
| 🔋 Swap stations & fleets | When to charge: schedule slider, savings/CO₂ cards (~1 kg per swap), charging-under-the-sun chart, rider receipt. |
| 🏢 Data centres | Size your DPPA: firm-block sliders, hourly CFE score, blended $/MWh vs grid tariff. |
| 🌏 City & judges | Verify the impact: every assumption on a slider, arithmetic written out. |

## Module map

| File | Role |
|---|---|
| `twin.py` | Synthetic feeder: 30 PV homes, 25 non-PV, 3 C&I rooftops, 2 swap stations, 1 depot; one seeded year @ 15-min. |
| `gridmind.py` | Gradient-boosted congestion classifier (day-split held-out eval) + surplus nowcast. |
| `auction.py` | HeadRoom MILP (PuLP/CBC, greedy fallback): ≤ 90% of forecast headroom, fairness rejection-credits, explainable outcomes. |
| `flexmatch.py` | Steers station/depot charging into the 10:00–14:00 solar window; computes savings + CO₂. |
| `firmblock.py` | Aggregates N feeders + storage into a 24/7 CFE-matched data-centre block. |
| `ledger.py` | TrustLedger (SHA-256 hash chain) + Sentinel (physical-cap bid screening). |
| `market.py` | Runs one day both ways and produces the counterfactual numbers. |
| `app.py` | The Streamlit dashboard. |
