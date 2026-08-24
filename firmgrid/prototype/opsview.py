"""GridMind Ops — operations-console visuals (dark).

The intelligence layer's own screen: a live energy-routing network, the
probabilistic forecast the allocator plans on, the per-window order book,
and the settlement event feed. Pure figure/data builders — no Streamlit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from mapview import node_layout
from twin import REVERSE_LIMIT_KW

# console palette
BG = "#0a0f1c"
PANEL = "#0e1526"
GRID = "rgba(148,163,184,0.10)"
INK = "#dbe4f0"
MUTED = "#5b6b82"
AMBER = "#f5b83d"      # solar export
CYAN = "#39c5cf"       # forecast / intelligence
BLUE = "#3d9df5"       # station charging
TEAL = "#2fd6a3"       # local absorption / ok
RED = "#f0564f"        # risk / declined
SLATE = "#31405c"


def _dark(fig, height=520, title=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=PANEL,
        height=height,
        margin=dict(l=10, r=10, t=44 if title else 12, b=10),
        title=dict(text=title, font=dict(color=INK, size=14, family="Menlo, monospace")) if title else None,
        font=dict(color=INK, size=12),
        legend=dict(orientation="h", y=-0.04, x=0, font=dict(color=MUTED, size=10.5)),
    )
    return fig


# --------------------------------------------------------------------- #
# per-window energy routing (who feeds whom, in kW)
# --------------------------------------------------------------------- #
def window_flows(twin, res, t: int) -> dict:
    """Physical routing for one 15-min window, all in kW."""
    exported_home = res.home_accepted_kw[t]                 # per home
    total_exported = float(exported_home.sum())
    station_kw = float(res.steered_station_kw[t])
    absorbed_station = min(total_exported, station_kw)
    grid_load = float(res.df_day["grid_load_kw"].iloc[t])
    absorbed_local = min(max(total_exported - absorbed_station, 0.0), grid_load)
    to_upstream = max(total_exported - absorbed_station - absorbed_local, 0.0)
    headroom = REVERSE_LIMIT_KW + grid_load + station_kw
    return {
        "exported_home": exported_home,
        "total_exported": total_exported,
        "absorbed_station": absorbed_station,
        "absorbed_local": absorbed_local,
        "to_upstream": to_upstream,
        "headroom": headroom,
        "utilisation": total_exported / max(0.9 * headroom, 1e-6),
        "reverse": float(res.reverse_fg_kw[t]),
    }


def flow_network(twin, res, t: int):
    """The routing map: every kW from roof → transformer → station/home/grid."""
    lay = node_layout(twin)
    xs, ys = lay["homes_xy"]
    fl = window_flows(twin, res, t)
    exported = fl["exported_home"]
    surplus = res.home_surplus_kw[t]
    kwp = np.array([h.kwp for h in twin.households])
    # actual per-home load this window (align by timestamp within the stored year)
    mask = twin.index.get_indexer([res.df_day.index[t]])
    loads_now = twin.per_home_load[mask[0]] if mask[0] >= 0 else np.zeros(twin.n_households)

    GRID_XY = (0.0, 0.86)
    fig = go.Figure()

    def edge(x0, y0, x1, y1, kw, color, name=None, dash=None):
        if kw <= 0.05:
            return
        fig.add_trace(go.Scatter(
            x=[x0, (x0 + x1) / 2, x1], y=[y0, (y0 + y1) / 2 + 0.03, y1],
            mode="lines",
            line=dict(color=color, width=min(1.0 + kw * 0.55, 9), shape="spline",
                      dash=dash),
            opacity=0.75, hoverinfo="text",
            hovertext=f"{name or 'flow'} · {kw:.1f} kW", showlegend=False))

    # 1 · faint feeder skeleton
    lx, ly = [], []
    for x, y in zip(xs, ys):
        lx += [x, 0, None]; ly += [y, 0, None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines",
                             line=dict(color="rgba(90,105,130,0.14)", width=0.7),
                             hoverinfo="skip", showlegend=False))

    # 2 · export flows: home → TX (amber, width = kW sold this window)
    for h in range(twin.n_households):
        edge(xs[h], ys[h], 0, 0, float(exported[h]), AMBER,
             name=f"H{h:02d} export")

    # 3 · absorption flows out of TX
    sx, sy = lay["stations_xy"]
    st_pts = [(sx[0], sy[0]), (sx[1], sy[1]), lay["depot_xy"]]
    for (x, y), share in zip(st_pts, (0.4, 0.3, 0.3)):
        edge(0, 0, x, y, fl["absorbed_station"] * share, BLUE, name="station charging")
    # local absorption: spread over consumer homes weighted by their current load
    non_pv = np.where(kwp <= 0)[0]
    w = loads_now[non_pv]; w = w / w.sum() if w.sum() > 0 else np.ones(len(non_pv)) / len(non_pv)
    for i, h in enumerate(non_pv):
        edge(0, 0, xs[h], ys[h], fl["absorbed_local"] * float(w[i]), TEAL,
             name=f"H{h:02d} local supply")
    # upstream grid
    edge(0, 0, *GRID_XY, fl["to_upstream"], "#93a6c4", name="to upstream grid", dash=None)

    # 4 · nodes
    is_ci = kwp >= 12
    colors, sizes, hover = [], [], []
    for h in range(twin.n_households):
        s, a = float(surplus[h]), float(exported[h])
        if kwp[h] <= 0:
            colors.append("rgba(47,214,163,0.45)"); sizes.append(7)
            hover.append(f"H{h:02d} · consumer · drawing {loads_now[h]:.1f} kW")
        elif a > 0.05:
            colors.append(AMBER); sizes.append(9 + min(a, 7) * 1.7)
            hover.append(f"H{h:02d} · {kwp[h]:.1f} kWp · selling {a:.1f} kW")
        elif s > 0.05:
            colors.append(RED); sizes.append(9)
            hover.append(f"H{h:02d} · {kwp[h]:.1f} kWp · declined ({s:.1f} kW held)")
        else:
            colors.append(SLATE); sizes.append(6)
            hover.append(f"H{h:02d} · {kwp[h]:.1f} kWp · no surplus")
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=sizes, color=colors, symbol=np.where(is_ci, "diamond", "circle"),
                    line=dict(color="rgba(219,228,240,0.35)", width=0.8)),
        hovertext=hover, hoverinfo="text", showlegend=False))

    # stations
    st_kw_total = float(res.steered_station_kw[t])
    for (x, y), share, nm in zip(st_pts, (0.4, 0.3, 0.3),
                                 ("SWAP-1", "SWAP-2", "DEPOT-1")):
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text",
            marker=dict(size=15 + st_kw_total * share * 0.45, color=BLUE, symbol="square",
                        line=dict(color="rgba(219,228,240,0.4)", width=1)),
            text=[nm], textposition="bottom center",
            textfont=dict(size=9, color=MUTED, family="Menlo, monospace"),
            hovertext=[f"{nm} · charging {st_kw_total*share:.1f} kW"],
            hoverinfo="text", showlegend=False))

    # transformer + upstream grid
    util = fl["reverse"] / REVERSE_LIMIT_KW
    tx_color = TEAL if util < 0.7 else (AMBER if util <= 1 else RED)
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers+text",
        marker=dict(size=30, color=tx_color, symbol="diamond",
                    line=dict(color=INK, width=1.6)),
        text=["TX-0421"], textposition="bottom center",
        textfont=dict(size=10, color=INK, family="Menlo, monospace"),
        hovertext=[f"TX-A-0421 · reverse {fl['reverse']:.0f}/{REVERSE_LIMIT_KW:.0f} kW"],
        hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[GRID_XY[0]], y=[GRID_XY[1]], mode="markers+text",
        marker=dict(size=17, color="#93a6c4", symbol="triangle-up",
                    line=dict(color=INK, width=1)),
        text=["UPSTREAM 22kV"], textposition="top center",
        textfont=dict(size=9, color=MUTED, family="Menlo, monospace"),
        hovertext=[f"export to upstream grid · {fl['to_upstream']:.1f} kW"],
        hoverinfo="text", showlegend=False))

    # legend proxies
    for c, lbl in [(AMBER, "rooftop export"), (BLUE, "station charging"),
                   (TEAL, "local absorption"), ("#93a6c4", "to upstream grid"),
                   (RED, "held (no headroom)")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines",
                                 line=dict(color=c, width=3), name=lbl))

    fig.update_layout(xaxis=dict(visible=False, range=[-1.35, 1.35]),
                      yaxis=dict(visible=False, range=[-1.05, 1.02], scaleanchor="x"),
                      showlegend=True)
    ts = res.df_day.index[t]
    return _dark(fig, height=560,
                 title=f"ENERGY ROUTING · {ts:%H:%M}–{(ts + pd.Timedelta(minutes=15)):%H:%M} · "
                       f"{fl['total_exported']:.0f} kW routed")


# --------------------------------------------------------------------- #
# forecast intelligence panel
# --------------------------------------------------------------------- #
def forecast_panel(fc: pd.DataFrame, mae: float, t: int):
    """Forecast vs actual with a P10–P90 band + breach-probability strip."""
    x = [ts.isoformat() for ts in fc.index]   # plain strings: render- and export-safe
    f = fc["surplus_forecast_kw"].values
    a = fc["surplus_actual_kw"].values
    band = 1.28 * mae
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.74, 0.26], vertical_spacing=0.06)
    fig.add_trace(go.Scatter(x=x, y=np.clip(f + band, 0, None), line=dict(width=0),
                             hoverinfo="skip", showlegend=False), 1, 1)
    fig.add_trace(go.Scatter(x=x, y=np.clip(f - band, 0, None), fill="tonexty",
                             fillcolor="rgba(57,197,207,0.14)", line=dict(width=0),
                             name="P10–P90 band"), 1, 1)
    fig.add_trace(go.Scatter(x=x, y=f, name="forecast surplus",
                             line=dict(color=CYAN, width=2)), 1, 1)
    fig.add_trace(go.Scatter(x=x, y=a, name="actual",
                             line=dict(color=INK, width=1.2, dash="dot")), 1, 1)
    fig.add_vline(x=x[t], line_color=AMBER, line_width=1.2, line_dash="dash")

    p = fc["p_breach_1h"].values
    fig.add_trace(go.Bar(x=x, y=p, marker=dict(
        color=p, colorscale=[[0, "#123028"], [0.5, "#7a5b16"], [1, "#7a1f1b"]],
        cmin=0, cmax=1, line_width=0), name="P(overload ≤ 1 h)"), 2, 1)
    fig.add_hline(y=0.5, line_color=RED, line_width=1, line_dash="dot", row=2, col=1)

    fig.update_yaxes(title_text="kW", gridcolor=GRID, row=1, col=1,
                     title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(range=[0, 1], gridcolor=GRID, row=2, col=1,
                     tickvals=[0, 0.5, 1], title_text="risk",
                     title_font=dict(size=10, color=MUTED))
    fig.update_xaxes(gridcolor=GRID)
    return _dark(fig, height=330, title="GRIDMIND FORECAST · feeder surplus + overload risk")


# --------------------------------------------------------------------- #
# order book + settlement feed (data builders)
# --------------------------------------------------------------------- #
def order_book(twin, res, t: int, top: int = 12) -> tuple[list, int]:
    """Rows for the current window's clearing, largest offers first."""
    rows = []
    for h in range(twin.n_households):
        cap = float(res.home_surplus_kw[t][h])
        if cap <= 0.05:
            continue
        acc = float(res.home_accepted_kw[t][h])
        fill = acc / cap if cap else 0
        status = ("FILLED" if fill > 0.98 else
                  "PARTIAL" if acc > 0.05 else "DECLINED")
        rows.append({"id": f"H{h:02d}", "kwp": twin.households[h].kwp,
                     "offer": cap, "cleared": acc, "fill": fill, "status": status})
    rows.sort(key=lambda r: -r["offer"])
    return rows[:top], max(0, len(rows) - top)


def ledger_feed(res, t: int, n: int = 9) -> list:
    """Last n settlement events at or before the selected window."""
    cutoff = res.df_day.index[t].isoformat()
    out = []
    for b in res.ledger.blocks:
        bt = b["payload"].get("t", "")
        if b["type"] == "window_cleared" and bt and bt > cutoff:
            continue
        out.append(b)
    lines = []
    for b in out[-n:]:
        p = b["payload"]
        if b["type"] == "window_cleared":
            ts = pd.Timestamp(p["t"]).strftime("%H:%M")
            msg = f"CLEAR  {p['accepted_kw']:>6.1f} kW accepted · headroom {p['headroom_kw']:.0f} kW"
        elif b["type"] == "fraud_blocked":
            ts = "--:--"
            msg = f"BLOCK  H{p['hid']:02d} bid {p['bid_kw']:.1f} kW > cap {p['cap_kw']:.1f} kW"
        else:
            ts = "--:--"
            msg = f"SEAL   day settled · {p.get('vnd_paid', 0):,} VND"
        lines.append({"hash": b["hash"][:10], "ts": ts, "msg": msg, "type": b["type"]})
    return lines
