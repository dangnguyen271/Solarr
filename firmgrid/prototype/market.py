"""One full market day on the feeder — baseline vs FirmGrid ON.

Baseline (today's reality): when reverse flow breaches the transformer
limit, the operator cuts ALL export on the feeder for that window
(blunt, blind curtailment). FirmGrid ON: GridMind forecasts headroom,
FlexMatch steers station charging into the solar window, the HeadRoom
auction accepts the maximum safe export, Sentinel screens bids, and
every event lands in the TrustLedger.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from auction import BASE_PRICE_VND, SAFETY_MARGIN, AuctionEngine, Bid
from flexmatch import steer_stations
from gridmind import GridMind
from ledger import Sentinel, TrustLedger
from twin import REVERSE_LIMIT_KW, FeederTwin

EVENING_EF = 0.85   # kg CO2/kWh displaced when surplus offsets evening fossil burn


@dataclass
class DayResult:
    df_day: pd.DataFrame
    baseline_exported_kwh: float
    baseline_wasted_kwh: float
    baseline_breaches: int
    fg_exported_kwh: float
    fg_wasted_kwh: float
    fg_breaches: int
    recovered_kwh: float
    co2_avoided_kg: float
    vnd_paid: float
    fairness_max_wait: int
    flex_stats: dict
    reverse_baseline_kw: np.ndarray
    reverse_fg_kw: np.ndarray
    steered_station_kw: np.ndarray
    allocations_log: list
    ledger: TrustLedger
    fraud_events: list
    # per-home, per-window detail for the neighbourhood map (steps, H)
    home_surplus_kw: np.ndarray = None
    home_accepted_kw: np.ndarray = None
    baseline_curtailed: np.ndarray = None   # bool (steps,): feeder-wide cut active
    exported_fg_kw: np.ndarray = None       # (steps,)
    exported_base_kw: np.ndarray = None     # (steps,)


def run_day(
    twin: FeederTwin,
    df: pd.DataFrame,
    mind: GridMind,
    date: str,
    cloud_dim: float = 0.0,
    fraud_bid: dict | None = None,
    flex_share: float = 0.7,
) -> DayResult:
    """Simulate one day both ways.

    cloud_dim: 0..1 — judge-dragged storm front, scales down irradiance/surplus.
    fraud_bid: e.g. {"hid": 3, "kw": 8.0} — injected inflated bid for Sentinel.
    """
    df_day = df.loc[date].copy()
    home_surplus = twin.home_surplus_on(date).copy()          # (96, H) kW

    if cloud_dim > 0:
        dim = 1.0 - cloud_dim
        for col in ("surplus_total_kw", "pv_total_kw", "irradiance"):
            df_day[col] = df_day[col] * dim
        home_surplus *= dim
        df_day["net_kw"] = (
            df_day["grid_load_kw"] + df_day["station_baseline_kw"] - df_day["surplus_total_kw"]
        )
        df_day["reverse_kw"] = np.clip(-df_day["net_kw"], 0, None)

    steps = len(df_day)
    surplus = df_day["surplus_total_kw"].values

    # ------------------------------------------------------------------ #
    # BASELINE: blunt feeder-wide curtailment
    # ------------------------------------------------------------------ #
    headroom_base = twin.headroom_kw(df_day, 0.0)
    breach_base = surplus > headroom_base
    exported_base = np.where(breach_base, 0.0, surplus)       # whole feeder cut
    wasted_base = surplus - exported_base
    reverse_base = np.clip(
        exported_base - df_day["grid_load_kw"].values - df_day["station_baseline_kw"].values,
        0,
        None,
    )

    # ------------------------------------------------------------------ #
    # FIRMGRID ON
    # ------------------------------------------------------------------ #
    steered, baseline_station, flex_stats = steer_stations(
        df_day, twin.stations, shift_share=flex_share
    )
    extra_absorption = steered - baseline_station
    headroom_fg = twin.headroom_kw(df_day, extra_absorption)

    forecast = mind.predict_day(df, date)
    if cloud_dim > 0:
        forecast["surplus_forecast_kw"] *= 1.0 - cloud_dim

    engine = AuctionEngine(n_households=twin.n_households)
    ledger = TrustLedger()
    sentinel = Sentinel(ledger)
    fraud_events: list[str] = []
    allocations_log: list[dict] = []

    exported_fg = np.zeros(steps)
    home_accepted = np.zeros((steps, twin.n_households))
    vnd_paid = 0.0

    for t in range(steps):
        # Auto-Sell agents bid each home's physical surplus (the twin stands in
        # for the per-home nowcast); Sentinel enforces the same physical cap.
        # GridMind's forecast steers headroom planning and the breach warnings.
        bids = []
        for hid in range(twin.n_households):
            kw = float(home_surplus[t][hid])
            if kw <= 1e-3:
                continue
            bids.append(Bid(hid=hid, kw=kw, cap_kw=kw))

        # judge-injected fraudulent bid, screened by Sentinel before auction
        if fraud_bid and t == steps // 2:
            ok, msg = sentinel.screen_bid(
                fraud_bid["hid"], fraud_bid["kw"], float(home_surplus[t][fraud_bid["hid"]])
            )
            if not ok:
                fraud_events.append(msg)

        allocs = engine.clear_window(bids, float(headroom_fg[t]))
        window_kw = 0.0
        for a in allocs:
            window_kw += a.accepted_kw
            home_accepted[t, a.hid] = a.accepted_kw
            if a.accepted_kw > 0:
                kwh = a.accepted_kw * 0.25
                vnd_paid += kwh * BASE_PRICE_VND
        exported_fg[t] = min(window_kw, surplus[t])

        if t % 8 == 0 and bids:                       # log every 2h for the UI
            allocations_log.append(
                {
                    "time": df_day.index[t].strftime("%H:%M"),
                    "bids": len(bids),
                    "accepted_kw": round(window_kw, 1),
                    "headroom_kw": round(float(headroom_fg[t]), 1),
                    "example": allocs[0].reason if allocs else "",
                }
            )
        if bids:
            ledger.append(
                "window_cleared",
                {
                    "t": df_day.index[t].isoformat(),
                    "accepted_kw": round(window_kw, 2),
                    "headroom_kw": round(float(headroom_fg[t]), 2),
                },
            )

    wasted_fg = np.clip(surplus - exported_fg, 0, None)
    reverse_fg = np.clip(
        exported_fg - df_day["grid_load_kw"].values - steered, 0, None
    )
    breaches_fg = int((reverse_fg > REVERSE_LIMIT_KW + 1e-6).sum())

    recovered_kwh = float((wasted_base.sum() - wasted_fg.sum()) * 0.25)
    co2 = recovered_kwh * EVENING_EF + flex_stats["co2_avoided_kg"]

    ledger.append("settlement_sealed", {"date": date, "vnd_paid": round(vnd_paid)})

    return DayResult(
        df_day=df_day,
        baseline_exported_kwh=float(exported_base.sum() * 0.25),
        baseline_wasted_kwh=float(wasted_base.sum() * 0.25),
        baseline_breaches=int(breach_base.sum()),
        fg_exported_kwh=float(exported_fg.sum() * 0.25),
        fg_wasted_kwh=float(wasted_fg.sum() * 0.25),
        fg_breaches=breaches_fg,
        recovered_kwh=recovered_kwh,
        co2_avoided_kg=float(co2),
        vnd_paid=float(vnd_paid),
        fairness_max_wait=engine.max_consecutive_rejects,
        flex_stats=flex_stats,
        reverse_baseline_kw=reverse_base,
        reverse_fg_kw=reverse_fg,
        steered_station_kw=steered,
        allocations_log=allocations_log,
        ledger=ledger,
        fraud_events=fraud_events,
        home_surplus_kw=home_surplus,
        home_accepted_kw=home_accepted,
        baseline_curtailed=breach_base,
        exported_fg_kw=exported_fg,
        exported_base_kw=exported_base,
    )
