# FirmGrid Prototype

The working MVP for the Asian Hackathon for Green Future 2026 (Track 1).
A digital twin of one Hanoi 400 kVA distribution feeder, a congestion/surplus
forecasting layer, a fair headroom auction, mobility demand steering, a
hash-chained settlement ledger — and a Tier-2 "firm block" simulator for
data-centre DPPAs. **Fully offline: no network calls, no API keys.**

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

| Tab | Decision demonstrated |
|---|---|
| ① Baseline vs FirmGrid ON | Blunt feeder-wide curtailment vs auctioned minimal curtailment — same day, live counters (kWh, CO₂, ₫, breaches). |
| ② Judge-in-the-loop | Storm-front slider re-clears forecasts + auction; injected 15 kW fraud bid blocked by Sentinel pre-auction. |
| ③ Firm Block Studio | Tier 2: shape a 24/7 hour-matched clean block for a 20 MW data centre; CFE score + blended $/MWh vs grid tariff. |
| ④ Impact & assumptions | The full impact arithmetic with every parameter on a slider. |

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
