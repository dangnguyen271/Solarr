"""Visual layer: neighbourhood feeder map, transformer gauges, energy Sankey.

Bright, clean palette. Pure plotly figure builders — no Streamlit imports.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from twin import REVERSE_LIMIT_KW

GREEN = "#059669"
BLUE = "#0284c7"
AMBER = "#d97706"
RED = "#dc2626"
GREY = "#94a3b8"
INK = "#0f172a"
MUTED = "#64748b"
PAPER = "rgba(0,0,0,0)"
PLOT_BG = "#ffffff"
GRIDLINE = "rgba(15,23,42,0.07)"


# --------------------------------------------------------------------- #
# static neighbourhood layout (seeded, stable across reruns)
# --------------------------------------------------------------------- #
def node_layout(twin, seed: int = 11):
    rng = np.random.default_rng(seed)
    n = twin.n_households
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rng.shuffle(angles)
    radii = rng.uniform(0.45, 1.0, n)
    xs = radii * np.cos(angles)
    ys = radii * np.sin(angles) * 0.72
    xs[-3:], ys[-3:] = [-1.12, 1.12, 0.02], [0.28, 0.30, -0.82]
    return {
        "homes_xy": (xs, ys),
        "stations_xy": ([-0.72, 0.78], [-0.62, -0.60]),
        "depot_xy": (1.02, -0.42),
        "tx_xy": (0.0, 0.0),
    }


def _clean(fig, height=520, title=None):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=PAPER,
        plot_bgcolor=PLOT_BG,
        height=height,
        margin=dict(l=10, r=10, t=48 if title else 16, b=10),
        title=dict(text=title, font=dict(color=INK, size=15)) if title else None,
        showlegend=True,
        legend=dict(orientation="h", y=-0.02, x=0, font=dict(color=MUTED, size=11)),
        xaxis=dict(visible=False, range=[-1.35, 1.35]),
        yaxis=dict(visible=False, range=[-1.05, 0.95], scaleanchor="x"),
        font=dict(color=INK),
    )
    return fig


def unmanaged_reverse(res, t: int) -> float:
    """Reverse flow if every home exported freely and nobody intervened —
    the stress signal that forces today's blunt feeder-wide cut."""
    df = res.df_day
    return max(
        float(df["surplus_total_kw"].iloc[t]
              - df["grid_load_kw"].iloc[t]
              - df["station_baseline_kw"].iloc[t]),
        0.0,
    )


# --------------------------------------------------------------------- #
# the living neighbourhood map
# --------------------------------------------------------------------- #
def feeder_map(twin, res, t: int, mode: str = "on"):
    """One 15-min window of the demo day as a street map.

    mode: "on" (FirmGrid) or "base" (today's blunt curtailment).
    """
    lay = node_layout(twin)
    xs, ys = lay["homes_xy"]
    surplus = res.home_surplus_kw[t]
    accepted = res.home_accepted_kw[t]
    kwp = np.array([h.kwp for h in twin.households])
    curtailed_now = bool(res.baseline_curtailed[t])

    fig = go.Figure()

    # feeder lines home -> transformer
    lx, ly = [], []
    for x, y in zip(xs, ys):
        lx += [x, 0, None]
        ly += [y, 0, None]
    for pt in [(lay["stations_xy"][0][0], lay["stations_xy"][1][0]),
               (lay["stations_xy"][0][1], lay["stations_xy"][1][1]),
               lay["depot_xy"]]:
        lx += [pt[0], 0, None]
        ly += [pt[1], 0, None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines",
                             line=dict(color="rgba(100,116,139,0.22)", width=1),
                             hoverinfo="skip", showlegend=False))

    # ---- households, coloured by their status THIS window ----
    status_color, status_text, sizes = [], [], []
    for h in range(twin.n_households):
        s, a = float(surplus[h]), float(accepted[h])
        if kwp[h] <= 0:
            status_color.append("rgba(2,132,199,0.30)")
            status_text.append(f"H{h:02d} · consumer")
            sizes.append(9)
            continue
        sizes.append(11 + min(s, 8) * 1.6)
        if s < 0.05:
            status_color.append("rgba(148,163,184,0.75)")
            status_text.append(f"H{h:02d} · {kwp[h]:.1f} kWp · no surplus now")
        elif mode == "base":
            if curtailed_now:
                status_color.append(RED)
                status_text.append(f"H{h:02d} · CURTAILED — {s:.1f} kW wasted (feeder-wide cut)")
            else:
                status_color.append(GREEN)
                status_text.append(f"H{h:02d} · exporting {s:.1f} kW (unmanaged)")
        else:
            if a >= s - 1e-3:
                status_color.append(GREEN)
                status_text.append(f"H{h:02d} · SOLD {a:.1f} kW — paid {a*0.25*700:,.0f} ₫ this window")
            elif a > 1e-3:
                status_color.append(AMBER)
                status_text.append(f"H{h:02d} · partial: {a:.1f} of {s:.1f} kW (headroom binding)")
            else:
                status_color.append(RED)
                status_text.append(f"H{h:02d} · declined this window → priority credit")

    is_ci = np.array([h.kwp >= 12 for h in twin.households])
    for mask, emoji in [(~is_ci, "🏠"), (is_ci, "🏭")]:
        idxs = np.where(mask)[0]
        fig.add_trace(go.Scatter(
            x=xs[idxs], y=ys[idxs], mode="markers+text",
            marker=dict(size=[sizes[i] for i in idxs],
                        color=[status_color[i] for i in idxs],
                        line=dict(color="rgba(15,23,42,0.35)", width=1)),
            text=[emoji] * len(idxs), textposition="top center",
            textfont=dict(size=11),
            hovertext=[status_text[i] for i in idxs], hoverinfo="text",
            showlegend=False))

    # ---- stations & depot: size = charging power this window ----
    station_kw_total = (res.steered_station_kw if mode == "on"
                        else res.df_day["station_baseline_kw"].values)[t]
    share = [0.4, 0.3, 0.3]
    sx, sy = lay["stations_xy"]
    pts = [(sx[0], sy[0], "🔋", "Swap station 1"), (sx[1], sy[1], "🔋", "Swap station 2"),
           (*lay["depot_xy"], "🚕", "e-Taxi depot")]
    for (x, y, emoji, name), sh in zip(pts, share):
        kw = station_kw_total * sh
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text",
            marker=dict(size=16 + kw * 0.5, color=BLUE, symbol="square",
                        line=dict(color="rgba(15,23,42,0.35)", width=1)),
            text=[emoji], textposition="top center", textfont=dict(size=15),
            hovertext=[f"{name} · charging {kw:.1f} kW "
                       f"({'solar-window schedule' if mode=='on' else 'uncoordinated'})"],
            hoverinfo="text", showlegend=False))

    # ---- transformer ----
    if mode == "on":
        reverse = float(res.reverse_fg_kw[t])
        note = ""
    else:
        reverse = float(unmanaged_reverse(res, t))
        note = " — feeder-wide cut triggered!" if curtailed_now else ""
    frac = reverse / REVERSE_LIMIT_KW
    tx_color = GREEN if frac < 0.7 else (AMBER if frac <= 1.0 else RED)
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers+text",
        marker=dict(size=34, color=tx_color, symbol="diamond",
                    line=dict(color=INK, width=2)),
        text=["⚡"], textposition="middle center", textfont=dict(size=16),
        hovertext=[f"400 kVA transformer · reverse flow {reverse:.0f} kW "
                   f"/ limit {REVERSE_LIMIT_KW:.0f} kW ({frac*100:.0f}%){note}"],
        hoverinfo="text", showlegend=False))

    for c, lbl in [(GREEN, "selling / safe"), (AMBER, "partial / near limit"),
                   (RED, "curtailed / declined"), ("rgba(148,163,184,0.75)", "no surplus"),
                   (BLUE, "flexible demand (stations)")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(size=9, color=c), name=lbl))

    label = "With FirmGrid" if mode == "on" else "Today (blunt curtailment)"
    return _clean(fig, title=f"{label} — {res.df_day.index[t]:%H:%M}")


# --------------------------------------------------------------------- #
# transformer gauge
# --------------------------------------------------------------------- #
def tx_gauge(reverse_kw: float, title: str):
    color = GREEN if reverse_kw < 0.7 * REVERSE_LIMIT_KW else (
        AMBER if reverse_kw <= REVERSE_LIMIT_KW else RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=reverse_kw,
        number={"suffix": " kW", "font": {"size": 26, "color": INK}},
        title={"text": title, "font": {"size": 13, "color": MUTED}},
        gauge={
            "axis": {"range": [0, REVERSE_LIMIT_KW * 1.4], "tickcolor": MUTED},
            "bar": {"color": color},
            "bgcolor": "#eef2f7",
            "threshold": {"line": {"color": RED, "width": 3},
                          "thickness": 0.9, "value": REVERSE_LIMIT_KW},
            "steps": [
                {"range": [0, 0.7 * REVERSE_LIMIT_KW], "color": "rgba(5,150,105,0.10)"},
                {"range": [0.7 * REVERSE_LIMIT_KW, REVERSE_LIMIT_KW],
                 "color": "rgba(217,119,6,0.12)"},
                {"range": [REVERSE_LIMIT_KW, REVERSE_LIMIT_KW * 1.4],
                 "color": "rgba(220,38,38,0.12)"},
            ],
        },
    ))
    fig.update_layout(template="plotly_white", paper_bgcolor=PAPER,
                      height=230, margin=dict(l=25, r=25, t=40, b=10),
                      font=dict(color=INK))
    return fig


# --------------------------------------------------------------------- #
# where did the sunshine go? (day-total Sankey)
# --------------------------------------------------------------------- #
def day_sankey(res, mode: str = "on"):
    df = res.df_day
    pv_kwh = df["pv_total_kw"].sum() * 0.25
    surplus_kwh = df["surplus_total_kw"].sum() * 0.25
    self_use = pv_kwh - surplus_kwh

    exported = (res.exported_fg_kw if mode == "on" else res.exported_base_kw)
    station = (res.steered_station_kw if mode == "on"
               else df["station_baseline_kw"].values)
    grid_load = df["grid_load_kw"].values

    to_station = np.minimum(exported, station).sum() * 0.25
    to_homes = np.minimum(np.clip(exported - station, 0, None), grid_load).sum() * 0.25
    to_grid = exported.sum() * 0.25 - to_station - to_homes
    wasted = surplus_kwh - exported.sum() * 0.25

    labels = ["☀️ Rooftop solar", "🏠 Self-consumed", "✅ Sold / exported",
              "🗑 Curtailed (wasted)", "🔋 Swap stations & depot",
              "🏘 Neighbourhood homes", "🔌 Upstream grid"]
    node_colors = [AMBER, GREEN, BLUE, RED, BLUE, GREEN, GREY]
    src = [0, 0, 0, 2, 2, 2]
    dst = [1, 2, 3, 4, 5, 6]
    val = [self_use, exported.sum() * 0.25, wasted, to_station, to_homes, max(to_grid, 0)]
    link_colors = ["rgba(5,150,105,0.25)", "rgba(2,132,199,0.25)",
                   "rgba(220,38,38,0.30)", "rgba(2,132,199,0.25)",
                   "rgba(5,150,105,0.25)", "rgba(100,116,139,0.22)"]

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=labels, pad=18, thickness=16,
                  color=node_colors, line=dict(width=0)),
        link=dict(source=src, target=dst, value=[max(v, 0.01) for v in val],
                  color=link_colors,
                  hovertemplate="%{value:.0f} kWh<extra></extra>"),
    ))
    title = ("Where the day's sunshine went — with FirmGrid"
             if mode == "on" else "Where the day's sunshine went — today")
    fig.update_layout(template="plotly_white", paper_bgcolor=PAPER,
                      height=380, margin=dict(l=10, r=10, t=48, b=10),
                      title=dict(text=title, font=dict(size=15, color=INK)),
                      font=dict(color=INK, size=13))
    return fig
