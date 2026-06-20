#!/usr/bin/env python3
"""Debug WTR/TTR with details"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import fetch_spx_data
from metrics_calculator import calculate_wtr, calculate_ttr, get_latest_metrics

print("Fetching SPX data...")
df = fetch_spx_data(lookback_days=120)

print("\nCalculating WTR...")
wtr = calculate_wtr(df)

print("\nWTR by week:")
for week_start in sorted(wtr.keys()):
    print(f"  {week_start}: {wtr[week_start]}")

print("\nCalculating TTR...")
ttr = calculate_ttr(df)

print("\nTTR by week:")
for week_start in sorted(ttr.keys()):
    print(f"  {week_start}: {ttr[week_start]}")

print("\nGetting latest metrics...")
latest_wtr, latest_ttr = get_latest_metrics(wtr, ttr)
print(f"Latest WTR: {latest_wtr}")
print(f"Latest TTR: {latest_ttr}")
