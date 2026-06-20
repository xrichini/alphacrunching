"""
Data fetcher module for SPX historical data using yfinance.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import yfinance as yf


def fetch_spx_data(lookback_days: int = 120) -> pd.DataFrame:
    """
    Fetch SPX daily OHLC data from Yahoo Finance.
    
    Args:
        lookback_days: Number of trading days to fetch (default 120 ≈ 4 months)
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume (all lowercase)
    
    Note:
        Uses DATA_END_DATE environment variable (YYYY-MM-DD) if set, otherwise uses today.
        This ensures reproducible results across different execution times.
    """
    # Allow overriding end_date via environment variable (e.g., for GitHub Actions consistency)
    end_date_str = os.environ.get("DATA_END_DATE")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"[WARN] Invalid DATA_END_DATE format '{end_date_str}', using today")
            end_date = datetime.now()
    else:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=int(lookback_days * 1.3))  # Buffer for weekends/holidays
    
    print(f"Fetching SPX data from {start_date.date()} to {end_date.date()}...")
    
    # Download SPX data
    spx = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
    
    # Reset index to make Date a column
    spx = spx.reset_index()
    
    # Handle multi-index columns from yfinance
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    
    # Rename all columns to lowercase for consistency
    spx.columns = spx.columns.str.lower()
    spx.rename(columns={"date": "date"}, inplace=True)
    
    # Keep only trading days (non-null close data)
    spx = spx.dropna(subset=["close"])
    
    # Keep only the last `lookback_days` trading days
    spx = spx.tail(lookback_days)
    
    # Ensure date is datetime
    spx["date"] = pd.to_datetime(spx["date"])
    
    print(f"Downloaded {len(spx)} trading days of SPX data")
    return spx


def save_spx_history(df: pd.DataFrame, output_path: str = "data/spx_history.json") -> None:
    """
    Save SPX data to JSON file.
    
    Args:
        df: DataFrame with SPX data
        output_path: Path to save JSON file
    """
    # Convert to list of dicts for JSON serialization
    data = []
    for _, row in df.iterrows():
        data.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
        })
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(data)} records to {output_path}")


def load_spx_history(filepath: str = "data/spx_history.json") -> pd.DataFrame:
    """
    Load SPX history from JSON file.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        DataFrame with SPX data
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


if __name__ == "__main__":
    # Fetch and save SPX data
    spx_df = fetch_spx_data(lookback_days=120)
    save_spx_history(spx_df)
    print("✓ SPX data fetch and save completed")
