"""
Metrics calculator module for WTR and TTR computation.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd


def get_next_monday() -> str:
    """Return next Monday's date as YYYY-MM-DD string (week-of key for history)."""
    today = datetime.now().date()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    return next_monday.strftime("%Y-%m-%d")


def append_weekly_history(filename: str, week_key: str, values: Dict) -> bool:
    """
    Append a week's values to a history JSON file. Skip if week_key already exists.
    Uses relative 'data/' path (run from project root).
    Returns True if appended, False if skipped.
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    filepath = data_dir / filename
    
    history = {}
    if filepath.exists():
        with open(filepath) as f:
            history = json.load(f)
    
    if week_key in history:
        print(f"Week {week_key} already in {filename}, skipping")
        return False
    
    history[week_key] = values
    with open(filepath, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Appended week {week_key} to {filename}")
    return True


def load_weekly_history(filepath, num_weeks: int = 8) -> Dict:
    """
    Load weekly history from JSON file, returning the last N weeks sorted descending.
    Accepts a full path (e.g. from Path(__file__).parent.parent / "data" / ...).
    """
    history = {}
    if Path(filepath).exists():
        with open(filepath) as f:
            history = json.load(f)
    sorted_keys = sorted(history.keys(), reverse=True)[:num_weeks]
    return {k: history[k] for k in sorted_keys}


def calculate_wtr_for_lookback(df: pd.DataFrame, lookback_weeks: int = 8) -> Dict[str, int]:
    """
    Calculate WTR over entire lookback period (8 weeks ≈ 2 months).
    Used for current week metrics display.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    # Keep only last `lookback_weeks * 5` trading days
    lookback_days = lookback_weeks * 5
    df = df.tail(lookback_days)
    
    weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    wtr_counts = {day: {"up": 0, "total": 0} for day in weekday_names}
    
    # For each day, check all occurrences
    for weekday_idx, weekday_name in enumerate(weekday_names):
        weekday_dates = df[df["date"].dt.weekday == weekday_idx]
        
        for _, row in weekday_dates.iterrows():
            current_date = row["date"]
            current_close = row["close"]
            target_date = current_date + timedelta(days=7)
            future_row = df[df["date"] == target_date]
            
            if not future_row.empty:
                future_close = future_row.iloc[0]["close"]
                wtr_counts[weekday_name]["total"] += 1
                
                if future_close > current_close:
                    wtr_counts[weekday_name]["up"] += 1
    
    # Calculate percentages (None when no data pairs available)
    wtr_result = {}
    for weekday_name in weekday_names:
        total = wtr_counts[weekday_name]["total"]
        up = wtr_counts[weekday_name]["up"]
        
        if total > 0:
            wtr_result[weekday_name] = int(round(up / total * 100))
        else:
            wtr_result[weekday_name] = None
    
    return wtr_result


# Backward compatibility: calculate_wtr is an alias for calculate_wtr_for_lookback
def calculate_wtr(df: pd.DataFrame, lookback_weeks: int = 8) -> Dict[str, int]:
    """Backward compatibility wrapper for calculate_wtr_for_lookback"""
    return calculate_wtr_for_lookback(df, lookback_weeks)


def calculate_wtr_weekly_history(df: pd.DataFrame, num_weeks: int = 8) -> Dict[str, Dict[str, int]]:
    """
    Calculate WTR for each of the past N weeks.
    Returns: {"2026-06-15": {"monday": 60, "tuesday": 71, ...}, "2026-06-08": {...}, ...}
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    if df.empty:
        return {}
    
    # Get the last date and work backwards by weeks
    last_date = df["date"].max()
    weeks_data = {}
    
    for week_offset in range(num_weeks):
        # Get end of week (Sunday of that week)
        week_end = last_date - timedelta(weeks=week_offset)
        # Get start of week (Monday of that week)
        week_start = week_end - timedelta(days=week_end.weekday())
        
        # Get data for this week
        week_df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]
        
        if len(week_df) < 3:  # Not enough data for this week
            continue
        
        # Calculate WTR for this week
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        wtr_counts = {day: {"up": 0, "total": 0} for day in weekday_names}
        
        for weekday_idx, weekday_name in enumerate(weekday_names):
            weekday_dates = week_df[week_df["date"].dt.weekday == weekday_idx]
            
            for _, row in weekday_dates.iterrows():
                current_date = row["date"]
                current_close = row["close"]
                target_date = current_date + timedelta(days=7)
                future_row = df[df["date"] == target_date]
                
                if not future_row.empty:
                    future_close = future_row.iloc[0]["close"]
                    wtr_counts[weekday_name]["total"] += 1
                    
                    if future_close > current_close:
                        wtr_counts[weekday_name]["up"] += 1
        
        # Calculate percentages (None when no data pairs available)
        week_key = week_end.strftime("%Y-%m-%d")
        wtr_result = {}
        for weekday_name in weekday_names:
            total = wtr_counts[weekday_name]["total"]
            up = wtr_counts[weekday_name]["up"]
            
            if total > 0:
                wtr_result[weekday_name] = int(round(up / total * 100))
            else:
                wtr_result[weekday_name] = None
        
        weeks_data[week_key] = wtr_result
    
    return weeks_data


def calculate_ttr_for_lookback(df: pd.DataFrame, lookback_weeks: int = 8) -> Dict[str, int]:
    """
    Calculate TTR over entire lookback period (8 weeks ≈ 2 months).
    Used for current week metrics display.
    Special case: Friday TTR checks vs. Monday (skips weekend).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    # Keep only last `lookback_weeks * 5` trading days
    lookback_days = lookback_weeks * 5
    df = df.tail(lookback_days)
    
    # Create a set of all available trading dates for fast lookup
    trading_dates = set(df["date"].dt.date)
    
    weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    ttr_counts = {day: {"up": 0, "total": 0} for day in weekday_names}
    
    # For each day, check all occurrences
    for weekday_idx, weekday_name in enumerate(weekday_names):
        weekday_dates = df[df["date"].dt.weekday == weekday_idx]
        
        for _, row in weekday_dates.iterrows():
            current_date = row["date"]
            current_close = row["close"]
            
            # Find next trading day (skip weekends/holidays if market is closed)
            target_date = current_date + timedelta(days=1)
            
            # Keep searching for the next trading day until we find one or run out of data
            max_search_days = 7  # Don't search more than a week ahead
            for _ in range(max_search_days):
                if target_date.date() in trading_dates:
                    break
                target_date += timedelta(days=1)
            
            # Check if we found a future trading day
            future_row = df[df["date"] == target_date]
            
            if not future_row.empty:
                future_close = future_row.iloc[0]["close"]
                ttr_counts[weekday_name]["total"] += 1
                
                if future_close > current_close:
                    ttr_counts[weekday_name]["up"] += 1
    
    # Calculate percentages (None when no data pairs available)
    ttr_result = {}
    for weekday_name in weekday_names:
        total = ttr_counts[weekday_name]["total"]
        up = ttr_counts[weekday_name]["up"]
        
        if total > 0:
            ttr_result[weekday_name] = int(round(up / total * 100))
        else:
            ttr_result[weekday_name] = None
    
    return ttr_result


# Backward compatibility: calculate_ttr is an alias for calculate_ttr_for_lookback
def calculate_ttr(df: pd.DataFrame, lookback_weeks: int = 8) -> Dict[str, int]:
    """Backward compatibility wrapper for calculate_ttr_for_lookback"""
    return calculate_ttr_for_lookback(df, lookback_weeks)


def calculate_ttr_weekly_history(df: pd.DataFrame, num_weeks: int = 8) -> Dict[str, Dict[str, int]]:
    """
    Calculate TTR for each of the past N weeks.
    Returns: {"2026-06-15": {"monday": 29, "tuesday": 50, ...}, "2026-06-08": {...}, ...}
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    if df.empty:
        return {}
    
    # Create a set of all available trading dates
    trading_dates = set(df["date"].dt.date)
    
    # Get the last date and work backwards by weeks
    last_date = df["date"].max()
    weeks_data = {}
    
    for week_offset in range(num_weeks):
        # Get end of week (Sunday of that week)
        week_end = last_date - timedelta(weeks=week_offset)
        # Get start of week (Monday of that week)
        week_start = week_end - timedelta(days=week_end.weekday())
        
        # Get data for this week
        week_df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]
        
        if len(week_df) < 3:  # Not enough data for this week
            continue
        
        # Calculate TTR for this week
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        ttr_counts = {day: {"up": 0, "total": 0} for day in weekday_names}
        
        for weekday_idx, weekday_name in enumerate(weekday_names):
            weekday_dates = week_df[week_df["date"].dt.weekday == weekday_idx]
            
            for _, row in weekday_dates.iterrows():
                current_date = row["date"]
                current_close = row["close"]
                
                # Find next trading day
                target_date = current_date + timedelta(days=1)
                
                # Keep searching for the next trading day
                max_search_days = 7
                for _ in range(max_search_days):
                    if target_date.date() in trading_dates:
                        break
                    target_date += timedelta(days=1)
                
                future_row = df[df["date"] == target_date]
                
                if not future_row.empty:
                    future_close = future_row.iloc[0]["close"]
                    ttr_counts[weekday_name]["total"] += 1
                    
                    if future_close > current_close:
                        ttr_counts[weekday_name]["up"] += 1
        
        # Calculate percentages (None when no data pairs available)
        week_key = week_end.strftime("%Y-%m-%d")
        ttr_result = {}
        for weekday_name in weekday_names:
            total = ttr_counts[weekday_name]["total"]
            up = ttr_counts[weekday_name]["up"]
            
            if total > 0:
                ttr_result[weekday_name] = int(round(up / total * 100))
            else:
                ttr_result[weekday_name] = None
        
        weeks_data[week_key] = ttr_result
    
    return weeks_data



def get_latest_metrics(wtr_dict: Dict, ttr_dict: Dict) -> Tuple[Dict, Dict]:
    """
    Get the most recent WTR and TTR values.
    
    Args:
        wtr_dict: WTR data (day_of_week -> percentage)
        ttr_dict: TTR data (day_of_week -> percentage)
    
    Returns:
        Tuple of (wtr_dict, ttr_dict)
    """
    # With new structure, dicts are already in the right format
    return wtr_dict, ttr_dict


def generate_trade_ideas(
    wtr_value: int, 
    ttr_value: int, 
    day_of_week: str,
    prev_wtr_value: int = None,
    prev_ttr_value: int = None
) -> List[Dict]:
    """
    Generate trade ideas based on WTR/TTR values and day of week.
    Includes trend checking for Wed/Fri (flat/higher vs previous week).
    
    Args:
        wtr_value: Current WTR percentage for the day
        ttr_value: Current TTR percentage for the day
        day_of_week: Day name ("monday", "tuesday", etc.)
        prev_wtr_value: Previous week's WTR (for trend check)
        prev_ttr_value: Previous week's TTR (for trend check)
    
    Returns:
        List of trade idea dicts with detailed Go/No-Go reasons
    """
    ideas = []
    
    # Defensive: treat None (no data) as 0
    wtr_value = wtr_value or 0
    ttr_value = ttr_value or 0
    
    if day_of_week == "monday":
        # Mon 7DTE: WTR >= 50% → Bull Put Spread, 7DTE, 3:30pm ET, check 5sma > 10sma
        # NO trend requirement
        signal = "Go" if wtr_value >= 50 else "No Go"
        reason = f"WTR {wtr_value}% {'≥' if wtr_value >= 50 else '<'} 50%"
        ideas.append({
            "day": "Monday",
            "strategy": "7DTE ATM Bull Put Spread",
            "entry_time": "3:30pm ET",
            "expiration": "7DTE",
            "credit_target": "$2.00 (5pt wide)",
            "sma_check": "5sma > 10sma (30m before close)",
            "wtr_ttr": f"WTR: {wtr_value}%",
            "signal": signal,
            "reason": reason,
        })
    
    elif day_of_week == "tuesday":
        # Tue 7DTE: WTR >= 50% → Bull Put Spread, 7DTE, 3:30pm ET, check 5sma > 10sma
        # NO trend requirement (not in main 4 strategies, but included for completeness)
        signal = "Go" if wtr_value >= 50 else "No Go"
        reason = f"WTR {wtr_value}% {'≥' if wtr_value >= 50 else '<'} 50%"
        ideas.append({
            "day": "Tuesday",
            "strategy": "7DTE ATM Bull Put Spread",
            "entry_time": "3:30pm ET",
            "expiration": "7DTE",
            "credit_target": "$2.00 (5pt wide)",
            "sma_check": "5sma > 10sma (30m before close)",
            "wtr_ttr": f"WTR: {wtr_value}%",
            "signal": signal,
            "reason": reason,
        })
    
    elif day_of_week == "wednesday":
        # Wed 1DTE: TTR >= 60% + trend check "flat/higher"
        # Bull Put Spread, 1DTE, 3:45pm ET, check SPX > 20sma
        ttr_ok = ttr_value >= 60
        
        # Trend check: current week TTR >= previous week TTR (flat or higher)
        trend_ok = True
        trend_reason = ""
        if prev_ttr_value is not None:
            trend_ok = ttr_value >= prev_ttr_value
            trend_text = "higher" if ttr_value > prev_ttr_value else ("flat" if ttr_value == prev_ttr_value else "lower")
            trend_reason = f"Trend: {trend_text} vs prev week ({prev_ttr_value}%)"
        
        signal = "Go" if (ttr_ok and trend_ok) else "No Go"
        reason = ""
        if not ttr_ok:
            reason = f"TTR {ttr_value}% < 60%"
        elif not trend_ok:
            reason = f"TTR {ttr_value}% ≥ 60% but {trend_text} ({prev_ttr_value}%)"
        else:
            reason = f"TTR {ttr_value}% ≥ 60% and {trend_reason}"
        
        ideas.append({
            "day": "Wednesday",
            "strategy": "1DTE ATM Bull Put Spread",
            "entry_time": "3:45pm ET",
            "expiration": "1DTE",
            "credit_target": "$2.00 (5pt wide)",
            "sma_check": "SPX > 20sma (15m before close)",
            "wtr_ttr": f"TTR: {ttr_value}%",
            "signal": signal,
            "reason": reason,
            "trend_check": trend_reason if trend_reason else "N/A",
        })
    
    elif day_of_week == "thursday":
        # Thu 7DTE: WTR >= 50% → Bull Put Spread, 7DTE, 3:30pm ET, check 5sma > 10sma
        # NO trend requirement
        signal = "Go" if wtr_value >= 50 else "No Go"
        reason = f"WTR {wtr_value}% {'≥' if wtr_value >= 50 else '<'} 50%"
        ideas.append({
            "day": "Thursday",
            "strategy": "7DTE ATM Bull Put Spread",
            "entry_time": "3:30pm ET",
            "expiration": "7DTE",
            "credit_target": "$2.00 (5pt wide)",
            "sma_check": "5sma > 10sma (30m before close)",
            "wtr_ttr": f"WTR: {wtr_value}%",
            "signal": signal,
            "reason": reason,
        })
    
    elif day_of_week == "friday":
        # Fri 3DTE: TTR >= 60% + trend check "flat/higher"
        # Bull Put Spread, 3DTE (expires Mon), 3:45pm ET, check SPX > 20sma
        ttr_ok = ttr_value >= 60
        
        # Trend check: current week TTR >= previous week TTR (flat or higher)
        trend_ok = True
        trend_reason = ""
        if prev_ttr_value is not None:
            trend_ok = ttr_value >= prev_ttr_value
            trend_text = "higher" if ttr_value > prev_ttr_value else ("flat" if ttr_value == prev_ttr_value else "lower")
            trend_reason = f"Trend: {trend_text} vs prev week ({prev_ttr_value}%)"
        
        signal = "Go" if (ttr_ok and trend_ok) else "No Go"
        reason = ""
        if not ttr_ok:
            reason = f"TTR {ttr_value}% < 60%"
        elif not trend_ok:
            reason = f"TTR {ttr_value}% ≥ 60% but {trend_text} ({prev_ttr_value}%)"
        else:
            reason = f"TTR {ttr_value}% ≥ 60% and {trend_reason}"
        
        ideas.append({
            "day": "Friday",
            "strategy": "3DTE ATM Bull Put Spread",
            "entry_time": "3:45pm ET",
            "expiration": "3DTE",
            "credit_target": "$2.00 (5pt wide)",
            "sma_check": "SPX > 20sma (15m before close)",
            "wtr_ttr": f"TTR: {ttr_value}%",
            "signal": signal,
            "reason": reason,
            "trend_check": trend_reason if trend_reason else "N/A",
        })
    
    return ideas


def generate_upcoming_trade_ideas(
    wtr_dict: Dict,
    ttr_dict: Dict,
    wtr_weekly: Dict[str, Dict[str, int]] = None,
    ttr_weekly: Dict[str, Dict[str, int]] = None,
    next_trading_day: str = None
) -> Dict:
    """
    Generate trade ideas for the upcoming trading week with trend checking.
    
    Args:
        wtr_dict: Current WTR data keyed by day of week
        ttr_dict: Current TTR data keyed by day of week
        wtr_weekly: Weekly WTR history (optional, for trend checking)
        ttr_weekly: Weekly TTR history (optional, for trend checking)
        next_trading_day: Override for next trading day (for testing)
    
    Returns:
        Dict with trade ideas for the week including trend information
    """
    # Get latest metrics (for when weekly histories not provided)
    latest_wtr = wtr_dict
    latest_ttr = ttr_dict
    
    # Extract previous week's metrics for trend checking
    prev_wtr = {}
    prev_ttr = {}
    if wtr_weekly and ttr_weekly:
        # Get list of weeks (sorted, most recent first)
        wtr_weeks = sorted(wtr_weekly.keys(), reverse=True)
        ttr_weeks = sorted(ttr_weekly.keys(), reverse=True)
        
        # Current week is the first, previous is the second
        if len(wtr_weeks) > 1:
            prev_wtr = wtr_weekly.get(wtr_weeks[1], {})
        if len(ttr_weeks) > 1:
            prev_ttr = ttr_weekly.get(ttr_weeks[1], {})
    
    # Determine next trading week start date (next Monday)
    if next_trading_day is None:
        next_week_start = get_next_monday()
    else:
        next_week_start = None
    
    trade_ideas = []
    
    # Generate trade ideas for each day of the week with trend data
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        wtr_val = latest_wtr.get(day, 0)
        ttr_val = latest_ttr.get(day, 0)
        prev_wtr_val = prev_wtr.get(day) if prev_wtr else None
        prev_ttr_val = prev_ttr.get(day) if prev_ttr else None
        
        ideas = generate_trade_ideas(
            wtr_val, ttr_val, day, 
            prev_wtr_val, prev_ttr_val
        )
        trade_ideas.extend(ideas)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "next_week_start": next_week_start,
        "latest_wtr": latest_wtr,
        "latest_ttr": latest_ttr,
        "prev_wtr": prev_wtr,
        "prev_ttr": prev_ttr,
        "trade_ideas": trade_ideas,
    }


def save_metrics(wtr_dict: Dict, ttr_dict: Dict, ideas_dict: Dict) -> None:
    """
    Save WTR, TTR, and trade ideas to JSON files.
    """
    # Save WTR
    Path("data").mkdir(exist_ok=True)
    
    with open("data/wtr_history.json", "w") as f:
        json.dump(wtr_dict, f, indent=2)
    print(f"Saved WTR to data/wtr_history.json")
    
    # Save TTR
    with open("data/ttr_history.json", "w") as f:
        json.dump(ttr_dict, f, indent=2)
    print(f"Saved TTR to data/ttr_history.json")
    
    # Save trade ideas
    with open("data/trade_ideas_upcoming.json", "w") as f:
        json.dump(ideas_dict, f, indent=2)
    print(f"Saved trade ideas to data/trade_ideas_upcoming.json")


def save_wtr_weekly_history(wtr_weekly: Dict[str, Dict[str, int]]) -> None:
    """
    Save WTR weekly history to JSON file.
    Format: {"2026-06-15": {"monday": 60, ...}, "2026-06-08": {...}, ...}
    """
    Path("data").mkdir(exist_ok=True)
    
    with open("data/wtr_weekly_history.json", "w") as f:
        json.dump(wtr_weekly, f, indent=2)
    print(f"Saved WTR weekly history to data/wtr_weekly_history.json")


def save_ttr_weekly_history(ttr_weekly: Dict[str, Dict[str, int]]) -> None:
    """
    Save TTR weekly history to JSON file.
    Format: {"2026-06-15": {"monday": 29, ...}, "2026-06-08": {...}, ...}
    """
    Path("data").mkdir(exist_ok=True)
    
    with open("data/ttr_weekly_history.json", "w") as f:
        json.dump(ttr_weekly, f, indent=2)
    print(f"Saved TTR weekly history to data/ttr_weekly_history.json")


if __name__ == "__main__":
    from data_fetcher import load_spx_history
    
    df = load_spx_history()
    wtr = calculate_wtr(df)
    ttr = calculate_ttr(df)
    ideas = generate_upcoming_trade_ideas(wtr, ttr)
    
    save_metrics(wtr, ttr, ideas)
    
    # Append current week to history (skip if already exists)
    week_key = get_next_monday()
    append_weekly_history("wtr_weekly_history.json", week_key, wtr)
    append_weekly_history("ttr_weekly_history.json", week_key, ttr)
    
    print("✓ Metrics calculation completed")
