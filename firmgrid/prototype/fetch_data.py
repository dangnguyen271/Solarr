"""Fetch REAL Hanoi weather for the twin — run once, cache forever.

Downloads hourly shortwave radiation (GHI), temperature and cloud cover for
Hanoi from the Open-Meteo historical archive (ERA5/satellite reanalysis) for
the 12 months ending 30 June 2026, upsamples to 15 minutes, and stores
data/hanoi_weather.csv. The demo itself never touches the network — it reads
this file. Delete the file to fall back to the synthetic weather model.

Run:  python fetch_data.py
"""

import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

LAT, LON = 21.0285, 105.8542          # Hoan Kiem, Hanoi
START, END = "2025-07-01", "2026-06-30"  # the 12 real months before the hackathon
OUT = Path(__file__).resolve().parent / "data" / "hanoi_weather.csv"

URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LAT}&longitude={LON}&start_date={START}&end_date={END}"
    "&hourly=shortwave_radiation,temperature_2m,cloud_cover"
    "&timezone=Asia%2FBangkok"
)


def main():
    print(f"[fetch] {URL}")
    with urllib.request.urlopen(URL, timeout=120) as r:
        payload = json.load(r)

    h = payload["hourly"]
    df = pd.DataFrame(
        {
            "ghi_wm2": h["shortwave_radiation"],
            "temp_c": h["temperature_2m"],
            "cloud_pct": h["cloud_cover"],
        },
        index=pd.to_datetime(h["time"]),
    ).astype(float)

    # hourly -> 15-min: interpolate irradiance/temperature smoothly
    idx15 = pd.date_range(df.index[0], df.index[-1] + pd.Timedelta(minutes=45), freq="15min")
    df15 = df.reindex(df.index.union(idx15)).interpolate(method="time").reindex(idx15)
    df15["ghi_wm2"] = df15["ghi_wm2"].clip(lower=0)

    OUT.parent.mkdir(exist_ok=True)
    df15.to_csv(OUT, index_label="time")
    days = len(np.unique(idx15.date))
    print(f"[saved] {OUT}  ({len(df15):,} rows, {days} days, "
          f"GHI max {df15['ghi_wm2'].max():.0f} W/m², "
          f"mean daytime {df15.loc[df15['ghi_wm2'] > 0, 'ghi_wm2'].mean():.0f} W/m²)")


if __name__ == "__main__":
    main()
