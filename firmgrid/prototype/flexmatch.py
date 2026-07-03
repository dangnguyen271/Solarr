"""FlexMatch — Sun-to-Wheels demand steering.

Moves battery-swap-station and e-taxi-depot charging out of the coal-heavy
evening peak into the 10:00-14:00 solar window, subject to each station's
daily energy requirement and power cap. Steered charging is extra local
absorption: it directly raises export headroom for households AND fills
evening-swapped batteries with midday sunshine.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from twin import SOLAR_WINDOW, STEPS_PER_DAY

EVENING_TARIFF_VND = 3100.0     # peak business tariff, VND/kWh (order of magnitude)
SOLAR_TARIFF_VND = 2400.0       # off-peak/solar-window effective tariff
EVENING_EF = 0.85               # kg CO2/kWh, marginal evening (coal-heavy) factor
SOLAR_EF = 0.05                 # kg CO2/kWh charged on verified local surplus


def steer_stations(df_day: pd.DataFrame, stations, shift_share: float = 0.7):
    """Return (steered_profile_kw, baseline_profile_kw, stats) for one day.

    shift_share: fraction of each station's daily energy moved into the
    solar window (the rest keeps its baseline shape, scaled down).
    """
    hours = df_day["hour"].values
    baseline = df_day["station_baseline_kw"].values
    in_window = (hours >= SOLAR_WINDOW[0]) & (hours < SOLAR_WINDOW[1])
    window_steps = int(in_window.sum())

    total_daily_kwh = baseline.sum() * 0.25
    shifted_kwh = total_daily_kwh * shift_share
    max_power = sum(s.max_power_kw for s in stations)

    # weight steered charging by available surplus inside the window
    surplus_w = np.where(in_window, df_day["surplus_total_kw"].values, 0.0)
    if surplus_w.sum() > 0:
        w = surplus_w / surplus_w.sum()
    else:
        w = in_window.astype(float) / max(window_steps, 1)

    steered = baseline * (1.0 - shift_share) + w * shifted_kwh / 0.25
    steered = np.minimum(steered, max_power)

    stats = {
        "shifted_kwh": float(shifted_kwh),
        "station_saving_vnd": float(shifted_kwh * (EVENING_TARIFF_VND - SOLAR_TARIFF_VND)),
        "co2_avoided_kg": float(shifted_kwh * (EVENING_EF - SOLAR_EF)),
        "extra_absorption_kw": steered - baseline,   # per-step delta (can be negative in evening)
    }
    return steered, baseline, stats
