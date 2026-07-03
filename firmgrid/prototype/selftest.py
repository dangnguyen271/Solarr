"""End-to-end smoke test + invariant checks. Run: python selftest.py"""

import time

import numpy as np

from auction import SAFETY_MARGIN
from firmblock import build_firm_block
from gridmind import GridMind
from market import run_day
from twin import REVERSE_LIMIT_KW, FeederTwin, pick_demo_day

t0 = time.time()
twin = FeederTwin()
df = twin.simulate_year()
print(f"[twin] {len(df):,} steps | overload windows/yr: {int(df['overload'].sum())} "
      f"| annual surplus: {df['surplus_total_kw'].sum()*0.25/1000:.1f} MWh "
      f"| peak reverse: {df['reverse_kw'].max():.0f} kW (limit {REVERSE_LIMIT_KW:.0f})")
assert df["overload"].sum() > 50, "twin must produce a meaningful number of breach windows"

mind = GridMind().fit(df)
print(f"[gridmind] F1={mind.metrics['congestion_f1']:.3f} "
      f"MAE={mind.metrics['surplus_mae_kw']:.2f} kW "
      f"({mind.metrics['breach_windows_test']} breach windows in test)")
assert mind.metrics["congestion_f1"] > 0.6, "congestion model too weak"

day = pick_demo_day(df)
print(f"[demo day] {day}")

res = run_day(twin, df, mind, day)
print(f"[market] baseline wasted {res.baseline_wasted_kwh:.0f} kWh "
      f"({res.baseline_breaches} breach windows) | FirmGrid wasted {res.fg_wasted_kwh:.0f} kWh "
      f"({res.fg_breaches} breaches) | recovered {res.recovered_kwh:.0f} kWh "
      f"| paid {res.vnd_paid:,.0f} VND | CO2 {res.co2_avoided_kg:.0f} kg "
      f"| fairness max wait {res.fairness_max_wait}")
assert res.baseline_breaches > 0, "demo day must show a baseline breach"
assert res.fg_breaches == 0, "FirmGrid ON must stay inside the limit"
assert res.recovered_kwh > 0, "FirmGrid must recover energy"
assert res.ledger.verify_chain(), "ledger chain must verify"

# invariant: accepted export never exceeds SAFETY_MARGIN * headroom
steered = res.steered_station_kw
headroom = (REVERSE_LIMIT_KW + res.df_day["grid_load_kw"].values + steered)
exported = res.df_day["surplus_total_kw"].values - np.maximum(
    res.df_day["surplus_total_kw"].values - headroom * SAFETY_MARGIN, 0
)
assert (res.reverse_fg_kw <= REVERSE_LIMIT_KW + 1e-6).all(), "reverse flow must respect limit"

# fraud injection
res_f = run_day(twin, df, mind, day, fraud_bid={"hid": 3, "kw": 15.0})
print(f"[sentinel] fraud events: {len(res_f.fraud_events)}")
assert res_f.fraud_events, "sentinel must block the inflated bid"

# storm front
res_c = run_day(twin, df, mind, day, cloud_dim=0.6)
print(f"[storm 60%] recovered {res_c.recovered_kwh:.0f} kWh, breaches {res_c.fg_breaches}")
assert res_c.fg_breaches == 0
assert res_c.recovered_kwh >= -1.0, "FirmGrid must never do meaningfully worse than baseline"

blk = build_firm_block(df, n_transformers=200, storage_mwh=40, storage_mw=10, dc_load_mw=20)
print(f"[firmblock] CFE {blk['cfe_score']*100:.0f}% | ${blk['blended_cost_usd_mwh']:.0f}/MWh "
      f"| {blk['clean_gwh']:.1f} GWh/yr clean | {blk['co2_avoided_t_per_year']:,.0f} tCO2/yr")
assert 0.0 < blk["cfe_score"] <= 1.0

print(f"\nALL CHECKS PASSED in {time.time()-t0:.1f}s")
