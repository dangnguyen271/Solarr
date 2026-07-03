"""Firm Block Studio — Tier 2, Sun-to-Servers.

The same orchestration engine, aggregated up: N FirmGrid-orchestrated
transformers + shared battery storage are shaped into a firm, hour-matched
24/7 clean-power block for a data centre buying through a DPPA.

For each hour of a representative year we compute how much of the data
centre's flat load is covered by (a) direct recovered solar, (b) battery
discharge charged from that solar, and (c) residual grid power — giving an
hourly CFE (carbon-free energy) matching score and a blended cost, the two
numbers a DPPA negotiation actually runs on.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GRID_TARIFF_USD = 92.0          # USD/MWh — indicative industrial tariff
FIRM_SOLAR_LCOE_USD = 60.0      # USD/MWh — recovered solar via platform (IRENA band)
STORAGE_CYCLE_COST_USD = 45.0   # USD/MWh throughput — battery amortisation
GRID_EF = 0.681                 # tCO2/MWh, official 2024 Vietnam grid factor
ROUNDTRIP_EFF = 0.88


def build_firm_block(
    df: pd.DataFrame,
    n_transformers: int = 200,
    storage_mwh: float = 40.0,
    storage_mw: float = 10.0,
    dc_load_mw: float = 20.0,
    recovery_rate: float = 0.7,
):
    """Simulate one year of hourly 24/7 CFE matching for a data-centre block.

    df: the single-feeder twin year (15-min). The feeder's orchestrated,
    recovered surplus is scaled to n_transformers as the clean supply pool.
    """
    hourly = df.resample("1h").mean(numeric_only=True)

    # clean supply available to the block, MW
    supply_mw = hourly["surplus_total_kw"].values / 1000.0 * n_transformers * recovery_rate
    load_mw = np.full(len(hourly), dc_load_mw)

    soc = storage_mwh * 0.5
    direct = np.zeros(len(hourly))
    discharged = np.zeros(len(hourly))
    charged = np.zeros(len(hourly))
    grid = np.zeros(len(hourly))

    for t in range(len(hourly)):
        d = min(supply_mw[t], load_mw[t])
        direct[t] = d
        leftover = supply_mw[t] - d
        # charge with leftover clean energy
        c = min(leftover, storage_mw, (storage_mwh - soc) / 1.0)
        charged[t] = c
        soc += c * np.sqrt(ROUNDTRIP_EFF)
        # discharge to cover the gap
        gap = load_mw[t] - d
        dis = min(gap, storage_mw, soc)
        discharged[t] = dis * np.sqrt(ROUNDTRIP_EFF)
        soc -= dis
        grid[t] = max(load_mw[t] - direct[t] - discharged[t], 0.0)

    clean = direct + discharged
    total = load_mw.sum()
    cfe_hourly = clean / load_mw
    cfe_score = float(clean.sum() / total)

    blended_cost = float(
        (
            direct.sum() * FIRM_SOLAR_LCOE_USD
            + discharged.sum() * (FIRM_SOLAR_LCOE_USD + STORAGE_CYCLE_COST_USD)
            + grid.sum() * GRID_TARIFF_USD
        )
        / total
    )
    co2_avoided_t = float(clean.sum() * GRID_EF)

    profile = pd.DataFrame(
        {
            "direct_solar_mw": direct,
            "battery_mw": discharged,
            "grid_mw": grid,
            "cfe": cfe_hourly,
            "hour": hourly.index.hour,
        },
        index=hourly.index,
    )
    by_hour = profile.groupby("hour")[["direct_solar_mw", "battery_mw", "grid_mw"]].mean()

    return {
        "cfe_score": cfe_score,
        "blended_cost_usd_mwh": blended_cost,
        "grid_cost_usd_mwh": GRID_TARIFF_USD,
        "co2_avoided_t_per_year": co2_avoided_t,
        "clean_gwh": float(clean.sum() / 1000.0),
        "by_hour": by_hour,
        "profile": profile,
    }
