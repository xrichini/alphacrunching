#!/usr/bin/env python3
"""Test WTR/TTR calculation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import fetch_spx_data
from metrics_calculator import calculate_wtr, calculate_ttr

print("Fetching SPX data...")
df = fetch_spx_data(lookback_days=120)

print("\nCalculating WTR...")
wtr = calculate_wtr(df)

print(f"WTR result type: {type(wtr)}")
print(f"WTR: {wtr}")

print("\nCalculating TTR...")
ttr = calculate_ttr(df)

print(f"TTR result type: {type(ttr)}")
print(f"TTR: {ttr}")
