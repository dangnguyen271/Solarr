# FirmGrid — Role Dashboards (frontend prototype)

Four polished, role-based dashboards for the FirmGrid grid-aware clean-energy
marketplace — one per stakeholder — plus a landing page. Built for the
5-minute hackathon pitch: bright, clean, interactive, and **understandable
without narration**.

Pure static frontend: HTML + CSS + vanilla JS with inline-SVG charts. **No
build step, no backend, no network.** Opens by double-clicking `index.html`.

## Run

```bash
# simplest — just open it
open index.html                       # macOS (or double-click the file)

# or serve it (nicer URLs, any static server)
cd firmgrid/webapp && python3 -m http.server 8600   # → http://localhost:8600
```

## Routes

| Route | Stakeholder | What they can demo |
|---|---|---|
| `#/` | Landing | Product overview + four role cards + headline impact numbers |
| `#/household` | **Household solar seller** | See today's solar / consumption / battery / surplus; switch Auto-Sell vs Manual ask; configure kWh, min price, time window, include-battery; live estimated earnings; submit an ask and watch it move through *pending → matched → grid approval → confirmed → delivered*; past sales + monthly earnings |
| `#/buyer` | **Energy buyer** (data centre) | Browse live clean-energy offers (zone, kWh, price, window, CO₂, grid-approval likelihood); Auto-Buy vs Manual bid; local-solar-vs-grid comparison; buy an offer → it lands in matched transactions; CO₂ avoided + money saved |
| `#/operator` | **Grid / market operator** (EVN) | Market metrics; full order book (asks / bids / matched / rejected); per-zone grid constraints with a Zone-B congestion alert; **Clear market** (matches compatible trades, blocks over-limit zones); plain-language explainability for every approve/block |
| `#/station` | **Station console** (transformer node) | Real-time status badges; load / solar inflow / export capacity / utilization; live households→transformer→buyers/battery/local flow diagram; safety gauges; next-4-hour forecast; incoming scheduled exports; routing/dispatch instructions; console event log that streams new lines |

Navigation is the top app-bar role switcher. The **⏸ Pause** control freezes the
live simulation (clock + station telemetry + streaming event log) for a clean
screenshot or a held talking point.

## Files

| File | Role |
|---|---|
| `index.html` | Shell: app bar, role nav, sim controls; loads the scripts |
| `styles.css` | Design system — light theme, green/teal accents, cards, badges, forms, flow diagram, dark console log, per-role accent via `--role` |
| `mock-data.js` | Vietnam household-solar mock data (zones Tây Hồ / Cầu Giấy / Long Biên / Hà Đông, VND prices, order book, station telemetry) + a tiny in-memory `MockAPI` (submit ask, place/accept bid, clear market) + event bus |
| `ui.js` | Shared render helpers + inline-SVG charts (area/line, bars, stacked bars, semicircle gauge, donut) — no chart libraries |
| `app.js` | Hash router, landing + four page renderers, inline action handlers, and the live-simulation loop |

## Units & context

VND/kWh prices (EVN buyback ~700 · local clearing ~2,200 · grid retail ~3,000),
kWh / kW, kg & tonnes CO₂ (0.681 kg/kWh grid factor), Hanoi zones and swap-station
buyers (VinFast / Selex). All data is illustrative mock data for the pitch.

> This is the **front-of-house** demo. The Streamlit app in `../prototype/` is the
> **engine** demo (real Hanoi weather, forecasting, MILP auction, settlement) — the
> two are complementary: this shows the *experience*, that shows the *machinery*.
