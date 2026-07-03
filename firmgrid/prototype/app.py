"""FirmGrid — live prototype dashboard (stakeholder view, bright theme).

Run:  streamlit run app.py
Fully offline; every number is computed live from the digital twin.
One tab per stakeholder: who they are, what decision FirmGrid enables.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from firmblock import build_firm_block
from gridmind import GridMind
from mapview import day_sankey, feeder_map, tx_gauge, unmanaged_reverse
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

GREEN = "#059669"
BLUE = "#0284c7"
AMBER = "#d97706"
RED = "#dc2626"
INK = "#0f172a"
MUTED = "#64748b"
GRIDLINE = "rgba(15,23,42,0.07)"

st.markdown(
    """
    <style>
      div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #059669;
        border-radius: 10px; padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(15,23,42,0.06);
      }
      div[data-testid="stMetricLabel"] { color: #64748b; }
      .fg-hero { font-size: 1.02rem; color: #475569; margin-top: -6px; }
      .fg-model { font-size: .9rem; color: #475569; background: #ffffff;
        border: 1px solid #e2e8f0; border-left: 4px solid #059669; border-radius: 10px;
        padding: 11px 15px; margin: 6px 0 4px; line-height: 1.65; }
      .fg-model b { color: #0f172a; }
      .fg-banner {
        border-radius: 10px; padding: 10px 16px; margin: 2px 0 14px;
        border: 1px solid #e2e8f0; background: #ffffff;
        box-shadow: 0 1px 3px rgba(15,23,42,0.05);
      }
      .fg-banner b { font-size: 1.0rem; }
      .fg-banner span { color: #475569; font-size: 0.93rem; }
      .fg-receipt {
        border-radius: 12px; padding: 14px 18px; margin: 6px 0;
        background: #ecfdf5; border: 1.5px solid #059669; color: #064e3b;
        font-size: 1.0rem;
      }
      button[data-baseweb="tab"] { font-size: 1.0rem; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)


def banner(color: str, icon: str, who: str, decision: str):
    st.markdown(
        f"""<div class="fg-banner" style="border-left: 5px solid {color};">
        <b>{icon} {who}</b><br><span><b>Decision this screen enables:</b> {decision}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def clean_fig(fig: go.Figure, height=340) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=height,
        margin=dict(l=40, r=20, t=40, b=30),
        font=dict(color=INK, size=13),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor=GRIDLINE),
        yaxis=dict(gridcolor=GRIDLINE),
    )
    return fig


# ----------------------------------------------------------------------- #
# Cached simulation + models
# ----------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Building the digital twin (one year of real Hanoi weather)…")
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
res0 = cached_day(DEMO_DAY, 0.0, False, 0.7)

# ----------------------------------------------------------------------- #
# Header
# ----------------------------------------------------------------------- #
st.title("⚡ FirmGrid")
st.markdown(
    '<p class="fg-hero">A local marketplace that turns a neighbourhood\'s surplus rooftop '
    "solar into firm clean power — coordinated so the grid stays safe.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="fg-model"><b>What this models —</b> one Hanoi low-voltage feeder on a single '
    "400&nbsp;kVA transformer:<br>"
    "• <b>30</b> homes with rooftop solar — the <b>sellers</b><br>"
    "• <b>25</b> homes without solar — local <b>consumers</b> who absorb nearby export<br>"
    "• <b>3</b> business rooftops (shop, school, small factory) — larger sellers<br>"
    "• <b>2</b> battery-swap stations + <b>1</b> e-taxi depot — <b>flexible demand</b> that can "
    "charge on midday surplus<br>"
    f"Driven by {twin.data_source}; one day shown is {DEMO_DAY}.</p>",
    unsafe_allow_html=True,
)

m = mind.metrics
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Clean energy rescued today", f"{res0.recovered_kwh:.0f} kWh",
           delta=f"{res0.recovered_kwh/max(res0.baseline_wasted_kwh,1)*100:.0f}% of what is wasted now")
mc2.metric("Paid to solar families today", f"{res0.vnd_paid:,.0f} ₫")
mc3.metric("Grid safety", f"{res0.baseline_breaches} → {res0.fg_breaches} breaches",
           help="15-minute windows where reverse flow exceeds the safe limit, without vs with FirmGrid.")
mc4.metric("Forecast accuracy", f"F1 = {m['congestion_f1']:.2f}",
           help="Predicts a transformer overload about an hour ahead — catches roughly 6 of every 7, measured on days not used for training.")

tabs = st.tabs([
    "⚡ Grid operator (EVN)",
    "🏠 Solar households",
    "🔋 Swap stations & fleets",
    "🏢 Data centres",
    "🌏 City impact",
])

# ======================================================================= #
# TAB 1 — GRID OPERATOR
# ======================================================================= #
with tabs[0]:
    banner(GREEN, "⚡", "EVN distribution operator",
           "when and how little to curtail, window by window — instead of cutting the whole feeder.")

    c1, c2 = st.columns([3, 1])
    tsel = c1.slider("Time of day (15-minute windows)", 0, 95, 49, 1, key="op_t")
    storm = c2.slider("☁️ Cloud cover — % of solar lost", 0, 90, 0, 10, key="op_storm")
    opres = cached_day(DEMO_DAY, storm / 100.0, False, 0.7) if storm else res0
    tstamp = opres.df_day.index[tsel]

    m1, m2 = st.columns(2)
    with m1:
        st.plotly_chart(feeder_map(twin, opres, tsel, mode="base"), width="stretch", key="op_map_b")
    with m2:
        st.plotly_chart(feeder_map(twin, opres, tsel, mode="on"), width="stretch", key="op_map_on")

    g1, g2, g3 = st.columns([1, 1, 2])
    with g1:
        st.plotly_chart(tx_gauge(unmanaged_reverse(opres, tsel),
                                 "Unmanaged flow (forces today's cut)"), width="stretch", key="op_g1")
    with g2:
        st.plotly_chart(tx_gauge(float(opres.reverse_fg_kw[tsel]),
                                 "Managed flow — FirmGrid"), width="stretch", key="op_g2")
    with g3:
        t = opres.df_day.index
        figr = go.Figure()
        figr.add_trace(go.Scatter(x=t, y=opres.reverse_baseline_kw, name="Reverse flow — today",
                                  line=dict(color=RED, width=2)))
        figr.add_trace(go.Scatter(x=t, y=opres.reverse_fg_kw, name="Reverse flow — FirmGrid",
                                  line=dict(color=GREEN, width=2)))
        figr.add_hline(y=REVERSE_LIMIT_KW, line_dash="dash", line_color=AMBER,
                       annotation_text="safe limit", annotation_font_color=AMBER)
        figr.update_layout(title="The whole day at a glance")
        st.plotly_chart(clean_fig(figr, height=300), width="stretch", key="op_day")

    st.plotly_chart(day_sankey(opres, "on"), width="stretch", key="op_sankey")
    with st.expander("📋 Auction log — every decision, explained in one sentence"):
        st.dataframe(pd.DataFrame(opres.allocations_log), width="stretch", height=240)
    st.caption(
        "Safety rules: never allocate above 90% of forecast headroom · bids capped at each "
        "home's physical maximum · a manual operator override outranks every automated decision."
    )

# ======================================================================= #
# TAB 2 — HOUSEHOLDS
# ======================================================================= #
with tabs[1]:
    banner(AMBER, "🏠", "Households with rooftop solar",
           "none needed: switch on Auto-Sell once and earn passively — with a fair queue and a "
           "verifiable payment trail.")

    sold_per_home = res0.home_accepted_kw.sum(axis=0) * 0.25
    offered_per_home = res0.home_surplus_kw.sum(axis=0) * 0.25
    earn_per_home = sold_per_home * 700.0
    pv_ids = [h.hid for h in twin.households if h.kwp > 0]

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Families paid today", f"{int((earn_per_home > 0).sum())}")
    h2.metric("Neighbourhood earnings", f"{res0.vnd_paid:,.0f} ₫")
    h3.metric("Longest wait for a 'yes'", f"{res0.fairness_max_wait} window(s)",
              help="Fairness bound: every rejection earns a priority credit for the next auction.")
    h4.metric("Payment trail verified", "✓ ledger intact" if res0.ledger.verify_chain() else "✗",
              help=f"{len(res0.ledger.blocks)} events, each hash-chained to the previous one.")

    st.markdown("##### Pick a family")
    hid = st.selectbox("Household", pv_ids, index=1,
                       format_func=lambda i: f"H{i:02d} · {twin.households[i].kwp:.1f} kWp rooftop",
                       key="home_pick")
    p1, p2 = st.columns([1, 2])
    with p1:
        st.markdown(
            f"""<div class="fg-receipt">📱 <b>Hôm nay bạn kiếm được
            {earn_per_home[hid]:,.0f} ₫</b><br>
            Sold {sold_per_home[hid]:.1f} of {offered_per_home[hid]:.1f} kWh surplus ·
            Auto-Sell ON · paid to your e-wallet</div>""",
            unsafe_allow_html=True,
        )
        declined = int(((res0.home_surplus_kw[:, hid] > 0.05)
                        & (res0.home_accepted_kw[:, hid] <= 1e-3)).sum())
        st.markdown(
            f"- Windows declined today: **{declined}** (each earns a priority credit for next time)\n"
            f"- Each step is traceable: bid → auction → meter reading → payment\n"
            f"- Households pay nothing to take part."
        )
        fraud = st.toggle("Simulate a false bid: 15 kW, above this roof's limit", key="home_fraud")
        if fraud:
            fres = cached_day(DEMO_DAY, 0.0, True, 0.7)
            for msg in fres.fraud_events:
                st.error(f"🛡️ Sentinel — {msg}")
    with p2:
        t = res0.df_day.index
        figh = go.Figure()
        figh.add_trace(go.Scatter(x=t, y=res0.home_surplus_kw[:, hid], name="Your surplus",
                                  line=dict(color=AMBER, width=1.5), fill="tozeroy",
                                  fillcolor="rgba(217,119,6,0.12)"))
        figh.add_trace(go.Scatter(x=t, y=res0.home_accepted_kw[:, hid], name="Sold via auction",
                                  line=dict(color=GREEN, width=2)))
        figh.update_layout(title=f"H{hid:02d} — your day, kW")
        st.plotly_chart(clean_fig(figh, height=330), width="stretch", key="home_fig")

# ======================================================================= #
# TAB 3 — SWAP STATIONS & FLEETS
# ======================================================================= #
with tabs[2]:
    banner(BLUE, "🔋", "Battery-swap stations & e-taxi depots — the flexible demand",
           "when to charge: follow the solar-window schedule, cut your power bill, and sell "
           "'charged on sunshine' to riders.")

    flex = st.slider("How much of daily charging follows FirmGrid's schedule", 0.0, 1.0, 0.7, 0.1,
                     key="st_flex")
    sres = cached_day(DEMO_DAY, 0.0, False, flex)
    fs = sres.flex_stats

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Charging moved into the sun", f"{fs['shifted_kwh']:.0f} kWh/day")
    s2.metric("Saved on tariffs", f"{fs['station_saving_vnd']:,.0f} ₫/day",
              delta=f"≈ {fs['station_saving_vnd']*365/1e6:.0f}M ₫/yr across the 3 sites")
    s3.metric("CO₂ avoided (charging)", f"{fs['co2_avoided_kg']:.0f} kg/day")
    s4.metric("Per battery swap", "≈ 1 kg CO₂ avoided",
              help="Midday solar charging vs the coal-heavy evening margin — printed on the rider's receipt.")

    t = sres.df_day.index
    figs = go.Figure()
    figs.add_trace(go.Scatter(x=t, y=sres.df_day["surplus_total_kw"], name="Neighbourhood solar surplus",
                              line=dict(color=AMBER, width=1.5), fill="tozeroy",
                              fillcolor="rgba(217,119,6,0.10)"))
    figs.add_trace(go.Scatter(x=t, y=sres.df_day["station_baseline_kw"],
                              name="Your charging — today (uncoordinated, evening)",
                              line=dict(color=RED, width=2, dash="dot")))
    figs.add_trace(go.Scatter(x=t, y=sres.steered_station_kw,
                              name="Your charging — FirmGrid schedule",
                              line=dict(color=BLUE, width=2.5)))
    figs.update_layout(title="Sun-to-Wheels: charging moves under the sunshine curve")
    st.plotly_chart(clean_fig(figs, height=360), width="stretch", key="st_fig")

    st.markdown(
        f"""<div class="fg-receipt">🛵 Rider receipt at 18:40 — <b>“Pin nạp lúc 12:10 —
        98% năng lượng mặt trời · ~0,9 kg CO₂ tránh được”</b> ·
        evening kilometres, morning sunshine.</div>""",
        unsafe_allow_html=True,
    )

# ======================================================================= #
# TAB 4 — DATA CENTRES (Tier 2)
# ======================================================================= #
with tabs[3]:
    banner(GREEN, "🏢", "Data centres & large buyers — mandated ≥50% green by 2030",
           "your DPPA: how much firm, hour-matched clean power to contract, and at what price.")

    b1, b2, b3, b4, b5 = st.columns(5)
    n_tr = b1.slider("Orchestrated transformers", 100, 2000, 800, 100, key="dc_tr")
    dc_mw = b2.slider("Your load (MW)", 5, 50, 20, 5, key="dc_mw")
    storage_mwh = b3.slider("Storage (MWh)", 0, 500, 160, 20, key="dc_smwh")
    storage_mw = b4.slider("Storage power (MW)", 5, 100, 40, 5, key="dc_smw")
    rec = b5.slider("Recovery rate", 0.3, 0.9, 0.7, 0.05, key="dc_rec")

    blk = cached_block(n_tr, float(storage_mwh), float(storage_mw), float(dc_mw), float(rec))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Hourly CFE match", f"{blk['cfe_score']*100:.0f}%",
              help="Share of your load covered by clean energy in the same hour it is consumed — "
                   "the 24/7 standard your green mandate will be audited against.")
    k2.metric("Blended block price", f"${blk['blended_cost_usd_mwh']:.0f}/MWh",
              delta=f"vs grid tariff ${blk['grid_cost_usd_mwh']:.0f}/MWh", delta_color="off")
    k3.metric("Clean energy delivered", f"{blk['clean_gwh']:.1f} GWh/yr")
    k4.metric("CO₂ avoided", f"{blk['co2_avoided_t_per_year']:,.0f} t/yr")

    bh = blk["by_hour"]
    figb = go.Figure()
    figb.add_trace(go.Bar(x=bh.index, y=bh["direct_solar_mw"], name="Direct recovered solar",
                          marker_color=AMBER))
    figb.add_trace(go.Bar(x=bh.index, y=bh["battery_mw"], name="Storage (solar-charged)",
                          marker_color=GREEN))
    figb.add_trace(go.Bar(x=bh.index, y=bh["grid_mw"], name="Residual grid",
                          marker_color="rgba(100,116,139,0.45)"))
    figb.update_layout(barmode="stack", title="Your average day, hour by hour",
                       xaxis_title="hour of day", yaxis_title="MW")
    st.plotly_chart(clean_fig(figb, height=380), width="stretch", key="dc_fig")
    st.caption(
        "Indicative economics: recovered firm solar $60/MWh (IRENA band $54–82), storage cycling "
        "$45/MWh throughput, grid tariff $92/MWh."
    )

# ======================================================================= #
# TAB 5 — CITY & JUDGES
# ======================================================================= #
with tabs[4]:
    banner(RED, "🌏", "Hanoi & policymakers",
           "how much curtailed solar the city recovers — adjust the assumptions to your own figures.")

    a1, a2, a3 = st.columns(3)
    with a1:
        homes = st.slider("PV homes per constrained transformer", 10, 60, 30, key="j_homes")
        kwp = st.slider("Average system size (kWp)", 3.0, 10.0, 5.0, 0.5, key="j_kwp")
    with a2:
        yield_kwh = st.slider("Specific yield (kWh/kWp·yr)", 900, 1300, 1050, 25, key="j_yield")
        curt = st.slider("Share lost to curtailment (%)", 5, 30, 15, key="j_curt") / 100
    with a3:
        recov = st.slider("FirmGrid recovery rate (%)", 40, 90, 70, key="j_rec") / 100
        ntr = st.slider("Constrained transformers (Hanoi)", 100, 3000, 1000, 100, key="j_ntr")

    ef = 0.681  # official 2024 Vietnam grid emission factor, tCO2/MWh
    per_tr_mwh = homes * kwp * yield_kwh * curt / 1000.0
    rec_tr = per_tr_mwh * recov
    city_gwh = rec_tr * ntr / 1000.0
    city_co2 = city_gwh * 1000 * ef / 1000.0
    homes_equiv = int(city_gwh * 1e6 / 2800 / 1000) * 1000

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Stranded per transformer", f"{per_tr_mwh:.1f} MWh/yr")
    i2.metric("Rescued per transformer", f"{rec_tr:.1f} MWh/yr")
    i3.metric("Hanoi rollout", f"{city_gwh:.1f} GWh/yr",
              delta=f"a year's power for ~{homes_equiv:,} homes")
    i4.metric("CO₂ avoided (supply side)", f"{city_co2:,.0f} t/yr")

    st.markdown(
        f"""
**How this is calculated** — {homes} homes × {kwp:.1f} kWp × {yield_kwh} kWh/kWp·yr ×
{curt*100:.0f}% curtailed = **{per_tr_mwh:.1f} MWh/yr** stranded per transformer →
recover {recov*100:.0f}% → × {ntr:,} transformers = **{city_gwh:.1f} GWh/yr ≈
{city_co2:,.0f} t CO₂/yr** (official 2024 grid factor {ef}).

**Mobility:** steering 20–30% of the LEZ's ~100 GWh/yr charging wave into the solar window
avoids a further **16,000–27,000 t CO₂/yr** — like planting a million trees, every year.

**Digital economy:** data-centre demand doubles to ~1,500 MW by 2030 under a ≥50% green
mandate — the Tier-2 buyer for firm blocks (see the Data centres tab).
        """
    )
    st.caption("Aligned with SDG 7 · 9 · 11 · 13.")
