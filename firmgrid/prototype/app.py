"""FirmGrid — live prototype dashboard.

Run:  streamlit run app.py
Fully offline; every number is computed live from the digital twin.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from firmblock import build_firm_block
from gridmind import GridMind
from market import run_day
from twin import REVERSE_LIMIT_KW, FeederTwin, pick_demo_day

# ----------------------------------------------------------------------- #
# Page + theme
# ----------------------------------------------------------------------- #
st.set_page_config(
    page_title="FirmGrid — firm clean power, as software",
    page_icon="⚡",
    layout="wide",
)

GREEN = "#34d399"
BLUE = "#38bdf8"
AMBER = "#fbbf24"
RED = "#f87171"
INK = "#e2e8f0"
GRID = "rgba(148,163,184,0.15)"

st.markdown(
    """
    <style>
      .stApp { background: #0b1220; }
      h1, h2, h3, h4, p, li, span, div { color: #e2e8f0; }
      div[data-testid="stMetric"] {
        background: #101a30; border: 1px solid rgba(56,189,248,0.25);
        border-radius: 12px; padding: 12px 16px;
      }
      div[data-testid="stMetricLabel"] { color: #94a3b8; }
      .fg-hero { font-size: 1.05rem; color: #94a3b8; margin-top: -8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def dark_fig(fig: go.Figure, height=340) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(16,26,48,0.6)",
        height=height,
        margin=dict(l=40, r=20, t=40, b=30),
        font=dict(color=INK, size=13),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
    )
    return fig


# ----------------------------------------------------------------------- #
# Cached simulation + models
# ----------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Building the digital twin (one simulated year)…")
def load_world():
    twin = FeederTwin()
    df = twin.simulate_year()
    mind = GridMind().fit(df)
    demo_day = pick_demo_day(df)
    return twin, df, mind, demo_day


@st.cache_data(show_spinner="Clearing markets for the day…")
def cached_day(date: str, cloud: float, fraud: bool, flex: float):
    twin, df, mind, _ = load_world()
    fraud_bid = {"hid": 3, "kw": 15.0} if fraud else None
    return run_day(twin, df, mind, date, cloud_dim=cloud, fraud_bid=fraud_bid, flex_share=flex)


@st.cache_data(show_spinner="Shaping the 24/7 firm block…")
def cached_block(n_tr: int, storage_mwh: float, storage_mw: float, dc_mw: float, rec: float):
    _, df, _, _ = load_world()
    return build_firm_block(df, n_tr, storage_mwh, storage_mw, dc_mw, rec)


twin, df, mind, DEMO_DAY = load_world()

# ----------------------------------------------------------------------- #
# Header
# ----------------------------------------------------------------------- #
st.title("⚡ FirmGrid")
st.markdown(
    '<p class="fg-hero">The intelligence layer that turns Vietnam\'s wasted solar into '
    "firm clean power — <b>Sun-to-Wheels</b> today, <b>Sun-to-Servers</b> next. "
    "One 400 kVA Hanoi transformer: 30 PV homes, 25 non-PV homes, 3 C&amp;I rooftops, "
    "2 swap stations, 1 e-taxi depot — simulated for a full year, auctioned every 15 minutes.</p>",
    unsafe_allow_html=True,
)

m = mind.metrics
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("GridMind congestion F1 (held-out days)", f"{m['congestion_f1']:.2f}")
mc2.metric("Surplus forecast MAE", f"{m['surplus_mae_kw']:.1f} kW feeder-level")
mc3.metric("Held-out test days", f"{m['test_days']}")
mc4.metric("Transformer reverse-flow limit", f"{REVERSE_LIMIT_KW:.0f} kW")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "① Baseline vs FirmGrid ON",
        "② Judge-in-the-loop",
        "③ Firm Block Studio (Tier 2)",
        "④ Impact & assumptions",
    ]
)

# ======================================================================= #
# TAB 1 — the counterfactual day
# ======================================================================= #
with tab1:
    st.subheader(f"The same sunny day, twice — {DEMO_DAY}")
    res = cached_day(DEMO_DAY, 0.0, False, 0.7)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Clean energy wasted (baseline)",
        f"{res.baseline_wasted_kwh:.0f} kWh",
        help="Feeder-wide curtailment: every export cut when the transformer nears its limit.",
    )
    c2.metric(
        "Wasted with FirmGrid ON",
        f"{res.fg_wasted_kwh:.0f} kWh",
        delta=f"−{res.recovered_kwh:.0f} kWh recovered",
        delta_color="inverse",
    )
    c3.metric("CO₂ avoided today", f"{res.co2_avoided_kg:.0f} kg")
    c4.metric("Paid to households today", f"{res.vnd_paid:,.0f} ₫")
    c5.metric(
        "Limit breaches",
        f"{res.baseline_breaches} → {res.fg_breaches}",
        help="15-minute windows where reverse flow exceeds the safe limit.",
    )

    t = res.df_day.index
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=res.reverse_baseline_kw, name="Reverse flow — baseline",
                             line=dict(color=RED, width=2)))
    fig.add_trace(go.Scatter(x=t, y=res.reverse_fg_kw, name="Reverse flow — FirmGrid ON",
                             line=dict(color=GREEN, width=2)))
    fig.add_hline(y=REVERSE_LIMIT_KW, line_dash="dash", line_color=AMBER,
                  annotation_text="safe limit", annotation_font_color=AMBER)
    fig.update_layout(title="Transformer reverse flow (kW): blunt curtailment vs auctioned headroom")
    st.plotly_chart(dark_fig(fig), width="stretch")

    colA, colB = st.columns(2)
    with colA:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=t, y=res.df_day["surplus_total_kw"], name="Available surplus",
                                  line=dict(color=AMBER, width=1.5), fill="tozeroy",
                                  fillcolor="rgba(251,191,36,0.15)"))
        fig2.add_trace(go.Scatter(x=t, y=res.df_day["station_baseline_kw"],
                                  name="Station charging — uncoordinated (evening, coal)",
                                  line=dict(color=RED, width=2, dash="dot")))
        fig2.add_trace(go.Scatter(x=t, y=res.steered_station_kw,
                                  name="Station charging — FlexMatch (solar window)",
                                  line=dict(color=BLUE, width=2)))
        fig2.update_layout(title="Sun-to-Wheels: swap-station charging moves into the sun")
        st.plotly_chart(dark_fig(fig2), width="stretch")
    with colB:
        st.markdown("**HeadRoom auction log (every 2 hours)** — every decision explainable:")
        st.dataframe(pd.DataFrame(res.allocations_log), width="stretch", height=250)
        st.markdown(
            f"- FlexMatch shifted **{res.flex_stats['shifted_kwh']:.0f} kWh** of station charging "
            f"into the solar window → stations save **{res.flex_stats['station_saving_vnd']:,.0f} ₫** today.\n"
            f"- Fairness bound: longest any household waited = "
            f"**{res.fairness_max_wait} consecutive rejections**.\n"
            f"- TrustLedger chain valid: **{res.ledger.verify_chain()}** "
            f"({len(res.ledger.blocks)} hash-chained events)."
        )

# ======================================================================= #
# TAB 2 — judge-in-the-loop
# ======================================================================= #
with tab2:
    st.subheader("Break it yourself")
    st.markdown(
        "Drag a storm front over the feeder, or inject a fraudulent bid — "
        "forecasts, the auction and Sentinel all re-clear live."
    )
    jc1, jc2, jc3 = st.columns([2, 1, 1])
    cloud = jc1.slider("☁️ Storm front — % of solar wiped out", 0, 90, 0, 5) / 100.0
    fraud = jc2.toggle("💀 Inject fraudulent 8 kW bid (household H03)", value=False)
    flex = jc3.slider("FlexMatch shift share", 0.0, 1.0, 0.7, 0.1)

    jres = cached_day(DEMO_DAY, cloud, fraud, flex)

    j1, j2, j3, j4 = st.columns(4)
    j1.metric("Recovered today", f"{jres.recovered_kwh:.0f} kWh")
    j2.metric("CO₂ avoided", f"{jres.co2_avoided_kg:.0f} kg")
    j3.metric("Households paid", f"{jres.vnd_paid:,.0f} ₫")
    j4.metric("Breaches (FirmGrid ON)", jres.fg_breaches)

    if fraud:
        for msg in jres.fraud_events:
            st.error(f"🛡️ Sentinel — {msg}")
        if not jres.fraud_events:
            st.warning("Fraud bid was within physical limits this window — try a cloudier day.")

    t = jres.df_day.index
    figj = go.Figure()
    figj.add_trace(go.Scatter(x=t, y=jres.df_day["surplus_total_kw"], name="Surplus after storm",
                              line=dict(color=AMBER, width=2), fill="tozeroy",
                              fillcolor="rgba(251,191,36,0.12)"))
    figj.add_trace(go.Scatter(x=t, y=jres.reverse_fg_kw, name="Reverse flow — FirmGrid ON",
                              line=dict(color=GREEN, width=2)))
    figj.add_hline(y=REVERSE_LIMIT_KW, line_dash="dash", line_color=AMBER)
    figj.update_layout(title="The system stays inside the safe envelope, whatever you throw at it")
    st.plotly_chart(dark_fig(figj), width="stretch")

    st.caption(
        "Safety posture: the auction never allocates more than 90% of forecast headroom, "
        "bids are hard-capped at physically possible surplus, and a human operator override "
        "outranks every automated decision."
    )

# ======================================================================= #
# TAB 3 — Firm Block Studio (Tier 2)
# ======================================================================= #
with tab3:
    st.subheader("Sun-to-Servers — shape a firm 24/7 block for a data centre")
    st.markdown(
        "The same engine, aggregated: N orchestrated transformers + shared storage are shaped "
        "into an hour-matched clean block sold via DPPA. Data-centre demand is mandated "
        "**≥50% green by 2030** — this is where Tier 1's data flywheel becomes Tier 2's product."
    )
    b1, b2, b3, b4, b5 = st.columns(5)
    n_tr = b1.slider("Orchestrated transformers", 100, 2000, 800, 100)
    dc_mw = b2.slider("Data-centre load (MW)", 5, 50, 20, 5)
    storage_mwh = b3.slider("Storage (MWh)", 0, 500, 160, 20)
    storage_mw = b4.slider("Storage power (MW)", 5, 100, 40, 5)
    rec = b5.slider("Recovery rate", 0.3, 0.9, 0.7, 0.05)

    blk = cached_block(n_tr, float(storage_mwh), float(storage_mw), float(dc_mw), float(rec))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Hourly CFE match", f"{blk['cfe_score']*100:.0f}%",
              help="Share of the data centre's load covered by hour-matched clean energy.")
    k2.metric("Blended block cost", f"${blk['blended_cost_usd_mwh']:.0f}/MWh",
              delta=f"grid: ${blk['grid_cost_usd_mwh']:.0f}/MWh")
    k3.metric("Clean energy delivered", f"{blk['clean_gwh']:.1f} GWh/yr")
    k4.metric("CO₂ avoided", f"{blk['co2_avoided_t_per_year']:,.0f} t/yr")

    bh = blk["by_hour"]
    figb = go.Figure()
    figb.add_trace(go.Bar(x=bh.index, y=bh["direct_solar_mw"], name="Direct recovered solar",
                          marker_color=AMBER))
    figb.add_trace(go.Bar(x=bh.index, y=bh["battery_mw"], name="Storage (solar-charged)",
                          marker_color=GREEN))
    figb.add_trace(go.Bar(x=bh.index, y=bh["grid_mw"], name="Residual grid",
                          marker_color="rgba(148,163,184,0.5)"))
    figb.update_layout(barmode="stack",
                       title="Average day, hour by hour: what serves the data centre",
                       xaxis_title="hour of day", yaxis_title="MW")
    st.plotly_chart(dark_fig(figb, height=380), width="stretch")

    st.caption(
        "Indicative economics: recovered firm solar $60/MWh (IRENA band $54–82), storage cycling "
        "$45/MWh throughput, grid tariff $92/MWh. Every parameter is a slider or a constant a "
        "judge can change."
    )

# ======================================================================= #
# TAB 4 — impact arithmetic with assumptions on the table
# ======================================================================= #
with tab4:
    st.subheader("Impact arithmetic — every assumption adjustable")
    a1, a2, a3 = st.columns(3)
    with a1:
        homes = st.slider("PV homes per constrained transformer", 10, 60, 30)
        kwp = st.slider("Average system size (kWp)", 3.0, 10.0, 5.0, 0.5)
    with a2:
        yield_kwh = st.slider("Specific yield (kWh/kWp·yr)", 900, 1300, 1050, 25)
        curt = st.slider("Share lost to curtailment (%)", 5, 30, 15) / 100
    with a3:
        recov = st.slider("FirmGrid recovery rate (%)", 40, 90, 70) / 100
        ntr = st.slider("Constrained transformers (Hanoi)", 100, 3000, 1000, 100)

    ef = 0.681  # official 2024 Vietnam grid emission factor, tCO2/MWh
    per_tr_mwh = homes * kwp * yield_kwh * curt / 1000.0
    rec_tr = per_tr_mwh * recov
    city_gwh = rec_tr * ntr / 1000.0
    city_co2 = city_gwh * 1000 * ef / 1000.0  # t

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Curtailed per transformer", f"{per_tr_mwh:.1f} MWh/yr")
    i2.metric("Recovered per transformer", f"{rec_tr:.1f} MWh/yr")
    i3.metric("Hanoi rollout recovery", f"{city_gwh:.1f} GWh/yr")
    i4.metric("CO₂ avoided (supply side)", f"{city_co2:,.0f} t/yr")

    st.markdown(
        f"""
**The chain, written out** — {homes} homes × {kwp:.1f} kWp × {yield_kwh} kWh/kWp·yr ×
{curt*100:.0f}% curtailed = **{per_tr_mwh:.1f} MWh/yr** stranded per transformer.
FirmGrid recovers {recov*100:.0f}% → **{rec_tr:.1f} MWh/yr**. Across {ntr:,} constrained
Hanoi transformers → **{city_gwh:.1f} GWh/yr ≈ {city_co2:,.0f} t CO₂/yr**
(grid factor {ef} tCO₂/MWh, official 2024 value).

**Mobility side (Tier 1):** replacing 450,000 petrol motorbikes ≈ 100 GWh/yr of new charging
demand in Hanoi. Steering 20–30% into the solar window avoids a further **16,000–27,000 t CO₂/yr**
— about **1 kg CO₂ per swap**, printed on the rider's receipt.

**Digital side (Tier 2):** data-centre demand ~735 MW (2025) → **1,330–1,543 MW by 2030**,
mandated ≥50% green. One 20 MW block at the CFE score shown in Tab ③ is the proof-of-product
for Vietnam's first firm-solar DPPA.
        """
    )
    st.caption(
        "Households: ~800 kWh/yr recovered ≈ 560k ₫ at the Decree-58 reference price, "
        "0.6–1.0M ₫ with FlexMatch premiums. Stations: ≈27–44M ₫/yr saved. "
        "EVN: transformer reinforcement deferred at hundreds of millions ₫ per site."
    )
