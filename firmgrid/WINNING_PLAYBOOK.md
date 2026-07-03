# FirmGrid — Winning Playbook
### Asian Hackathon for Green Future 2026 · Track 1 · Preliminary Round

Everything you need to submit, present, and win — in one file.
Generated 04 Jul 2026, ~03:00. **Submission deadline: TODAY 08:00 (GMT+7).**

---

## 0. SUBMIT FIRST — the checklist (do this before anything else)

Send **one email** to **hackathon@foundationforgreenfuture.com** before **08:00, Sat 04 July 2026**. Late = not accepted.

| # | Attachment | File (in `firmgrid/submission/`) | Status |
|---|---|---|---|
| 1 | Proposal (short version) | `[TEAM_NAME]_FirmGrid_PreliminaryRound.pdf` (DOCX also available) | ⚠️ rename `[TEAM_NAME]`, fill member names |
| 2 | Presentation slides | `[TEAM_NAME]_FirmGrid_Slides.pptx` | ⚠️ rename, fill names on slides 1 & 10 |
| 3 | Poster for TV (optional, recommended) | `[TEAM_NAME]_FirmGrid_Poster.pptx` | ⚠️ rename |

**Before hitting send:**
1. Replace every `[TEAM_NAME]` / `[Member N]` placeholder (filenames AND inside the documents — the DOCX is editable in Word; or edit `tools/proposal_content.py` and re-run `tools/build_proposal.py`).
2. File naming convention is mandatory: `[TeamName]_[ProjectName]_PreliminaryRound.pdf`.
3. Open each attachment once to confirm it renders.

---

## 1. Competition analysis — what the judges are actually scoring

**Format:** Preliminary round = 5-min presentation + 5-min Q&A, scored by 2 judges = **85%** of total. Top-30 showcase = 5 min incl. Q&A, 1 judge = **15%**. So the preliminary pitch is nearly everything; the poster/TV matters for the showcase.

**Scorecard and how FirmGrid answers it:**

| Criterion | Weight | Our answer |
|---|---|---|
| Product feasibility & quality | **40%** | A *working, offline* prototype: digital twin + real forecasting (F1 0.80 held-out) + MILP auction + settlement ledger. Judges can operate it. Regulation-native design = feasible in the real world, not just in code. |
| Social & environmental impact | **30%** | Bottom-up arithmetic with visible assumptions: 15–19 GWh/yr and 10–13 kt CO₂/yr at Hanoi scale, +16–27 kt mobility-side, ~1 kg CO₂ per swap; household income 0.6–1.0M ₫/yr; fairness bound = social sustainability. |
| Creativity | **15%** | Curtailment reframed as a *forecast product*; energy–mobility coupling (swap stations as the grid's sponge); two-tier "firmness as software" reaching data centres. |
| Presentation & critical thinking | **15%** | Tight 5-min arc (script in the deck's speaker notes), honest-risk slide, rehearsed rebuttals (Section 4 below). |

**The explicit guardrail (from the challenge statement):** *"Solutions that only monitor or visualize energy data without enabling meaningful decisions, actions, or operational improvements may receive lower scores."* → Never demo FirmGrid as a dashboard. Every screen shows a **decision**: an auction clearing, a schedule steering, a fraud block, a DPPA price. Say the word "decision" out loud, repeatedly.

**Judging panel (from Opening.pdf):** Head: Prof. Duong Nguyen Vu. Panel includes Assoc. Prof. Shauhrat S. Chopra (sustainability/LCA background), Dr. Paul Wang, Assoc. Prof. Carrie Ling, Mr. David Falcon, Dr. Nguyen Duy Dat, Assoc. Prof. Nguyen Trung Thanh. Mixed academic + industry ⇒ expect both "how does the MILP work?" and "who pays you?". Mentors are from VinUniversity/Vingroup ecosystem (incl. Electrical Engineering and AI program leads) — the EVNHANOI shadow-pilot claim via VinUni industry network is credible to this room; VinFast swap stations are a Vingroup asset, so **Sun-to-Wheels lands as home turf**.

**Prototype requirements (verbatim essentials):** working prototype/MVP required; slides-only projects "not eligible for top consideration"; must show defined user, real problem, tech approach, working prototype, pathway to measurable impact. FirmGrid ticks all five — say so explicitly on the demo slide.

---

## 2. What was built and where (regenerate anything in one command)

```
firmgrid/
├── prototype/            # the working MVP — streamlit run app.py (or ./run.sh)
│   ├── twin.py           # digital twin: 400 kVA feeder, 30 PV + 25 homes + 3 C&I,
│   │                     #   2 swap stations + 1 depot, 1 simulated year @ 15-min
│   ├── gridmind.py       # congestion classifier (F1 0.80 held-out) + surplus nowcast
│   ├── auction.py        # HeadRoom MILP (PuLP/CBC), ≤90% headroom, fairness credits
│   ├── flexmatch.py      # steers station charging into the 10:00–14:00 solar window
│   ├── firmblock.py      # Tier-2: 24/7 CFE block for a data centre (54% @ $84/MWh)
│   ├── ledger.py         # SHA-256 hash-chained TrustLedger + Sentinel anti-fraud
│   ├── market.py         # one day, both ways: blunt baseline vs FirmGrid ON
│   ├── app.py            # 4-tab Streamlit demo dashboard
│   └── selftest.py       # invariants + smoke test (run before every demo!)
├── tools/
│   ├── proposal_content.py  # single source of truth for proposal text — edit HERE
│   ├── build_proposal.py    # → submission DOCX + PDF (Chrome renders the PDF)
│   └── build_deck.py        # → slides PPTX + poster PPTX
├── submission/           # the three deliverables
└── WINNING_PLAYBOOK.md   # this file
```

- Environment: `firmgrid/.venv` (Python 3.14). Recreate: `python3 -m venv .venv && .venv/bin/pip install -r prototype/requirements.txt python-pptx python-docx`.
- Verify before demoing: `cd prototype && ../.venv/bin/python selftest.py` → must end `ALL CHECKS PASSED`.
- Run the demo: `cd prototype && ./run.sh` → http://localhost:8501. **Fully offline — venue Wi-Fi cannot hurt you.**
- Key demo numbers (seed 42; they recompute live): demo day 2026-05-20, baseline waste 811 kWh / 19 breaches → FirmGrid 39 kWh / 0 breaches, 95% recovered, 836,928 ₫ paid, fairness max-wait 1 window; GridMind F1 0.80, MAE 2.4 kW; Firm Block 54% CFE @ $84/MWh vs $92 grid.

---

## 3. The 5-minute presentation script

Full per-slide script lives in the **speaker notes of the PPTX**. The skeleton (timings):

1. **Hook (25s)** — the paradox: waste at noon, coal at night. "Everything you'll see runs live on this laptop."
2. **Problem (45s)** — 19 GW curtailed · 450k bikes electrifying · DC demand ×2 · cap 20→50% one week before the hackathon.
3. **Root cause (30s)** — curtailment is blunt because it is blind; it's a software gap.
4. **Solution (45s)** — one engine, two tiers; EVN stays the buyer; no new law. Nuclear = destination, FirmGrid = bridge.
5. **Mechanism (35s)** — sense→bid→clear→settle; 90% safety margin; human override.
6. **DEMO (60s)** — switch to the app: baseline vs ON, then a judge drags the storm / injects fraud.
7. **Impact (40s)** — the arithmetic chain with sliders; Hanoi/national/mobility/Tier-2 numbers.
8. **Moat (35s)** — pre-empt: Powerledger ledger-not-forecast; storage complementary; honest AI.
9. **Roadmap (30s)** — shadow pilot → sandbox → 1,000 transformers → first firm DPPA → ASEAN; de-risked floor.
10. **Close (20s)** — Tay Ho rooftop → Grab driver's evening ride; questions invited, prototype open.

**Demo choreography:** have `run.sh` already running before you're called; Tab 1 pre-loaded (cache warm). Hand the mouse to a judge on Tab 2 — *judges remember what they touched.*

---

## 4. Q&A prep — the hard questions, with rebuttals

1. **"Which decree exactly allows this?"** → Households: Decree 58/2025 (rooftop self-production, surplus sale, EVN sole buyer) — amended June 2026 raising the sellable cap 20%→50%. Stations: Decree 57/2025 (DPPA; charging providers = large consumers). Payments: Decree 52/2024. If pressed on the amendment number: "58/2025, amended effective 26 June 2026 — we'll follow up in writing with the amendment number." Do NOT bluff a number.
2. **"Isn't this the Powerledger/EVN CPC pilot?"** → "That pilot proves households want to trade — but it's a ledger: it records trades after the fact. It has no predictive congestion model, so it can't say whether a trade is *safe* before it happens. GridMind is what's missing, and it's the hard part."
3. **"EVN is building 10–16 GW of storage (PDP8). Why not wait?"** → "Years and billions of dong. FirmGrid runs on meters and rooftops already installed and captures value this year. Complementary: storage does bulk shifting; we do fine-grained allocation — and we make every battery more valuable when it arrives."
4. **"Why not wait for nuclear?"** → "The crunch is 2027–2030; Ninh Thuận 1 is 2030–2035 at the earliest. Waiting means outages and missed green targets now. If nuclear lands on time, we built the flexible grid it plugs into; if it slips, we're why the lights stayed clean. Either way the firm grid must be built." (Keep the claim generic — "firm nuclear baseload targeted 2030–2035"; don't say SMR.)
5. **"Is solar really 'firm' here?"** → Precise language: "Solar becomes a firm *dispatchable block* via storage + hour-matching + market design. It does not become baseload by itself." Never overclaim — this is the easiest takedown and we've designed the answer in.
6. **"Your data is synthetic."** → "Deliberately and declaredly: a physics-grounded twin calibrated to Hanoi climatology and Vietnamese load shapes, with every assumption on a slider — plus measured skill on held-out days and a transfer-learning path: shadow pilot on real telemetry before any money moves. We show F1 0.80 honestly instead of pretending to real data we don't have."
7. **"EVN single-buyer friction will kill you."** → "We sell intelligence, not electricity — EVN keeps operational authority and remains the financial counterparty. Value prop #1 (predictive minimal curtailment) is a pure operations tool EVN can adopt unilaterally, no market reform needed."
8. **"Who pays, concretely?"** → "SaaS to distribution utilities (curtailment ↓, reinforcement deferral), a take-rate on FlexMatch absorption credits, station subscriptions, and in Tier 2 a structuring/M&V fee on firm-block DPPAs. Households never pay — non-negotiable for adoption and equity."
9. **"What if the forecast is wrong?"** → "Three layers: allocate only 90% of forecast headroom; bids capped at physical reality; operator override outranks everything. In the twin, zero breaches across the year with the market on — you can try to break it yourself."
10. **"Fraud / gaming?"** → Live demo: inject a 15 kW bid from a 10 kWp home — Sentinel blocks it pre-auction, the event is hash-chained. Collusion patterns and meter-tamper signatures are Sentinel's roadmap scope.

---

## 5. If you have spare time before 08:00 (priority order)

1. Fill real team name + members; regenerate (`build_proposal.py`, `build_deck.py`) and rename files.
2. Run `selftest.py` once on the presentation laptop; open the app and click all 4 tabs (warms the cache).
3. Rehearse the 5-minute script out loud once against a timer, and rebuttals #1–#3 (most likely gotchas).
4. Optional: 2-minute check of the June-2026 amendment number on baochinhphu.vn to close Q&A risk #1 fully.
5. Optional polish: export the poster slide as PNG from PowerPoint for the TV (16:9 already).
