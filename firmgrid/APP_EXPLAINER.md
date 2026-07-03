# FirmGrid — What the App and Demo Actually Do
*A plain-language reference. Read this in 10 minutes and you can explain every pixel on screen.*

---

## 1. The one-paragraph version

FirmGrid is a simulation-backed prototype of an **energy market that doesn't exist yet in Vietnam — but legally could tomorrow**. Today, when too many rooftops export solar at once, EVN cuts the *whole neighbourhood's* export to protect the local transformer (blunt curtailment), and clean energy is thrown away. The app shows a full year of a realistic Hanoi neighbourhood, then replays it with FirmGrid's intelligence layer switched on: it **predicts** how much export is safe, **auctions** that safe capacity fairly among households every 15 minutes, **steers** electric-motorbike swap stations to charge at solar noon instead of the coal evening, and **settles** payments in VND with a tamper-evident audit trail. The demo's job is to prove one sentence: *the difference between wasted solar and firm clean power is software, not hardware.*

---

## 2. The world being simulated (the "digital twin")

Everything runs on a synthetic but physics-grounded model of **one neighbourhood distribution transformer** — the real bottleneck in Vietnam's solar problem:

| Element | What it is | Why it's in the model |
|---|---|---|
| **400 kVA transformer** | The box on a pole serving one neighbourhood | This is where curtailment decisions actually happen — not at power plants |
| **Reverse-flow limit (120 kW)** | Max power that can safely flow *backwards* (from rooftops to grid). Set at 30% of nameplate because voltage rise, not heat, binds first on long feeders | When rooftop exports exceed this, EVN must curtail. This limit is the scarce resource the whole market allocates |
| **30 PV homes (4–10 kWp)** | Households with rooftop solar | The sellers. Their midday surplus is what gets wasted today |
| **25 non-PV homes** | Ordinary consumers | Their consumption absorbs exports locally — they create "headroom" |
| **3 C&I rooftops (15–30 kWp)** | Shop/school/mini-factory solar | Bigger exporters that stress the transformer — realistic for Hanoi |
| **2 swap stations + 1 e-taxi depot** | Battery-swap stations (VinFast/Selex-style) and a fleet depot | The flexible demand. Today they charge in the evening (on coal); they are physically capable of charging at noon (on surplus) |
| **One simulated year, 15-min steps** | Hanoi-like weather: monsoon clouds, hazy winters, sunny spells | Enough data to *train and honestly test* the forecasting models, and to find the days where curtailment really bites |

Everything is seeded (reproducible) and offline — no internet, no APIs, no hidden data.

**Key vocabulary used everywhere:**
- **Surplus** — solar a home generates *beyond its own consumption*; the only thing that can be exported.
- **Headroom** — how much total export the feeder can absorb right now without breaching the limit = limit + local consumption + station charging. More local demand at noon ⇒ more headroom ⇒ less curtailment.
- **Breach** — a 15-minute window where reverse flow exceeds the safe limit. Baseline reality: EVN prevents breaches by cutting *everyone*.

---

## 3. The four header metrics (top of the app)

| Metric | Meaning | Why judges should care |
|---|---|---|
| **GridMind congestion F1 = 0.80** | Accuracy (F1 score) of predicting "will the transformer breach within the next hour?", measured on **held-out days the model never saw** | Proves the AI is real and honestly evaluated — not a demo trick |
| **Surplus forecast MAE ≈ 2.4 kW** | Average error of the next-window feeder surplus forecast | Small vs ~150 kW midday surplus ⇒ forecasts are good enough to plan on |
| **Held-out test days** | Size of the honest test set (~91 days) | Shows train/test discipline (split by whole days, no leakage) |
| **Reverse-flow limit 120 kW** | The physical constraint everything respects | The hard safety line every decision is checked against |

---

## 4. Tab ① — "Baseline vs FirmGrid ON" (the core proof)

**What it does:** picks the worst curtailment day of the simulated year (2026-05-20 — sunny, low demand) and runs it **twice**: once as today's reality, once with FirmGrid operating. Same weather, same homes, same physics.

**The five counters:**
| Counter | Meaning |
|---|---|
| **Clean energy wasted (baseline): 811 kWh** | What blunt curtailment throws away on this one day, one transformer: the transformer nears its limit 19 times, and each time *all* export is cut |
| **Wasted with FirmGrid ON: 39 kWh (−771 recovered)** | With prediction + auction, only the marginal kilowatt-hours that physically cannot be absorbed are declined — 95% of the waste is recovered |
| **CO₂ avoided: ~896 kg** | Recovered solar displaces evening fossil generation (0.85 kg/kWh marginal factor) + stations charging on sun instead of coal |
| **Paid to households: ~837,000 ₫** | Real money at the Decree-58 buyback price (700 ₫/kWh) for energy that today earns nothing |
| **Limit breaches: 19 → 0** | FirmGrid never violates the safety limit — it's *more* protective than the status quo, while wasting far less |

**The reverse-flow chart:** red line = baseline reverse flow slamming into the amber dashed safety limit; green line = FirmGrid keeping the feeder just under it all day. This is the whole product in one picture.

**The Sun-to-Wheels chart:** shows station charging (dotted red = today's uncoordinated evening charging) being moved under the yellow surplus curve (blue = FlexMatch schedule). The "sponge" absorbing the solar peak.

**The auction log:** a sample of real market clearings — number of bids, kW accepted, headroom available, plus a one-sentence explanation ("Accepted in full — headroom sufficient" / "Declined — priority credit granted"). Point: **every automated decision is explainable to a grandmother in one sentence.**

**The three footer facts:** kWh of station charging shifted + station savings in ₫; the **fairness bound** (longest any household waited = 1 window); the **TrustLedger** validity check (every event hash-chained, chain verifies = True).

---

## 5. Tab ② — "Judge-in-the-loop" (trust through touch)

**What it does:** lets a judge attack the system live. Three controls:

| Control | What it simulates | What you see happen |
|---|---|---|
| **☁️ Storm front slider (0–90%)** | A weather front wiping out that % of solar | Forecasts and every 15-min auction **re-clear in seconds**. Less surplus ⇒ less market activity ⇒ still zero breaches. Crucially, FirmGrid never does *worse* than baseline — on cloudy days it simply stands down |
| **💀 Fraud toggle** | Household H03 bids 15 kW when its panels can physically produce at most ~8 kW | **Sentinel** blocks the bid *before* the auction runs, shows the reason, and seals the block event into the audit ledger. Fraud is structurally impossible, not just discouraged |
| **FlexMatch shift share (0–100%)** | How much station charging is moved into the solar window | Drag to 0: recovery drops (less absorption headroom). Drag up: recovery rises. Shows demand-steering is a real lever, not decoration |

**The message:** the system is safe under weather shocks, safe under adversarial bids, and its safety posture is explicit — never allocate above 90% of forecast headroom, bids capped at physical reality, human operator override outranks everything.

---

## 6. Tab ③ — "Firm Block Studio" (Tier 2: Sun-to-Servers)

**What it does:** answers "fine, one neighbourhood — but does this scale into a business?" It aggregates many FirmGrid-orchestrated feeders + shared battery storage and shapes them into a **firm, hour-matched 24/7 clean power block** for a data centre — the product a DPPA (direct power purchase agreement) negotiation runs on.

| Slider | Meaning |
|---|---|
| **Orchestrated transformers (800)** | How many neighbourhoods feed recovered surplus into the portfolio |
| **Data-centre load (20 MW)** | The flat, around-the-clock demand to be served |
| **Storage MWh / MW (160 / 40)** | Battery capacity (how much sun can be time-shifted to night) and its charge/discharge speed |
| **Recovery rate (0.7)** | Fraction of curtailed energy FirmGrid actually rescues (from Tier-1 results) |

| KPI | Meaning |
|---|---|
| **Hourly CFE match: 54%** | Carbon-Free Energy score — % of the data centre's load covered by clean energy *in the same hour it's consumed* (the Google/UN 24/7 standard, and what "≥50% green by 2030" audits will demand). Not an annual offset — hour-by-hour truth |
| **Blended cost: $84/MWh vs $92 grid** | Weighted cost of the block (recovered solar $60 + storage cycling $45/MWh throughput + residual grid $92). **The clean block is cheaper than the tariff** — the pitch closes itself |
| **Clean energy delivered: ~94 GWh/yr** | Total hour-matched clean energy into the block |
| **CO₂ avoided: ~19,000 t/yr** | Clean GWh × official 0.681 tCO₂/MWh grid factor |

**The stacked bar chart:** an average day, hour by hour — yellow (direct solar) fills the day, green (solar-charged battery) covers the evening shoulder, grey (residual grid) covers deep night. Judges instantly see both the achievement (54% hour-matched) and the honest limit (solar+storage alone doesn't reach 100% — which is exactly the bridge-to-nuclear talking point).

---

## 7. Tab ④ — "Impact & assumptions" (the arithmetic, naked)

**What it does:** rebuilds our headline impact claims from first principles, with **every input a slider**. Nothing is asserted; everything is computed in front of the judge:

> homes/transformer (30) × system size (5 kWp) × Hanoi yield (1,050 kWh/kWp·yr) × share curtailed (15%) = **~24 MWh/yr stranded per transformer** → × recovery rate (70%) = **~17 MWh recovered** → × Hanoi's constrained transformers (1,000) = **15–19 GWh/yr ≈ 10–13 kt CO₂/yr**

Below it, the two other impact channels are stated with their logic: the **mobility side** (450,000 replaced petrol bikes ≈ 100 GWh/yr of new charging; steering 20–30% into the solar window avoids 16–27 kt CO₂/yr ≈ **1 kg CO₂ per battery swap**) and the **digital side** (data-centre demand doubling to ~1.4 GW by 2030 with a ≥50% green mandate — Tier 2's customer). If a judge doubts any number, you move the slider to *their* number and the conclusion survives.

---

## 8. What each engine module means (the tech behind the tabs)

| Module | Plain meaning | The one thing to remember |
|---|---|---|
| **`twin.py` — Digital Twin** | The simulated neighbourhood and year of weather/load/solar | Stands in for real telemetry, with declared assumptions; the roadmap swaps it for EVN smart-meter data in a shadow pilot |
| **`gridmind.py` — GridMind** | Two ML models (gradient boosting): "will the transformer breach within an hour?" and "how much surplus next window?" | The *predict* in predict-then-allocate. Evaluated on held-out days: F1 0.80 |
| **`auction.py` — HeadRoom Auction** | Every 15 min, a small optimisation (MILP) decides whose export is accepted, maximising renewable use + fairness, never exceeding **90% of forecast headroom** | Curtailment becomes minimal, market-cleared, and explainable — with **fairness credits**: every rejection raises your priority next round, so no household is frozen out by richer neighbours |
| **`flexmatch.py` — FlexMatch** | Schedules swap stations/depots to charge inside 10:00–14:00, paid via absorption credits | Demand steering is the cheapest headroom: the batteries mobility already paid for become the grid's sponge — and evening swaps become verified solar kilometres |
| **`firmblock.py` — Firm Block Studio** | Portfolio simulation: recovered solar + storage vs a 24/7 data-centre load, hour by hour | Tier 1's recovered energy becomes Tier 2's sellable product: an auditable CFE score and a $/MWh price |
| **`ledger.py` — TrustLedger + Sentinel** | Every market event hash-chained (SHA-256, each block includes the previous hash) so history can't be silently edited; Sentinel rejects bids above physical possibility *before* money moves | Trust infrastructure without cryptocurrency — audit, not tokens (deliberate: crypto isn't legal payment in Vietnam) |
| **`market.py` — Day runner** | Replays one day both ways (blunt baseline vs FirmGrid) and produces all counterfactual counters | The "same day, twice" comparison that powers Tab ① |
| **`selftest.py`** | Automated checks: baseline must breach, FirmGrid must not, energy must be recovered, fraud must be caught, ledger must verify | Run before every demo; must print `ALL CHECKS PASSED` |

---

## 9. The demo's argument, in order

1. **Tab ①**: the problem is real and the fix works — 95% of wasted energy recovered, zero safety violations, households paid. *(Feasibility, 40%)*
2. **Tab ②**: it's robust and honest — break it with weather, break it with fraud; it holds. *(Feasibility + critical thinking)*
3. **Tab ③**: it scales into a business serving Vietnam's digital economy. *(Impact + creativity)*
4. **Tab ④**: the impact numbers are arithmetic, not marketing. *(Impact, 30%)*

One sentence to close every demo: **"Nothing you saw was a dashboard — every screen was a decision: an auction cleared, a schedule steered, a fraud blocked, a price quoted."** That sentence is aimed directly at the competition's guardrail against visualization-only tools.
