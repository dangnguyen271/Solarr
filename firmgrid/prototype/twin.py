"""Digital twin of one Hanoi distribution feeder.

One 400 kVA transformer, 55 households (30 with rooftop PV) + 3 C&I rooftops,
two e-motorbike battery-swap stations and one e-taxi depot, simulated for a
full year at 15-minute resolution.

Weather: REAL Hanoi data (Open-Meteo archive, Jul 2025 – Jun 2026 — the 12
months ending days before the hackathon), cached in data/hanoi_weather.csv by
fetch_data.py so the demo runs fully offline. If the cache is missing, a
seeded synthetic Hanoi-climatology model is used instead. Household loads and
station behaviour are synthetic-but-calibrated models in both cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

WEATHER_CSV = Path(__file__).resolve().parent / "data" / "hanoi_weather.csv"

STEPS_PER_DAY = 96          # 15-minute resolution
DAYS = 365
KVA_RATING = 400.0          # transformer nameplate
# Safe reverse-flow limit is far below nameplate on long LV feeders —
# voltage rise, not thermal rating, binds first (typ. 30-50% of kVA).
REVERSE_LIMIT_KW = 0.30 * KVA_RATING
SOLAR_WINDOW = (10.0, 14.0)  # hours; when FlexMatch wants stations charging

# Hanoi-like monthly clearness (monsoon summers, hazy winters)
MONTHLY_CLEARNESS = np.array(
    [0.42, 0.44, 0.48, 0.55, 0.62, 0.60, 0.58, 0.57, 0.55, 0.52, 0.48, 0.44]
)
MONTHLY_DAYLENGTH_H = np.array(
    [10.9, 11.4, 12.0, 12.7, 13.2, 13.5, 13.4, 12.9, 12.2, 11.6, 11.0, 10.7]
)


@dataclass
class Household:
    hid: int
    kwp: float          # 0 for non-PV homes
    base_load_kw: float


@dataclass
class Station:
    sid: str
    daily_energy_kwh: float   # energy it must charge every day
    max_power_kw: float
    kind: str = "swap"        # swap | depot


@dataclass
class FeederTwin:
    seed: int = 42
    n_households: int = 55
    n_pv: int = 30
    households: list = field(default_factory=list)
    stations: list = field(default_factory=list)

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        self.households = [
            Household(
                hid=i,
                kwp=float(rng.uniform(4.0, 10.0)) if i < self.n_pv else 0.0,
                base_load_kw=float(rng.uniform(0.25, 0.6)),
            )
            for i in range(self.n_households)
        ]
        # three C&I rooftops (shop / school / mini-factory) on the same feeder
        for j, kwp in enumerate(rng.uniform(15.0, 30.0, 3)):
            self.households.append(
                Household(
                    hid=self.n_households + j,
                    kwp=float(kwp),
                    base_load_kw=float(rng.uniform(2.0, 3.5)),
                )
            )
        self.n_households = len(self.households)
        self.n_pv += 3
        self.stations = [
            Station("SwapStation-1", daily_energy_kwh=140.0, max_power_kw=25.0),
            Station("SwapStation-2", daily_energy_kwh=110.0, max_power_kw=20.0),
            Station("eTaxiDepot-1", daily_energy_kwh=180.0, max_power_kw=40.0, kind="depot"),
        ]
        self.rng = rng

    # ------------------------------------------------------------------ #
    # Weather / irradiance
    # ------------------------------------------------------------------ #
    def _daily_clearness(self) -> np.ndarray:
        """One clearness index per day: monthly mean + AR(1) weather noise."""
        month_of_day = pd.date_range("2026-01-01", periods=DAYS, freq="D").month - 1
        base = MONTHLY_CLEARNESS[month_of_day]
        noise = np.zeros(DAYS)
        for d in range(1, DAYS):
            noise[d] = 0.6 * noise[d - 1] + self.rng.normal(0, 0.10)
        return np.clip(base + noise, 0.05, 0.95)

    def simulate_year(self) -> pd.DataFrame:
        """Return a tidy frame indexed by timestamp with per-feeder series (kW)."""
        idx = pd.date_range("2026-01-01", periods=DAYS * STEPS_PER_DAY, freq="15min")
        hours = (idx.hour + idx.minute / 60.0).values
        month = idx.month.values - 1
        dow = idx.dayofweek.values
        day_of_year = idx.dayofyear.values - 1

        clearness_d = self._daily_clearness()
        clearness = clearness_d[day_of_year]

        # --- irradiance shape: half-sine over daylight, per-step cloud flicker
        daylen = MONTHLY_DAYLENGTH_H[month]
        sunrise = 12.0 - daylen / 2.0
        solar_pos = np.clip((hours - sunrise) / daylen, 0.0, 1.0)
        shape = np.sin(np.pi * solar_pos) ** 1.3
        flicker = np.clip(self.rng.normal(1.0, 0.08, len(idx)), 0.6, 1.15)
        irradiance = shape * clearness * flicker          # 0..1 plane-of-array proxy

        # --- PV generation per home (kW): kWp * irradiance * performance ratio
        pv_kwp = np.array([h.kwp for h in self.households])
        pv_total = irradiance[:, None] * pv_kwp[None, :] * 0.82   # (T, H)

        # --- household consumption (kW): morning bump + evening peak, weekend lift
        base = np.array([h.base_load_kw for h in self.households])
        morning = 0.7 * np.exp(-0.5 * ((hours - 6.5) / 1.2) ** 2)
        evening = 1.8 * np.exp(-0.5 * ((hours - 19.5) / 1.8) ** 2)
        midday_weekend = np.where(dow >= 5, 0.5 * np.exp(-0.5 * ((hours - 12.0) / 2.5) ** 2), 0.0)
        # summer AC load scales with month
        ac = np.isin(month, [4, 5, 6, 7]) * 0.35
        profile = 0.35 + morning + evening + midday_weekend + ac
        noise_h = np.clip(self.rng.normal(1.0, 0.15, (len(idx), len(base))), 0.4, 1.8)
        load = profile[:, None] * base[None, :] * 2.2 * noise_h   # (T, H)

        # --- surplus per PV home (kW), what could physically be exported
        surplus = np.clip(pv_total - load, 0.0, None)
        self_use = np.minimum(pv_total, load)

        # --- stations: baseline charging profile is evening-heavy (uncoordinated)
        station_baseline = np.zeros(len(idx))
        for s in self.stations:
            # most energy 17:00-22:00, a morning bump, small flat floor
            w = (
                0.60 * np.exp(-0.5 * ((hours - 19.0) / 1.6) ** 2)
                + 0.25 * np.exp(-0.5 * ((hours - 7.5) / 1.1) ** 2)
                + 0.05
            )
            per_day_sum = w.reshape(DAYS, STEPS_PER_DAY).sum(axis=1)
            w_norm = w / np.repeat(per_day_sum, STEPS_PER_DAY)   # sums to 1 each day
            prof_kw = w_norm * s.daily_energy_kwh / 0.25          # kWh -> kW per 15-min step
            station_baseline += np.minimum(prof_kw, s.max_power_kw)

        df = pd.DataFrame(
            {
                "irradiance": irradiance,
                "clearness": clearness,
                "pv_total_kw": pv_total.sum(axis=1),
                "load_total_kw": load.sum(axis=1),
                # consumption still drawn from the grid after PV self-use —
                # this, not total load, is what absorbs exported surplus
                "grid_load_kw": (load - self_use).sum(axis=1),
                "surplus_total_kw": surplus.sum(axis=1),
                "station_baseline_kw": station_baseline,
                "hour": hours,
                "dow": dow,
                "month": month + 1,
            },
            index=idx,
        )
        # net feeder flow seen by transformer, positive = import, negative = reverse
        df["net_kw"] = (
            df["load_total_kw"] + df["station_baseline_kw"] - df["pv_total_kw"]
        )
        df["reverse_kw"] = np.clip(-df["net_kw"], 0.0, None)
        df["overload"] = (df["reverse_kw"] > REVERSE_LIMIT_KW).astype(int)

        self.per_home_surplus = surplus     # (T, H) ndarray, kW
        self.per_home_load = load
        self.index = idx
        return df

    # ------------------------------------------------------------------ #
    # Convenience views used by the market layer
    # ------------------------------------------------------------------ #
    def day_slice(self, df: pd.DataFrame, date: str) -> pd.DataFrame:
        return df.loc[date]

    def home_surplus_on(self, date: str) -> np.ndarray:
        mask = self.index.normalize() == pd.Timestamp(date)
        return self.per_home_surplus[mask]

    def headroom_kw(self, df_day: pd.DataFrame, extra_absorption_kw: np.ndarray | float = 0.0):
        """Safe export headroom per step (kW of surplus the feeder can accept).

        Exported surplus is absorbed by residual grid consumption and station
        charging before it reverses through the transformer, so headroom =
        reverse-flow limit + grid consumption + station load + steered load.
        """
        return (
            REVERSE_LIMIT_KW
            + df_day["grid_load_kw"].values
            + df_day["station_baseline_kw"].values
            + np.asarray(extra_absorption_kw)
        )


def pick_demo_day(df: pd.DataFrame) -> str:
    """The day blunt curtailment hurts most — maximum wasted clean energy."""
    wasted = df["surplus_total_kw"] * df["overload"] * 0.25
    daily = wasted.groupby(df.index.date).sum()
    if daily.max() <= 0:  # no breach anywhere: fall back to sunniest day
        daily = df.groupby(df.index.date)["irradiance"].mean()
    return str(daily.idxmax())
