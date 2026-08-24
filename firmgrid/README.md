# ⚡ FirmGrid

**A grid-aware clean-energy marketplace that turns wasted rooftop solar into firm, 24/7 clean power.**

Asian Hackathon for Green Future 2026 · Track 1 — Renewable Energy & Low-Carbon Mobility
Team **The Broke Three**

---

## The problem

Vietnam has built ~19 GW of rooftop solar, but on sunny mornings neighbourhood transformers
cannot absorb all the export, so the grid operator curtails **entire feeders at once** and clean
energy is thrown away. Hours later the sun sets and the same homes — and the new wave of electric
motorbikes under Hanoi's Low-Emission Zone — draw power from a majority-coal grid. Vietnam wastes
clean power at noon and burns coal at night.

The missing piece is not more hardware — it is an **intelligence layer** that predicts how much
export each transformer can safely accept, allocates that scarce capacity fairly, and steers
flexible demand into the solar window.

## The solution

FirmGrid is that layer. It predicts per-transformer **headroom**, runs a fair **auction** so
households can sell surplus, **steers** battery-swap stations and fleets to charge on midday sun,
and **settles** every trade in VND with a tamper-evident audit trail — all inside Vietnam's current
single-buyer regulation, with no new hardware in the home.

- **Tier 1 — Sun-to-Wheels (today):** a local flexibility market at the neighbourhood transformer.
- **Tier 2 — Sun-to-Servers (next):** the same engine aggregates orchestrated feeders + storage
  into firm, hour-matched 24/7 clean blocks sold to data centres via DPPA.

---

## What's in this repository

Two runnable applications and the supporting materials:

| Component | What it is | Run it |
|---|---|---|
| **`webapp/`** | **Role dashboards** — four polished, interactive stakeholder UIs (household seller · energy buyer · grid/market operator · station console) + a landing page. Static frontend, no build, no backend. | `open webapp/index.html` |
| **`prototype/`** | **Decision engine** — a Streamlit app backed by a physics-based digital twin of a Hanoi feeder driven by **real Hanoi weather**: forecasting, a MILP clearing auction, demand steering, settlement, and impact analysis. | `cd prototype && ./run.sh` |
| **`tools/`** | Scripts that generate the proposal document and the pitch deck from a single source of truth. | `python tools/build_proposal.py` |
| **`documents/`** | Final submission deliverables (proposal PDF/DOCX, slide deck). | — |

The **web app** demonstrates the *experience* for each stakeholder; the **Streamlit engine**
demonstrates the *machinery* (real data, real models). They are complementary.

---

## Quickstart

### 1 · Role dashboards (web app) — zero setup

```bash
# just open the file
open webapp/index.html            # macOS (or double-click it)

# …or serve it with any static server
cd webapp && python3 -m http.server 8600     # → http://localhost:8600
```

Pure HTML/CSS/vanilla JavaScript — no build step, no dependencies, works fully offline.
Navigate roles from the top bar: `#/household`, `#/buyer`, `#/operator`, `#/station`.

### 2 · Decision engine (Streamlit) — Python 3.11+

```bash
cd prototype
python3 -m venv ../.venv
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python selftest.py      # sanity check → prints "ALL CHECKS PASSED"
./run.sh                             # → http://localhost:8501
```

The engine ships with a cached year of real Hanoi weather (`prototype/data/hanoi_weather.csv`);
it runs **fully offline**. To refresh the weather, run `python fetch_data.py`.

---

## How it works

One 15-minute market cycle, end to end:

```
telemetry + weather  →  GridMind (forecast)  →  HeadRoom Auction (allocate)  →  FlexMatch (steer)
                                                        │
                                          Sentinel (anti-fraud) + TrustLedger (settle in VND)
```

| Stage | Module | What it does |
|---|---|---|
| **Forecast** | `gridmind.py` | Gradient-boosted models predict per-transformer overload probability and household surplus. Measured **F1 ≈ 0.86** on held-out days. |
| **Allocate** | `auction.py` | A MILP clears each window, accepting at most **90 % of forecast headroom**, with fairness credits so no household is repeatedly excluded. |
| **Steer** | `flexmatch.py` | Schedules swap-station / depot charging into the 10:00–14:00 solar window — the cheapest form of grid headroom. |
| **Settle** | `ledger.py` | SHA-256 hash-chained audit log; Sentinel blocks bids above a home's physical limit before any payment. VND rails only — no cryptocurrency. |
| **Scale (Tier 2)** | `firmblock.py` | Aggregates orchestrated feeders + storage into an hour-matched 24/7 clean block for a data centre, with a live CFE score and $/MWh price. |
| **Simulate** | `twin.py`, `market.py` | The digital twin (one 400 kVA feeder: 30 solar homes, 25 consumers, 3 C&I rooftops, 2 swap stations, 1 e-taxi depot) and the day-runner that replays it with and without FirmGrid. |

---

## Technology

- **Engine:** Python · pandas / NumPy · scikit-learn (gradient boosting) · PuLP + CBC (MILP) ·
  Streamlit · Plotly. Real weather from the Open-Meteo historical archive.
- **Web app:** HTML · CSS · vanilla JavaScript · inline-SVG charts. No frameworks, no build.
- **Docs/pitch:** python-docx · python-pptx (generated from `tools/`).

Design goal throughout: **regulation-native, capital-light, and demonstrable on one laptop.**

---

## Project structure

```
firmgrid/
├── README.md                 ← you are here
├── webapp/                   ← role dashboards (static frontend)
│   ├── index.html · styles.css · ui.js · mock-data.js · app.js
│   └── README.md
├── prototype/                ← Streamlit decision engine
│   ├── app.py                ← dashboard (GridMind Ops console + 5 stakeholder tabs)
│   ├── opsview.py            ← ops console: energy-routing network, forecast, order book
│   ├── twin.py               ← digital twin (real Hanoi weather)
│   ├── gridmind.py           ← forecasting (congestion + surplus)
│   ├── auction.py            ← fair HeadRoom clearing (MILP)
│   ├── flexmatch.py          ← mobility demand steering
│   ├── firmblock.py          ← Tier-2 firm-block simulator
│   ├── ledger.py             ← settlement audit + anti-fraud
│   ├── market.py             ← one-day runner (baseline vs FirmGrid)
│   ├── mapview.py            ← map / gauge / Sankey visuals
│   ├── selftest.py           ← invariant checks
│   ├── requirements.txt · run.sh · data/hanoi_weather.csv
│   └── README.md
├── tools/                    ← proposal + deck generators
│   ├── proposal_content.py · build_proposal.py · build_deck.py
├── documents/                ← final submission deliverables
└── .gitignore
```

## Data & methodology

- **Weather is real:** 12 months of Hanoi irradiance, temperature and cloud cover from the
  Open-Meteo historical archive (Jul 2025 – Jun 2026), cached locally.
- **Loads are modelled:** calibrated Vietnamese residential/commercial profiles, with
  air-conditioning driven by the real temperature. Per-home smart-meter data is the first
  step of the pilot roadmap.
- **Web-app data is illustrative** mock data for the Hanoi household-solar context (VND prices,
  zones, order book). No personal data is used anywhere.
- Forecast metrics are reported on **held-out days** the models were not trained on.

## Impact (at Hanoi scale)

Recovering curtailed solar across ~1,000 constrained transformers: **15–19 GWh/yr**
(≈ 10,000–13,000 t CO₂/yr), plus **16,000–27,000 t CO₂/yr** from charging electric motorbikes on
midday sun instead of the evening coal margin. All figures are recomputable with adjustable
assumptions in the engine's *City impact* tab.

---

## Deliverables

Final materials for the preliminary round are in [`documents/`](documents/):
the project proposal (PDF + DOCX) and the presentation slides.

## Team

**The Broke Three** — Asian Hackathon for Green Future 2026, Track 1.

## Notes

This is a hackathon prototype. Figures are planning-grade and clearly sourced; the code is
provided to demonstrate feasibility, not as a production system.
