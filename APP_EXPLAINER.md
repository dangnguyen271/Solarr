# FirmGrid — What the App and Demo Actually Do
*A plain-language reference. Read this in 10 minutes and you can explain every pixel on screen.*

---

## 1. The one-paragraph version

FirmGrid is a simulation-backed prototype of an **energy market that doesn't exist yet in Vietnam — but legally could tomorrow**. Today, when too many rooftops export solar at once, EVN cuts the *whole neighbourhood's* export to protect the local transformer (blunt curtailment), and clean energy is thrown away. The app shows a full year of a realistic Hanoi neighbourhood, then replays it with FirmGrid's intelligence layer switched on: it **predicts** how much export is safe, **auctions** that safe capacity fairly among households every 15 minutes, **steers** electric-motorbike swap stations to charge at solar noon instead of the coal evening, and **settles** payments in VND with a tamper-evident audit trail. The demo is organised as **one tab per stakeholder** — each tab states who it serves and what decision it enables, because that is exactly what the judges score.

---

## 2. The world being simulated (the "digital twin")

Everything runs on a physics-grounded model of **one neighbourhood distribution transformer** — the real bottleneck in Vietnam's solar problem — driven by a year of real Hanoi weather:

| Element | What it is | Why it's in the model |
|---|---|---|
| **400 kVA transformer** | The box on a pole serving one neighbourhood | This is where curtailment decisions actually happen — not at power plants |
| **Reverse-flow limit (120 kW)** | Max power that can safely flow *backwards* (from rooftops to grid). Set at 30% of nameplate because voltage rise, not heat, binds first on long feeders | When rooftop exports exceed this, EVN must curtail. This limit is the scarce resource the whole market allocates |
| **30 PV homes (4–10 kWp)** | Households with rooftop solar | The sellers. Their midday surplus is what gets wasted today |
| **25 non-PV homes** | Ordinary consumers | Their consumption absorbs exports locally — they create "headroom" |
| **3 C&I rooftops (15–30 kWp)** | Shop/school/mini-factory solar | Bigger exporters that stress the transformer — realistic for Hanoi |
| **2 swap stations + 1 e-taxi depot** | Battery-swap stations (VinFast/Selex-style) and a fleet depot | The flexible demand. Today they charge in the evening (on coal); they are physically capable of charging at noon (on surplus) |
| **One year of REAL Hanoi weather, 15-min steps** | Actual irradiance, temperature and cloud cover for Hanoi, July 2025 → June 2026, from the Open-Meteo historical archive (`fetch_data.py` downloaded it once; the demo reads the local cache) | The sunshine driving every panel is what the Hanoi sky actually did in the 12 months ending days before the hackathon — including the real sunny day used in the demo. Air-conditioning load follows the real temperature |

Weather is real; household loads are calibrated Vietnamese profiles (per-home meter data is what the pilot phase obtains). Everything is seeded (reproducible) and offline — the demo never touches the network.

**Key vocabulary used everywhere:**
- **Surplus** — solar a home generates *beyond its own consumption*; the only thing that can be exported.
- **Headroom** — how much total export the feeder can absorb right now without breaching the limit = limit + local consumption + station charging. More local demand at noon ⇒ more headroom ⇒ less curtailment.
- **Breach** — a 15-minute window where reverse flow exceeds the safe limit. Baseline reality: EVN prevents breaches by cutting *everyone*.

---

## 3. The header (top of the app)

Four cards summarise the whole pitch before any tab is opened, all computed live from the demo day (**26 May 2026 — the worst curtailment day of the real-weather year**):

| Card | Meaning |
|---|---|
| **Clean energy rescued today: ~683 kWh (97%)** | Baseline curtailment wastes 703 kWh on this one transformer-day; FirmGrid recovers all but 20 — a day's power for ~100 homes |
| **Paid to solar families today: ~791,000 ₫** | Real money at the Decree-58 buyback price (700 ₫/kWh) for energy that today earns nothing |
| **Grid safety: 17 → 0 breaches** | FirmGrid is *more* protective than the status quo while wasting far less |
| **Forecast skill: F1 = 0.86** | Catches ~6 of every 7 transformer overloads an hour ahead, measured on held-out real-weather days the model never saw |

---

## 4. The five stakeholder tabs

Each tab opens with a banner: **who** the screen is for and **what decision** it enables — the challenge's own scoring language.

### ⚡ Tab 1 — Grid operator (EVN)
*Decision: when and how little to curtail, window by window — instead of cutting the whole feeder.*

- **Time slider + side-by-side neighbourhood maps** — every home 🏠, C&I rooftop 🏭, swap station 🔋, depot 🚕 and the transformer ⚡ as coloured nodes. Left map = today (at noon it floods red: feeder-wide cut, transformer diamond shows the *unmanaged* stress that forces the cut). Right map = FirmGrid (green sellers, stations swollen with midday charging, transformer safely inside the limit). Hover any node for its status in one sentence.
- **Two gauges** — unmanaged reverse flow (the problem) vs managed flow (always under the red line).
- **Whole-day chart** — red baseline reverse flow slamming the limit vs the green FirmGrid line.
- **Storm-front slider** — wipe out up to 90% of the sun: forecasts and all 96 auctions re-clear in seconds, still zero breaches. The operator's what-if tool, and the judges' first break-it lever.
- **Energy Sankey** — where the day's sunshine went: self-consumed / sold / curtailed, and sold energy onward to stations, homes, or the upstream grid.
- **Auction log (expander)** — every clearing explained in one sentence.

### 🏠 Tab 2 — Solar households
*Decision: none needed — switch on Auto-Sell once, earn passively, with a fair queue and a verifiable payment trail.*

- **Neighbourhood cards** — families paid today, total earnings, longest wait for a "yes" (fairness bound: 1 window), ledger-intact check.
- **Pick a family** — select any of the 33 solar roofs: a phone-style receipt ("Hôm nay bạn kiếm được … ₫"), their personal surplus-vs-sold chart, and how many windows they were declined (each one earning a priority credit).
- **"Try to cheat" toggle** — bids 15 kW from a roof that can physically make ~8: **Sentinel blocks it before the auction**, shows why, and seals the event into the hash-chained ledger. Fraud is structurally impossible, not just discouraged.

### 🔋 Tab 3 — Swap stations & fleets
*Decision: when to charge — follow the solar-window schedule, cut the power bill, sell "charged on sunshine" to riders.*

- **Schedule-share slider** — the station's own lever: how much of daily charging follows FirmGrid.
- **Cards** — ~300 kWh/day moved into the sun · ~210,000 ₫/day saved (≈ tens of millions ₫/yr across the three sites) · charging CO₂ avoided · **≈ 1 kg CO₂ per swap**.
- **The Sun-to-Wheels chart** — dotted red (today's evening charging) moving under the yellow sunshine curve (blue FirmGrid schedule).
- **Rider receipt** — "Pin nạp lúc 12:10 — 98% năng lượng mặt trời": evening kilometres, morning sunshine.

### 🏢 Tab 4 — Data centres (Tier 2, Sun-to-Servers)
*Decision: your DPPA — how much firm, hour-matched clean power to contract, and at what price.*

- **Five sliders** — orchestrated transformers, your load, storage MWh/MW, recovery rate.
- **Cards** — **hourly CFE match 54%** (share of load covered by clean energy *in the same hour* — the 24/7 standard the ≥50%-green mandate will be audited against) · **blended price $85/MWh vs $92 grid** · ~94 GWh/yr clean · ~64,000 t CO₂/yr.
- **Stacked hourly chart** — yellow direct solar fills the day, green solar-charged storage covers the evening shoulder, grey residual grid covers deep night: both the achievement and the honest limit (solar+storage alone doesn't reach 100% — the bridge-to-nuclear talking point).

### 🌏 Tab 5 — City & judges
*Decision: whether the numbers hold — change any assumption and watch the impact recompute.*

- **Six assumption sliders** (homes/transformer, kWp, yield, curtailment share, recovery rate, transformer count) → four live cards: stranded and rescued MWh per transformer, the Hanoi rollout in GWh/yr (with its "~N homes' annual power" equivalent), and CO₂ at the official 0.681 t/MWh factor.
- **The chain written out** — the full arithmetic in one paragraph, plus the mobility (16–27 kt CO₂/yr ≈ a million trees) and data-centre context. Nothing asserted; everything recomputable to *the judge's own* numbers.

---

## 5. What each engine module means (the tech behind the tabs)

| Module | Plain meaning | The one thing to remember |
|---|---|---|
| **`twin.py` — Digital Twin** | The simulated neighbourhood, driven by a year of real Hanoi weather | Stands in for real telemetry with declared load assumptions; the roadmap swaps it for EVN smart-meter data in a shadow pilot |
| **`gridmind.py` — GridMind** | Two ML models (gradient boosting): "will the transformer breach within an hour?" and "how much surplus next window?" | The *predict* in predict-then-allocate. Evaluated on held-out real-weather days: F1 0.86 |
| **`auction.py` — HeadRoom Auction** | Every 15 min, a small optimisation (MILP) decides whose export is accepted, maximising renewable use + fairness, never exceeding **90% of forecast headroom** | Curtailment becomes minimal, market-cleared, and explainable — with **fairness credits**: every rejection raises your priority next round |
| **`flexmatch.py` — FlexMatch** | Schedules swap stations/depots to charge inside 10:00–14:00, paid via absorption credits | Demand steering is the cheapest headroom: batteries mobility already paid for become the grid's sponge |
| **`firmblock.py` — Firm Block Studio** | Portfolio simulation: recovered solar + storage vs a 24/7 data-centre load, hour by hour | Tier 1's recovered energy becomes Tier 2's sellable product: an auditable CFE score and a $/MWh price |
| **`ledger.py` — TrustLedger + Sentinel** | Every market event hash-chained (SHA-256) so history can't be silently edited; Sentinel rejects bids above physical possibility *before* money moves | Trust infrastructure without cryptocurrency — audit, not tokens |
| **`market.py` — Day runner** | Replays one day both ways (blunt baseline vs FirmGrid) and produces all counterfactual counters | The "same day, twice" comparison behind every number |
| **`mapview.py` — Visual layer** | The neighbourhood map, gauges and Sankey (bright, clean palette) | Turns market decisions into pictures a non-engineer reads instantly |
| **`selftest.py`** | Automated checks: baseline must breach, FirmGrid must not, energy recovered, fraud caught, ledger verifies | Run before every demo; must print `ALL CHECKS PASSED` |

---

## 6. The demo's argument, in order

1. **Header**: the whole result in four cards before a single click. *(First 10 seconds)*
2. **Grid operator tab**: the problem is real, the fix works, and it survives a storm. *(Feasibility, 40%)*
3. **Households tab**: people get paid, fairly, fraud-proof — social licence. *(Impact + trust)*
4. **Stations tab**: mobility batteries become the grid's sponge — the creative coupling. *(Creativity, 15%)*
5. **Data-centres tab**: it scales into a business serving Vietnam's digital economy. *(Impact + scalability)*
6. **City & judges tab**: the numbers survive the judge's own assumptions. *(Critical thinking)*

One sentence to close every demo: **"Nothing you saw was a dashboard — every screen belongs to a stakeholder and ends in a decision: cleared, steered, blocked, or paid."**
