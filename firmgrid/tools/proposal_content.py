"""Single source of truth for the FirmGrid proposal text.

Rendered twice: python-docx (editable DOCX) and HTML (Chrome -> PDF).
Structure: list of (kind, payload) blocks per section.
kinds: h1, h2, p, bullets, table (rows = list of lists, first row = header).
"""

TEAM_NAME = "[TEAM_NAME]"
PROJECT = "FirmGrid"
TITLE = (
    "FirmGrid — Sun-to-Wheels & Sun-to-Servers: the intelligence layer that turns "
    "Vietnam's wasted rooftop solar into firm clean power"
)

MEMBERS = [
    ("1", "[Member 1 — full name]", "[Team lead / ML & optimisation]"),
    ("2", "[Member 2 — full name]", "[Power systems & digital twin]"),
    ("3", "[Member 3 — full name]", "[Backend & settlement engineering]"),
    ("4", "[Member 4 — full name]", "[Product, UX & policy research]"),
]

SECTIONS = [
    # ------------------------------------------------------------------ #
    ("1. PROJECT OVERVIEW", [
        ("p", f"1.1 Project Title — {TITLE}"),
        ("p", "1.2 Key challenge area — ☒ Renewable Energy and Low-Carbon Mobility   "
              "☐ Urban Air Quality and Climate Resilience   ☐ Water Resources and "
              "Climate-Resilient Agriculture"),
        ("p", "1.3 Solution category — ☒ Software/Platform   ☐ Mobile App/Web App   "
              "☐ Hardware/IoT   ☐ Integrated Solution"),
        ("p", "1.4 Project Summary — Vietnam curtails rooftop solar at noon and burns coal "
              "after sunset, just as two demand waves arrive: electric two-wheelers pushed by "
              "Hanoi's Low-Emission Zone (from 1 July 2026) and data centres mandated to be "
              "≥50% green by 2030. FirmGrid is an AI-orchestrated flexibility platform that "
              "makes the existing single-buyer grid intelligent instead of fighting it: "
              "GridMind forecasts, per neighbourhood transformer and 15-minute window, how much "
              "rooftop export is physically safe; a fair, explainable auction allocates that "
              "headroom among households; FlexMatch steers battery-swap and depot charging into "
              "the solar window (Tier 1 — Sun-to-Wheels). The same engine then aggregates "
              "orchestrated feeders and storage into firm, hour-matched 24/7 clean blocks sold "
              "to data centres via DPPA (Tier 2 — Sun-to-Servers). Beneficiaries: prosumer "
              "households, EV riders and swap operators, EVN distribution utilities, and "
              "Vietnam's digital economy."),
    ]),
    # ------------------------------------------------------------------ #
    ("2. CONTEXT AND PROBLEM STATEMENT", [
        ("p", "Vietnam built one of Asia's fastest solar booms (~18.8 GW by end-2024; PDP8 "
              "targets 46–73 GW by 2030), but generation peaks 10:00–14:00 while demand peaks "
              "18:00–22:00, when coal — still over half of generation — carries the load. The "
              "binding constraint is local: 250–630 kVA neighbourhood transformers were sized "
              "for one-way flow, so on sunny late mornings EVN curtails rooftop output "
              "feeder-wide to protect equipment — blunt cuts, because operators cannot see "
              "which household could keep exporting safely. Reporting through April 2026 "
              "confirms these curtailments remain routine."),
        ("p", "2026 adds a collision. Hanoi's LEZ starts on 1 July 2026 and the city plans to "
              "replace ~450,000 petrol motorbikes; VinFast alone operates ~4,500 battery-swap "
              "stations (target 45,000), with Selex and Honda scaling alongside — yet nothing "
              "coordinates when this flexible load charges, so by default it charges in the "
              "coal-heavy evening (~100 GWh/yr of new demand in Hanoi alone). Data-centre "
              "demand nearly doubles from ~735 MW (2025) to 1,330–1,543 MW by 2030 under the "
              "data-localisation law, with ≥50% mandated green. And on 26 June 2026 the rooftop "
              "surplus-sale ceiling was raised from 20% to 50% — more exportable energy pressing "
              "on the same constrained transformers, with no fair way to allocate it. Two "
              "visible failures — morning waste, evening dirt — share one root cause: no "
              "intelligence layer connects distributed solar, local grid state, and flexible "
              "demand."),
    ]),
    # ------------------------------------------------------------------ #
    ("3. EXISTING SOLUTIONS AND GAP ANALYSIS", [
        ("bullets", [
            "EVN status quo (Decree 58/2025 buyback + manual curtailment): trusted, universal — "
            "but reactive, feeder-wide, with no per-household granularity and no demand steering.",
            "Home batteries / residential VPPs (sonnen, Tesla): proven aggregation — but tens of "
            "millions of VND per home and no Vietnamese VPP regulatory category.",
            "Blockchain P2P trading (Powerledger — incl. the EVN CPC pilot; LO3): proved consumer "
            "appetite and transparent records — but it is a ledger: it records trades after the "
            "fact, has no predictive congestion model, and token settlement conflicts with "
            "Vietnamese payment law.",
            "SOLshare (Bangladesh): world-first P2P swarm grids and our benchmark for inclusive "
            "UX — but architected for off-grid DC nanogrids, not grid-tied urban feeders under a "
            "single buyer.",
            "DSO flexibility markets (Piclo Flex, GOPACS): the right congestion physics — but "
            "built for liberalised markets and professional aggregators, with no household UX.",
            "Uncoordinated smart charging (static time-of-use): no link to local surplus or "
            "transformer state.",
        ]),
        ("p", "The unresolved gap: no existing solution simultaneously (a) predicts "
              "distribution-level congestion before it happens, (b) allocates scarce export "
              "headroom fairly among ordinary households, (c) recruits mobility batteries as "
              "absorptive demand at solar noon, and (d) deploys inside Vietnam's single-buyer "
              "regulation without waiting for a new law. FirmGrid closes all four at once."),
    ]),
    # ------------------------------------------------------------------ #
    ("4. PROPOSED SOLUTION AND CORE FEATURES", [
        ("p", "FirmGrid replaces blunt curtailment with a predicted, market-cleared, minimal "
              "allocation — and gives the surplus somewhere useful to go. Five features, all "
              "demonstrated live in the working prototype: a digital twin of a real-topology "
              "400 kVA Hanoi feeder (30 PV homes, 25 non-PV homes, 3 C&I rooftops, 2 swap "
              "stations, 1 e-taxi depot) driven by 12 months of REAL Hanoi weather "
              "(Open-Meteo archive, Jul 2025 – Jun 2026) at 15-minute resolution, with an "
              "animated neighbourhood map showing every participant's market status live:"),
        ("bullets", [
            "F1 — GridMind Forecast: transformer breach probability and household surplus "
            "nowcast (gradient boosting; F1 = 0.86 on held-out days, feeder surplus "
            "MAE ≈ 2.0 kW on real weather — metrics shown on screen, honestly).",
            "F2 — HeadRoom Auction: a MILP clears every 15-minute window; accepted export never "
            "exceeds 90% of forecast headroom; rejection credits guarantee bounded maximum wait "
            "(measured max on the demo day: 1 window); every outcome explained in one sentence.",
            "F3 — Sun-to-Wheels FlexMatch: swap stations and depots are paid to pull charging "
            "into the 10:00–14:00 window — on the demo day (a real May 2026 sunny day) this "
            "shifts ~300 kWh into the sun and recovers 97% of otherwise-curtailed energy "
            "(703 → 20 kWh wasted; 17 → 0 limit breaches).",
            "F4 — One-Switch Prosumer App (roadmap: Zalo Mini App): default Auto-Sell, VND-first "
            "(“Hôm nay bạn kiếm được 12.400đ”), full bid→meter→payment transparency.",
            "F5 — TrustLedger + Sentinel: SHA-256 hash-chained audit of every event; bids are "
            "hard-capped at physically possible surplus, so an inflated 15 kW bid is blocked "
            "before money moves. No cryptocurrency — audit infrastructure, not tokens.",
        ]),
        ("p", "Tier 2 — Firm Block Studio: the same engine aggregates ~800 orchestrated "
              "transformers + 160 MWh storage into a 24/7 hour-matched block for a 20 MW data "
              "centre: 54% hourly CFE at a blended ~$85/MWh versus a ~$92/MWh grid tariff — the "
              "negotiation numbers of Vietnam's first firm-solar DPPA, computed live."),
    ]),
    # ------------------------------------------------------------------ #
    ("5. INNOVATION & COMPETITIVE ADVANTAGE", [
        ("bullets", [
            "Predict-then-allocate curtailment: “headroom” becomes a forecast product, "
            "market-cleared 15–60 minutes ahead — to our knowledge no deployed system offers "
            "household-granular, fairness-constrained allocation in a single-buyer market.",
            "Energy–mobility coupling at the feeder: swap networks become schedulable sinks for "
            "rooftop surplus — two national problems become each other's solution, in the launch "
            "city where both go live this quarter.",
            "Regulation-native design: households sell under Decree 58/2025 (cap 20%→50%, "
            "June 2026) with EVN as sole buyer; charging operators join as DPPA large consumers "
            "(Decree 57/2025); settlement is VND-only (Decree 52/2024). Ships without new law.",
            "Two-tier compounding: Tier 1's data flywheel (every onboarded feeder improves the "
            "forecasts) becomes Tier 2's product — firm 24/7 blocks for data centres — bridging "
            "Vietnam to its 2030–2035 nuclear baseload either way: if nuclear lands, FirmGrid "
            "prepared the flexible grid it plugs into; if it slips, FirmGrid is why the digital "
            "economy stayed clean.",
        ]),
        ("p", "Feasibility & development plan — Built during the hackathon: digital twin, "
              "GridMind, auction, FlexMatch, TrustLedger/Sentinel and Firm Block Studio, in a "
              "fully offline prototype with judge-in-the-loop controls (storm-front slider, "
              "fraud injection). Post-hackathon: Q3 2026 shadow pilot on one EVNHANOI feeder; "
              "Q4 2026 hardware-in-the-loop with ~20 volunteer homes via inverter-cloud APIs; "
              "H1 2027 regulatory-sandbox pilot with real money (200 households, 10 stations, "
              "EVN as counterparty); H2 2027 city scale (1,000 constrained transformers) plus "
              "the first firm-block DPPA pilot with a data centre; 2028 second city; 2029+ ASEAN "
              "(Thailand, Indonesia, the Philippines sit 3–5 years behind on the same curve). "
              "Risk honesty: if sandbox regulation lags, predictive minimal curtailment is a "
              "pure operations tool EVN can adopt unilaterally; market layers activate as "
              "regulation permits."),
    ]),
    # ------------------------------------------------------------------ #
    ("6. TARGET GROUPS & POTENTIAL IMPACT", [
        ("p", "Users: prosumer households (<100 kW rooftop, Decree 58/2025); swap-station and "
              "charging operators (VinFast / Selex / Honda ecosystems, e-taxi depots); EVN "
              "distribution companies (EVNHANOI first); EV riders (indirect); data centres and "
              "C&I rooftops via DPPA in Tier 2."),
        ("bullets", [
            "Environmental: one constrained 400 kVA transformer strands ~24 MWh/yr; FirmGrid "
            "recovers 60–80% → 15–19 MWh. A 1,000-transformer Hanoi rollout recovers "
            "15–19 GWh/yr ≈ 10,000–13,000 t CO₂ (official 2024 grid factor 0.681 tCO₂/MWh); a "
            "20,000-transformer national scenario ≈ 200,000–260,000 t CO₂/yr. Steering 20–30% "
            "of the LEZ's ~100 GWh/yr charging wave into the solar window avoids a further "
            "16,000–27,000 t CO₂/yr — about 1 kg CO₂ per swap, printed on the rider's receipt.",
            "Economic: households earn 0.6–1.0 million VND/yr per 5 kWp from energy that is "
            "thrown away today; stations save ~27–44 million VND/yr each by charging in the "
            "solar window; EVN defers transformer reinforcement measured in hundreds of "
            "millions of VND per site.",
            "Social: fairness bound guarantees small households their turn; every dong "
            "traceable from meter to payout; SDG 7, 9, 11, 13.",
        ]),
        ("p", "Committed KPIs: curtailed-kWh avoided; % of swap energy in the solar window; "
              "median household payout; transformer peak-loading delta; fairness index; fraud "
              "precision/recall; settlement latency; Tier-2 hourly CFE score."),
    ]),
    # ------------------------------------------------------------------ #
    ("7. DESCRIPTION OF TECHNOLOGIES APPLIED", [
        ("p", "A. Proposed technologies — Prototype (working today): Python, pandas/NumPy, "
              "scikit-learn gradient boosting, PuLP/CBC MILP auction, SHA-256 hash-chained "
              "ledger, Streamlit + Plotly dashboard; fully offline on one laptop. Scale-up "
              "roadmap: XGBoost/LSTM forecasting, OR-Tools, FastAPI, TimescaleDB, Redis "
              "Streams, MQTT, Zalo Mini App + React Native, Next.js + Mapbox operator console, "
              "optional permissioned Hyperledger Fabric, VNPay/MoMo sandbox payouts."),
        ("p", "B. System architecture — a modular monolith in four planes (Data → Intelligence "
              "→ Market → Experience) over event streams, splitting into services only under "
              "load. One 15-minute cycle: telemetry lands → GridMind publishes headroom h(t) and "
              "surplus ŝᵢ(t) → Auto-Sell agents and stations bid → MILP clears (Σ accepted ≤ "
              "0.9·h(t), fairness bounds) → dispatch set-points → meter reconciliation → Sentinel "
              "anomaly screen → VND settlement → Merkle root sealed. Human operator override "
              "outranks every automated decision."),
        ("p", "C. Data & infrastructure — Prototype: irradiance, temperature and cloud cover "
              "are REAL Hanoi data (Open-Meteo historical archive, hourly, Jul 2025 – Jun 2026, "
              "cached locally so the demo runs offline); household loads follow Vietnamese "
              "load-research shapes with air-conditioning driven by the real temperature; every "
              "assumption adjustable by judges. Pilot: EVN smart meters where deployed, "
              "inverter-cloud APIs elsewhere; partner station logs under MoU; personal data "
              "minimised, processed in-country. Infrastructure: demo = one laptop; cloud "
              "mirror ≈ US$40/month; pilot ≈ US$300–500/month."),
    ]),
    # ------------------------------------------------------------------ #
    ("8. REFERENCES", [
        ("bullets", [
            "Decree 58/2025/NĐ-CP (renewable energy development; rooftop surplus sale), as "
            "amended by Decree 243/2026/NĐ-CP effective 26 June 2026 (surplus-sale cap "
            "20% → 50%); EVN Decision 429/QĐ-EVN (2025). Amendment independently confirmed "
            "by: LNT Partners, “DPPA and Power Self-Production & Consumption Amendments — "
            "What's Changed” (2026); Việt Nam News, “Government raises rooftop solar excess "
            "electricity sales cap to 50 per cent”; Argus Media, “Vietnam raises grid export "
            "cap of rooftop solar to 50pc”; Nation Thailand, “Vietnam raises rooftop solar "
            "grid sales ceiling to 50 per cent”; pv magazine, “Vietnam proposes increase to "
            "surplus power sale from rooftop solar” (Jan 2026, draft stage).",
            "Decree 57/2025/NĐ-CP on the DPPA mechanism (EV charging providers as large "
            "consumers); Decree 52/2024/NĐ-CP on non-cash payment.",
            "Decision 768/QĐ-TTg (April 2025), revised PDP8: solar 46–73 GW and 10–16 GW "
            "battery storage by 2030.",
            "SolarQuarter, “Vietnam Faces Rooftop Solar Curtailment Amid Grid Constraints” "
            "(13 Apr 2026); Norton Rose Fulbright, Vietnam Power Sector Snapshot (2025).",
            "Directive 20/CT-TTg (2025) and Hanoi People's Council LEZ resolution (Nov 2025); "
            "F&L Asia, “Hanoi to subsidise 450,000 motorbike switch” (2025).",
            "Vietnam.vn (Jan 2026): VinFast ≈4,500 swap stations, 45,000 target; Honda swap "
            "rollout from Apr 2026; Selex Motors shared-network materials.",
            "Ministry of Agriculture and Environment: official 2024 grid emission factor "
            "0.681 tCO₂/MWh.",
            "IRENA (2025): firm solar+storage at USD 54–82/MWh in prime regions.",
            "Data-centre market: ~735 MW (2025) → 1,330–1,543 MW (2030) demand forecasts "
            "(Mordor Intelligence & industry reporting); Decision 2161 and the Jan-2026 "
            "data-localisation law.",
            "UNFCCC on SOLshare; Powerledger project materials (incl. EVN CPC pilot); Thurner "
            "et al., pandapower, IEEE TPS (2018); Chen & Guestrin, XGBoost, KDD (2016).",
        ]),
    ]),
]
