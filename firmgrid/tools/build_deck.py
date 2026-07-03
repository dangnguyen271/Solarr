"""Generate the FirmGrid presentation deck + TV poster (16:9 PPTX).

Run:  python build_deck.py
Dark navy/green theme matching the event's visual language.
Every slide carries speaker notes = the 5-minute script.
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).resolve().parent.parent / "submission"
OUT.mkdir(exist_ok=True)

W, H = Inches(13.333), Inches(7.5)

NAVY = RGBColor(0x0B, 0x12, 0x20)
PANEL = RGBColor(0x10, 0x1A, 0x30)
PANEL_EDGE = RGBColor(0x24, 0x3B, 0x5E)
GREEN = RGBColor(0x34, 0xD3, 0x99)
BLUE = RGBColor(0x38, 0xBD, 0xF8)
AMBER = RGBColor(0xFB, 0xBF, 0x24)
RED = RGBColor(0xF8, 0x71, 0x71)
INK = RGBColor(0xE2, 0xE8, 0xF0)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
FONT = "Avenir Next"


# --------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------- #
def add_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    bg.shadow.inherit = False
    # bottom accent strip
    strip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, H - Pt(6), W, Pt(6))
    strip.fill.solid()
    strip.fill.fore_color.rgb = GREEN
    strip.line.fill.background()
    strip.shadow.inherit = False
    return s


def txt(slide, x, y, w, h, runs, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT,
        space_after=6, anchor=MSO_ANCHOR.TOP):
    """runs: str, or list of paragraphs; paragraph = str or list of (text, color, bold)."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if isinstance(runs, str):
        runs = [runs]
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if isinstance(para, str):
            para = [(para, color, bold)]
        for text, c, b in para:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(size)
            r.font.bold = b
            r.font.color.rgb = c
            r.font.name = FONT
    return box


def kicker(slide, label, n=None):
    txt(slide, Inches(0.6), Inches(0.35), Inches(9), Inches(0.4),
        [[(f"FIRMGRID  ·  {label}" + (f"  ·  {n}/10" if n else ""), MUTED, True)]], size=12)


def headline(slide, text_, size=33, y=Inches(0.75), color=INK, w=Inches(12.1)):
    txt(slide, Inches(0.6), y, w, Inches(1.3), [[(text_, color, True)]], size=size)


def panel(slide, x, y, w, h, edge=PANEL_EDGE):
    p = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    p.adjustments[0] = 0.06
    p.fill.solid()
    p.fill.fore_color.rgb = PANEL
    p.line.color.rgb = edge
    p.line.width = Pt(1.2)
    p.shadow.inherit = False
    return p


def stat_tile(slide, x, y, w, h, big, label, accent=GREEN, big_size=32):
    panel(slide, x, y, w, h)
    txt(slide, x + Inches(0.18), y + Inches(0.12), w - Inches(0.36), Inches(0.8),
        [[(big, accent, True)]], size=big_size)
    txt(slide, x + Inches(0.18), y + h - Inches(0.95), w - Inches(0.36), Inches(0.85),
        [[(label, MUTED, False)]], size=12.5, space_after=0)


def bullets(slide, x, y, w, h, items, size=15.5, gap=8):
    """items: list of (lead, rest) tuples or plain strings."""
    paras = []
    for it in items:
        if isinstance(it, tuple):
            lead, rest = it
            paras.append([("▸ ", GREEN, True), (lead, INK, True), (rest, INK, False)])
        else:
            paras.append([("▸ ", GREEN, True), (it, INK, False)])
    txt(slide, x, y, w, h, paras, size=size, space_after=gap)


def notes(slide, text_):
    slide.notes_slide.notes_text_frame.text = text_


def flow_box(slide, x, y, w, h, title, sub, accent=BLUE):
    panel(slide, x, y, w, h, edge=accent)
    txt(slide, x + Inches(0.08), y + Inches(0.08), w - Inches(0.16), Inches(0.5),
        [[(title, accent, True)]], size=13.5, space_after=0)
    txt(slide, x + Inches(0.08), y + Inches(0.52), w - Inches(0.16), h - Inches(0.6),
        [[(sub, MUTED, False)]], size=10.5, space_after=0)


def arrow(slide, x, y, w=Inches(0.32)):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, y, w, Inches(0.28))
    a.fill.solid()
    a.fill.fore_color.rgb = GREEN
    a.line.fill.background()
    a.shadow.inherit = False


# --------------------------------------------------------------------- #
# deck
# --------------------------------------------------------------------- #
prs = Presentation()
prs.slide_width, prs.slide_height = W, H

# ---- 1 · title / hook -------------------------------------------------- #
s = add_slide(prs)
txt(s, Inches(0.6), Inches(1.5), Inches(12.1), Inches(1.0),
    [[("⚡ FirmGrid", GREEN, True)]], size=54)
txt(s, Inches(0.6), Inches(2.75), Inches(12.1), Inches(1.6),
    [[("Vietnam throws away clean power at noon —", INK, True)],
     [("and charges its clean vehicles on coal at night.", INK, True)]], size=30)
txt(s, Inches(0.6), Inches(4.6), Inches(12.1), Inches(0.9),
    [[("The intelligence layer that turns wasted rooftop solar into firm clean power.  ",
       MUTED, False), ("Sun-to-Wheels today. Sun-to-Servers next.", GREEN, True)]], size=19)
txt(s, Inches(0.6), Inches(6.4), Inches(12.1), Inches(0.6),
    [[("[TEAM_NAME]  ·  Asian Hackathon for Green Future 2026  ·  Track 1: "
       "Renewable Energy & Low-Carbon Mobility", MUTED, False)]], size=13)
notes(s, "HOOK (25s). Pause on the paradox: every sunny morning, EVN curtails rooftop "
         "solar because neighbourhood transformers can't absorb it. Every evening, the new "
         "electric motorbikes replacing Hanoi's petrol fleet charge on a majority-coal grid. "
         "Same city, same day, both directions of waste. FirmGrid closes both loops with one "
         "intelligence layer — and everything you'll see is running live on this laptop.")

# ---- 2 · the collision -------------------------------------------------- #
s = add_slide(prs)
kicker(s, "THE PROBLEM", 2)
headline(s, "2026: two demand waves collide with a grid that wastes its own sunshine")
y = Inches(2.0)
w3 = Inches(3.93)
stat_tile(s, Inches(0.6), y, w3, Inches(1.9), "~19 GW",
          "solar built — but curtailed feeder-wide on sunny mornings; routine cuts "
          "reported through April 2026", AMBER)
stat_tile(s, Inches(4.7), y, w3, Inches(1.9), "450,000",
          "petrol motorbikes to replace under Hanoi's LEZ (live since 1 July 2026) — "
          "~100 GWh/yr of new charging, defaulting to the coal evening", GREEN)
stat_tile(s, Inches(8.8), y, w3, Inches(1.9), "2× by 2030",
          "data-centre demand: 735 MW → 1,330–1,543 MW, mandated ≥50% green under the "
          "data-localisation law", BLUE)
bullets(s, Inches(0.6), Inches(4.35), Inches(12.1), Inches(2.6), [
    ("Generation peaks 10:00–14:00; demand peaks 18:00–22:00 ",
     "— and coal still carries over half the evening load."),
    ("26 June 2026: the rooftop surplus-sale cap jumped 20% → 50. ",
     "The ceiling just doubled — and nobody has a fair, safe way to allocate it."),
    ("Households pay twice: ", "panels curtailed at noon, full tariff for coal power at night."),
], size=16)
notes(s, "PROBLEM (45s). Three numbers: 19 GW of solar that gets curtailed; 450k motorbikes "
         "electrifying into the evening peak; data-centre demand doubling with a green "
         "mandate. And a fresh trigger — the surplus-sale cap was raised to 50% one week "
         "before this hackathon. More export pressure on the same transformers, no "
         "allocation mechanism. That's not a hardware gap, it's an intelligence gap.")

# ---- 3 · root cause ------------------------------------------------------ #
s = add_slide(prs)
kicker(s, "ROOT CAUSE", 3)
headline(s, "Curtailment is blunt because it is blind")
panel(s, Inches(0.6), Inches(1.95), Inches(5.9), Inches(4.6))
txt(s, Inches(0.85), Inches(2.15), Inches(5.4), Inches(0.5),
    [[("TODAY — the blunt cut", RED, True)]], size=17)
bullets(s, Inches(0.85), Inches(2.7), Inches(5.4), Inches(3.6), [
    "Operator sees one number: reverse flow at the transformer.",
    "No visibility into which household could keep exporting safely.",
    "So the whole feeder is cut — 100% of export lost to protect the last 10%.",
    "Households see nothing, earn nothing, and lose trust in solar.",
], size=14.5, gap=10)
panel(s, Inches(6.85), Inches(1.95), Inches(5.9), Inches(4.6), edge=GREEN)
txt(s, Inches(7.1), Inches(2.15), Inches(5.4), Inches(0.5),
    [[("THE MISSING LAYER", GREEN, True)]], size=17)
bullets(s, Inches(7.1), Inches(2.7), Inches(5.4), Inches(3.6), [
    "Predict per-transformer safe headroom 15 min – 24 h ahead.",
    "Allocate it fairly, household by household, window by window.",
    "Steer flexible mobility load INTO the surplus instead of the peak.",
    "All the data exists — weather, meters, inverters — in disconnected silos.",
], size=14.5, gap=10)
notes(s, "ROOT CAUSE (30s). EVN isn't wrong to curtail — it's protecting equipment while "
         "blind. The fix isn't more copper, it's sight: forecast the headroom, allocate it "
         "surgically, and give the surplus somewhere useful to go. Everything needed already "
         "exists in silos. Connecting them is a software problem — and software ships in "
         "months, not years.")

# ---- 4 · one engine, two tiers (money slide) ----------------------------- #
s = add_slide(prs)
kicker(s, "THE SOLUTION", 4)
headline(s, "One engine, two tiers — firmness as software", color=GREEN)
panel(s, Inches(0.6), Inches(1.9), Inches(5.9), Inches(4.7), edge=GREEN)
txt(s, Inches(0.85), Inches(2.1), Inches(5.4), Inches(0.8),
    [[("TIER 1 · SUN-TO-WHEELS", GREEN, True)], [("live in the prototype — legal today", MUTED, False)]],
    size=16, space_after=2)
bullets(s, Inches(0.85), Inches(3.0), Inches(5.4), Inches(3.4), [
    ("GridMind ", "forecasts safe headroom per transformer, per 15 minutes."),
    ("HeadRoom Auction ", "allocates it fairly — minimal, explainable curtailment."),
    ("FlexMatch ", "pays swap stations & depots to charge in the 10:00–14:00 sun."),
    ("TrustLedger ", "verifies delivery, pays VND, seals a tamper-evident audit."),
], size=13.5, gap=7)
panel(s, Inches(6.85), Inches(1.9), Inches(5.9), Inches(4.7), edge=BLUE)
txt(s, Inches(7.1), Inches(2.1), Inches(5.4), Inches(0.8),
    [[("TIER 2 · SUN-TO-SERVERS", BLUE, True)], [("the same engine, aggregated — 2027+", MUTED, False)]],
    size=16, space_after=2)
bullets(s, Inches(7.1), Inches(3.0), Inches(5.4), Inches(3.4), [
    ("Aggregate ", "hundreds of orchestrated feeders + storage into one portfolio."),
    ("Shape ", "firm, hour-matched 24/7 clean blocks — measured, auditable CFE."),
    ("Sell ", "via DPPA to data centres mandated ≥50% green by 2030."),
    ("Bridge ", "to nuclear-era firm baseload (2030–35): we win either way."),
], size=13.5, gap=7)
txt(s, Inches(0.6), Inches(6.75), Inches(12.1), Inches(0.5),
    [[("EVN stays the single buyer. No new law required. We don't fight the system — "
       "we make it intelligent.", AMBER, True)]], size=15)
notes(s, "SOLUTION (45s). Tier 1 is running today: forecast, auction, steer, settle — inside "
         "Decree 58, Decree 57 and VND payment law. Tier 2 is the same engine pointed at a "
         "bigger buyer: aggregate orchestrated feeders into firm 24/7 blocks for data "
         "centres. And the nuclear framing: firm baseload arrives 2030-35 at the earliest. "
         "FirmGrid is the bridge — if nuclear lands we built the flexible grid it needs; if "
         "it slips we're why the digital economy stayed clean. No-regrets.")

# ---- 5 · how tier 1 works ------------------------------------------------ #
s = add_slide(prs)
kicker(s, "HOW IT WORKS", 5)
headline(s, "One 15-minute market cycle")
y0 = Inches(2.1)
bw, bh, gap_ = Inches(2.72), Inches(1.75), Inches(0.36)
steps5 = [
    ("1 · SENSE + FORECAST",
     "Weather, meters, inverters → per-transformer headroom h(t) + per-home surplus, "
     "with confidence bands", BLUE),
    ("2 · BID",
     "Auto-Sell agents bid each home's surplus — hard-capped at what is physically "
     "possible (Sentinel)", GREEN),
    ("3 · CLEAR",
     "MILP auction: accept ≤ 90% of forecast headroom; fairness credits bound every "
     "household's wait", AMBER),
    ("4 · SETTLE",
     "Meter reconciliation → VND to e-wallets → hash-chained, publicly verifiable "
     "audit ledger", GREEN),
]
for i, (t5, sub5, c5) in enumerate(steps5):
    bx = Inches(0.6) + i * (bw + gap_)
    flow_box(s, bx, y0, bw, bh, t5, sub5, c5)
    if i:  # arrow centred in the gap before this box
        arrow(s, bx - gap_ + Inches(0.02), y0 + Inches(0.7))
panel(s, Inches(0.6), Inches(4.3), Inches(12.1), Inches(2.2))
txt(s, Inches(0.85), Inches(4.5), Inches(11.6), Inches(0.5),
    [[("MEANWHILE, ON THE DEMAND SIDE", BLUE, True)]], size=14)
bullets(s, Inches(0.85), Inches(5.0), Inches(11.6), Inches(1.4), [
    ("FlexMatch schedules swap stations & e-taxi depots into the solar window ",
     "— absorption is the cheapest headroom there is, and evening swaps become verified "
     "solar kilometres (~1 kg CO₂ avoided per swap, printed on the rider's receipt)."),
    ("Safety posture: ", "never allocate above 90% of forecast; human operator override "
     "outranks every automated decision."),
], size=14)
notes(s, "MECHANISM (35s). Walk the pipeline once: sense-forecast, bid, clear, settle — "
         "every 15 minutes. Two design choices to underline: bids are capped at physical "
         "reality so fraud is structurally impossible, and the auction never uses more than "
         "90% of forecast headroom so forecast error can't cause a breach. The operator can "
         "always override — human-in-command.")

# ---- 6 · live demo ------------------------------------------------------- #
s = add_slide(prs)
kicker(s, "WORKING PROTOTYPE — LIVE", 6)
headline(s, "The same sunny day, twice (digital twin of a Hanoi feeder)")
y = Inches(2.0)
w4 = Inches(2.9)
stat_tile(s, Inches(0.6), y, w4, Inches(1.8), "811 → 39",
          "kWh of clean energy wasted: baseline vs FirmGrid ON (95% recovered)", GREEN, 28)
stat_tile(s, Inches(3.67), y, w4, Inches(1.8), "19 → 0",
          "transformer limit breaches on the demo day", BLUE, 28)
stat_tile(s, Inches(6.74), y, w4, Inches(1.8), "837,000 ₫",
          "paid to households — for energy that is thrown away today", AMBER, 28)
stat_tile(s, Inches(9.81), y, w4, Inches(1.8), "F1 = 0.80",
          "congestion forecast skill on held-out days — measured, shown on screen", GREEN, 28)
panel(s, Inches(0.6), Inches(4.15), Inches(12.1), Inches(2.5))
txt(s, Inches(0.85), Inches(4.32), Inches(11.6), Inches(0.5),
    [[("JUDGES ARE INVITED TO BREAK IT", RED, True)]], size=14.5)
bullets(s, Inches(0.85), Inches(4.85), Inches(11.6), Inches(1.7), [
    ("Drag a storm front ", "— wipe out 60% of the sun: forecasts and the auction re-clear "
     "in seconds, zero breaches, and the system never does worse than today's baseline."),
    ("Inject a fraudulent 15 kW bid ", "— Sentinel blocks it before the auction because it "
     "exceeds the home's physical maximum; the block is sealed in the audit ledger."),
    ("Move any assumption ", "— every impact number recomputes live. No hidden constants."),
], size=14)
notes(s, "DEMO (60s — switch to the app). Tab 1: same day twice. Baseline: transformer "
         "breaches at midday, feeder cut, 811 kWh wasted. FirmGrid ON: stations ramp into "
         "the sun, auction clears, zero breaches, 39 kWh wasted, 837k dong paid. Tab 2: "
         "invite a judge to drag the storm slider and inject the fraud bid. The point: this "
         "is not a dashboard — every number is a decision the system made and can explain.")

# ---- 7 · impact ----------------------------------------------------------- #
s = add_slide(prs)
kicker(s, "IMPACT", 7)
headline(s, "The arithmetic is on the table — every assumption adjustable")
y = Inches(2.0)
stat_tile(s, Inches(0.6), y, Inches(3.93), Inches(1.9), "15–19 GWh/yr",
          "recovered by a 1,000-transformer Hanoi rollout ≈ 10,000–13,000 t CO₂/yr "
          "(grid factor 0.681 — official 2024 value)", GREEN, 26)
stat_tile(s, Inches(4.7), y, Inches(3.93), Inches(1.9), "+16–27 kt CO₂/yr",
          "from steering 20–30% of the LEZ's ~100 GWh/yr charging wave into the solar "
          "window — ≈1 kg per swap", BLUE, 26)
stat_tile(s, Inches(8.8), y, Inches(3.93), Inches(1.9), "54% CFE · $84",
          "hour-matched clean coverage and $/MWh for a 20 MW data-centre block "
          "(vs $92 grid) — Tier 2, computed live", AMBER, 26)
bullets(s, Inches(0.6), Inches(4.35), Inches(12.1), Inches(2.4), [
    ("Households: ", "0.6–1.0 million ₫/yr per 5 kWp — from energy discarded today; "
     "restored payback keeps the rooftop flywheel spinning."),
    ("Stations: ", "27–44 million ₫/yr saved each — real margin in a thin-margin business, "
     "aligned with the grid's needs."),
    ("EVN: ", "transformer reinforcement deferred — hundreds of millions of ₫ per site; "
     "a demand-side lever it has never had."),
    ("National scenario (20,000 transformers by 2030): ", "300–380 GWh/yr ≈ "
     "200,000–260,000 t CO₂/yr — before PDP8 doubles the solar fleet."),
], size=14.5)
notes(s, "IMPACT (40s). Bottom-up, not hand-waved: 30 homes × 5 kWp × 1,050 kWh/kWp × 15% "
         "curtailed × 70% recovered — that chain is on screen in the prototype with sliders. "
         "Hanoi scale: 15-19 GWh and ~10-13 kt CO₂ a year. Mobility adds 16-27 kt. And Tier 2 "
         "turns it into a product: 54% hour-matched CFE at $84/MWh — cheaper than the grid "
         "tariff a data centre pays today.")

# ---- 8 · why us / moat ----------------------------------------------------- #
s = add_slide(prs)
kicker(s, "WHY THIS WINS", 8)
headline(s, "Regulation-native, fairness-bounded, and compounding")
bullets(s, Inches(0.6), Inches(2.0), Inches(12.1), Inches(4.4), [
    ("Ships without new law: ", "households sell under Decree 58/2025 (EVN sole buyer), "
     "stations join as DPPA large consumers (57/2025), settlement is VND-only (52/2024). "
     "Powerledger-style P2P pilots record trades; none of them predict congestion — the "
     "hard part is the part we built."),
    ("Not 'just build batteries': ", "PDP8's 10–16 GW of storage takes years and billions; "
     "FirmGrid monetises the meters and rooftops already installed, this year — and makes "
     "every future battery more valuable. Complementary, not competing."),
    ("Fairness as physics: ", "a rejection-credit bound guarantees no household is "
     "persistently excluded — the property that makes a public utility able to say yes."),
    ("The data flywheel: ", "every onboarded feeder improves the forecasts; better "
     "forecasts unlock more headroom; more headroom attracts more feeders. Tier 1's "
     "flywheel is Tier 2's product."),
    ("Honest AI: ", "metrics on held-out days, on screen; synthetic twin with declared "
     "assumptions and a transfer-learning path to real telemetry. Judges can inspect "
     "everything."),
], size=15, gap=12)
notes(s, "MOAT (35s). Pre-empt the three obvious objections. One: 'isn't this the "
         "Powerledger pilot?' — that's a ledger, it records trades after the fact; it can't "
         "tell you whether a trade is safe beforehand. Two: 'why not wait for storage?' — "
         "years and billions; we capture value from existing assets now and make storage "
         "more valuable when it lands. Three: 'is the AI real?' — held-out metrics on "
         "screen, assumptions declared, judges can change them live.")

# ---- 9 · roadmap ----------------------------------------------------------- #
s = add_slide(prs)
kicker(s, "ROADMAP", 9)
headline(s, "From this laptop to ASEAN")
stages = [
    ("Q3 2026", "Shadow pilot", "Read-only on one EVNHANOI feeder; forecast skill vs real telemetry", BLUE),
    ("Q4 2026", "Hardware-in-loop", "20 volunteer homes via inverter APIs; one station honours schedules", GREEN),
    ("H1 2027", "Sandbox, real money", "200 households + 10 stations, EVN as settlement counterparty", AMBER),
    ("H2 2027", "City scale", "1,000 constrained transformers + first firm-block DPPA with a data centre", GREEN),
    ("2028+", "Second city → ASEAN", "Da Nang / HCMC; Thailand, Indonesia, Philippines — config, not re-architecture", BLUE),
]
x = Inches(0.6)
for when, title_, sub, c in stages:
    p = panel(s, x, Inches(2.2), Inches(2.32), Inches(3.4), edge=c)
    txt(s, x + Inches(0.12), Inches(2.4), Inches(2.08), Inches(0.4), [[(when, c, True)]], size=14)
    txt(s, x + Inches(0.12), Inches(2.85), Inches(2.08), Inches(0.7), [[(title_, INK, True)]], size=14.5)
    txt(s, x + Inches(0.12), Inches(3.6), Inches(2.08), Inches(1.9), [[(sub, MUTED, False)]], size=11)
    x += Inches(2.45)
txt(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(0.9),
    [[("De-risked by design: if market regulation lags, predictive minimal curtailment alone "
       "is a pure operations tool EVN can adopt unilaterally — revenue while we wait.",
       AMBER, True)]], size=14.5)
notes(s, "ROADMAP (30s). Staged and de-risked: shadow pilot first — no money moves until "
         "forecasts prove themselves on real telemetry. Then hardware-in-the-loop, then a "
         "sandbox with real settlement, then city scale and the first firm DPPA block. Each "
         "stage has a named success metric. And the floor: even with zero market reform, "
         "curtailment prediction alone is a product EVN can buy tomorrow.")

# ---- 10 · close ------------------------------------------------------------- #
s = add_slide(prs)
txt(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(2.6),
    [[("Vietnam has the panels, the swap stations,", INK, True)],
     [("the data — and, as of this month, the policy moment.", INK, True)],
     [("", INK, False)],
     [("What's missing is the intelligence layer that connects them.", GREEN, True)]],
    size=30)
txt(s, Inches(0.6), Inches(4.5), Inches(12.1), Inches(0.8),
    [[("FirmGrid is that layer: every safely exportable ray of morning sunshine becomes a "
       "fair payment to a household, a clean kilometre for a rider — and, at scale, firm "
       "24/7 power for the digital economy.", MUTED, False)]], size=17)
txt(s, Inches(0.6), Inches(6.1), Inches(12.1), Inches(0.9),
    [[("⚡ FirmGrid  ·  [TEAM_NAME]", GREEN, True)],
     [("[Member 1] · [Member 2] · [Member 3] · [Member 4]   —   demo: streamlit run app.py",
       MUTED, False)]], size=16)
notes(s, "CLOSE (20s). Land the one-sentence pitch: a rooftop in Tay Ho charges a Grab "
         "driver's battery at noon, so the sunshine wasted this morning becomes the clean "
         "ride home tonight — and the same engine will sell firm clean power to the data "
         "centres being built under the localisation law. We're ready for questions — and "
         "the prototype is live if you'd like to try to break it.")

deck_path = OUT / "[TEAM_NAME]_FirmGrid_Slides.pptx"
prs.save(deck_path)
print(f"[deck] {deck_path} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")

# --------------------------------------------------------------------- #
# poster (single 16:9 slide for the TV display)
# --------------------------------------------------------------------- #
pp = Presentation()
pp.slide_width, pp.slide_height = W, H
s = add_slide(pp)
txt(s, Inches(0.6), Inches(0.45), Inches(12.1), Inches(1.0),
    [[("⚡ FirmGrid", GREEN, True)]], size=44)
txt(s, Inches(0.6), Inches(1.5), Inches(12.1), Inches(0.9),
    [[("Vietnam throws away clean power at noon and charges its clean vehicles on coal "
       "at night. FirmGrid closes both loops.", INK, True)]], size=19)
y = Inches(2.6)
stat_tile(s, Inches(0.6), y, Inches(2.9), Inches(1.75), "811 → 39",
          "kWh wasted on one feeder-day: baseline vs FirmGrid ON — 95% recovered", GREEN, 26)
stat_tile(s, Inches(3.67), y, Inches(2.9), Inches(1.75), "15–19 GWh",
          "recovered per year across 1,000 Hanoi transformers ≈ 10–13 kt CO₂/yr", AMBER, 26)
stat_tile(s, Inches(6.74), y, Inches(2.9), Inches(1.75), "≈1 kg CO₂",
          "avoided per battery swap charged in the solar window", BLUE, 26)
stat_tile(s, Inches(9.81), y, Inches(2.9), Inches(1.75), "54% · $84",
          "hour-matched CFE and $/MWh for a 20 MW data-centre firm block (vs $92 grid)", GREEN, 26)
panel(s, Inches(0.6), Inches(4.6), Inches(7.9), Inches(2.35))
txt(s, Inches(0.85), Inches(4.75), Inches(7.5), Inches(0.45),
    [[("FORECAST → AUCTION → STEER → SETTLE, every 15 minutes", BLUE, True)]], size=14)
bullets(s, Inches(0.85), Inches(5.25), Inches(7.5), Inches(1.6), [
    ("GridMind ", "predicts safe headroom per transformer (F1 0.80, held-out)."),
    ("HeadRoom Auction ", "allocates it fairly — minimal, explainable curtailment."),
    ("FlexMatch ", "pays swap stations to charge on sunshine, not coal."),
    ("TrustLedger ", "verifies, pays VND, seals a tamper-evident audit."),
], size=12.5, gap=4)
panel(s, Inches(8.7), Inches(4.6), Inches(4.0), Inches(2.35), edge=GREEN)
txt(s, Inches(8.95), Inches(4.75), Inches(3.5), Inches(0.5),
    [[("TWO TIERS, ONE ENGINE", GREEN, True)]], size=14)
txt(s, Inches(8.95), Inches(5.25), Inches(3.5), Inches(1.6),
    [[("Tier 1 · Sun-to-Wheels — live today, legal today (Decrees 58 & 57/2025, VND rails).",
       INK, False)],
     [("Tier 2 · Sun-to-Servers — firm 24/7 blocks for data centres via DPPA.", INK, False)],
     [("[TEAM_NAME] · Track 1 · 2026", MUTED, False)]], size=12.5)
poster_path = OUT / "[TEAM_NAME]_FirmGrid_Poster.pptx"
pp.save(poster_path)
print(f"[poster] {poster_path}")
