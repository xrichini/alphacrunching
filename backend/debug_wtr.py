#!/usr/bin/env python3
"""Debug script to verify WTR calculation logic"""

import pandas as pd
from datetime import timedelta
from data_fetcher import fetch_spx_data

# Fetch data
df = fetch_spx_data(lookback_days=120)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

print(f"Total rows: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print()

# Get all Mondays in the data
mondays = df[df["date"].dt.weekday == 0].copy()
print(f"Total Mondays in data: {len(mondays)}")
print()

# For each Monday, check if 7 days later closes higher
print("Monday WTR Analysis:")
print("-" * 80)

up_count = 0
down_count = 0
missing_count = 0

for idx, (_, row) in enumerate(mondays.iterrows()):
    current_date = row["date"]
    current_close = row["close"]
    
    # Find close price 7 days later
    target_date = current_date + timedelta(days=7)
    future_row = df[df["date"] == target_date]
    
    if not future_row.empty:
        future_close = future_row.iloc[0]["close"]
        change_pct = ((future_close - current_close) / current_close) * 100
        
        if future_close > current_close:
            status = "UP ✓"
            up_count += 1
        else:
            status = "DOWN ✗"
            down_count += 1
            
        print(f"{current_date.strftime('%Y-%m-%d')}: ${current_close:.2f} → ${future_close:.2f} ({change_pct:+.2f}%) {status}")
    else:
        missing_count += 1
        print(f"{current_date.strftime('%Y-%m-%d')}: ${current_close:.2f} → [NO DATA 7 DAYS LATER]")

print()
print(f"Summary:")
print(f"  UP:      {up_count}")
print(f"  DOWN:    {down_count}")
print(f"  Missing: {missing_count}")
if (up_count + down_count) > 0:
    actual_wtr = (up_count / (up_count + down_count)) * 100
    print(f"  WTR %:   {actual_wtr:.1f}%")
print()

# Same for Tuesday
print("\nTuesday WTR Analysis:")
print("-" * 80)

tuesdays = df[df["date"].dt.weekday == 1].copy()
print(f"Total Tuesdays in data: {len(tuesdays)}")

up_count = 0
down_count = 0
missing_count = 0

for idx, (_, row) in enumerate(tuesdays.iterrows()):
    current_date = row["date"]
    current_close = row["close"]
    
    target_date = current_date + timedelta(days=7)
    future_row = df[df["date"] == target_date]
    
    if not future_row.empty:
        future_close = future_row.iloc[0]["close"]
        change_pct = ((future_close - current_close) / current_close) * 100
        
        if future_close > current_close:
            status = "UP ✓"
            up_count += 1
        else:
            status = "DOWN ✗"
            down_count += 1
            
        print(f"{current_date.strftime('%Y-%m-%d')}: ${current_close:.2f} → ${future_close:.2f} ({change_pct:+.2f}%) {status}")
    else:
        missing_count += 1
        print(f"{current_date.strftime('%Y-%m-%d')}: ${current_close:.2f} → [NO DATA 7 DAYS LATER]")

print()
print(f"Summary:")
print(f"  UP:      {up_count}")
print(f"  DOWN:    {down_count}")
print(f"  Missing: {missing_count}")
if (up_count + down_count) > 0:
    actual_wtr = (up_count / (up_count + down_count)) * 100
    print(f"  WTR %:   {actual_wtr:.1f}%")
