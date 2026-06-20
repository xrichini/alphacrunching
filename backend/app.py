"""
Flask backend for SPX WTR dashboard.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, send_from_directory
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import fetch_spx_data, save_spx_history, load_spx_history
from metrics_calculator import (
    calculate_wtr,
    calculate_ttr,
    calculate_wtr_weekly_history,
    calculate_ttr_weekly_history,
    generate_upcoming_trade_ideas,
    save_metrics,
    save_wtr_weekly_history,
    save_ttr_weekly_history,
    get_latest_metrics as calculate_latest_metrics,
)


app = Flask(__name__, static_folder="../frontend", static_url_path="")


def load_or_compute_metrics():
    """Load metrics from files or compute if missing."""
    data_dir = Path(__file__).parent.parent / "data"
    
    wtr_file = data_dir / "wtr_history.json"
    ttr_file = data_dir / "ttr_history.json"
    wtr_weekly_file = data_dir / "wtr_weekly_history.json"
    ttr_weekly_file = data_dir / "ttr_weekly_history.json"
    
    # If files exist, load them
    if wtr_file.exists() and ttr_file.exists():
        with open(wtr_file) as f:
            wtr = json.load(f)
        with open(ttr_file) as f:
            ttr = json.load(f)
        
        # Load weekly histories if available
        wtr_weekly = {}
        ttr_weekly = {}
        if wtr_weekly_file.exists():
            with open(wtr_weekly_file) as f:
                wtr_weekly = json.load(f)
        if ttr_weekly_file.exists():
            with open(ttr_weekly_file) as f:
                ttr_weekly = json.load(f)
        
        return wtr, ttr, wtr_weekly, ttr_weekly
    
    # Otherwise compute from scratch
    print("Computing metrics from scratch...")
    spx_df = fetch_spx_data(lookback_days=120)
    wtr = calculate_wtr(spx_df)
    ttr = calculate_ttr(spx_df)
    wtr_weekly = calculate_wtr_weekly_history(spx_df)
    ttr_weekly = calculate_ttr_weekly_history(spx_df)
    
    save_metrics(wtr, ttr, {})
    save_wtr_weekly_history(wtr_weekly)
    save_ttr_weekly_history(ttr_weekly)
    return wtr, ttr, wtr_weekly, ttr_weekly


# Load metrics at startup
WTR_DATA, TTR_DATA, WTR_WEEKLY, TTR_WEEKLY = load_or_compute_metrics()


@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory("../frontend", "index.html")


@app.route("/api/wtr", methods=["GET"])
def get_wtr():
    """
    GET /api/wtr
    Returns WTR history for week selection dropdown.
    """
    return jsonify(WTR_DATA)


@app.route("/api/ttr", methods=["GET"])
def get_ttr():
    """
    GET /api/ttr
    Returns TTR history.
    """
    data_dir = Path(__file__).parent.parent / "data"
    ttr_file = data_dir / "ttr_history.json"
    
    if ttr_file.exists():
        with open(ttr_file) as f:
            ttr = json.load(f)
        return jsonify(ttr)
    
    return jsonify(TTR_DATA)


@app.route("/api/trade-ideas", methods=["GET"])
def get_trade_ideas():
    """
    GET /api/trade-ideas
    Returns upcoming trade ideas for the coming week with trend analysis.
    """
    # Generate trade ideas with trend data
    ideas_dict = generate_upcoming_trade_ideas(
        WTR_DATA,
        TTR_DATA,
        WTR_WEEKLY,
        TTR_WEEKLY
    )
    return jsonify(ideas_dict)


@app.route("/api/refresh", methods=["POST"])
def refresh_data():
    """
    POST /api/refresh
    Fetch fresh SPX data and recompute all metrics.
    """
    global WTR_DATA, TTR_DATA, WTR_WEEKLY, TTR_WEEKLY
    
    try:
        print("Refreshing SPX data and metrics...")
        
        # Fetch fresh data
        spx_df = fetch_spx_data(lookback_days=120)
        save_spx_history(spx_df)
        
        # Compute metrics (flat, 8-week rolling)
        wtr = calculate_wtr(spx_df)
        ttr = calculate_ttr(spx_df)
        
        # Compute weekly histories
        wtr_weekly = calculate_wtr_weekly_history(spx_df)
        ttr_weekly = calculate_ttr_weekly_history(spx_df)
        
        # Generate trade ideas with weekly histories
        ideas = generate_upcoming_trade_ideas(wtr, ttr, wtr_weekly, ttr_weekly)
        
        # Save all
        save_metrics(wtr, ttr, ideas)
        save_wtr_weekly_history(wtr_weekly)
        save_ttr_weekly_history(ttr_weekly)
        
        # Update in-memory cache
        WTR_DATA = wtr
        TTR_DATA = ttr
        WTR_WEEKLY = wtr_weekly
        TTR_WEEKLY = ttr_weekly
        
        return jsonify({
            "status": "success",
            "message": "Data refreshed successfully",
            "timestamp": datetime.now().isoformat(),
            "wtr_weeks": len(wtr),
            "trade_ideas": len(ideas.get("trade_ideas", [])),
        })
    
    except Exception as e:
        print(f"Error during refresh: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/api/latest-metrics", methods=["GET"])
def get_latest_metrics():
    """
    GET /api/latest-metrics
    Returns latest WTR and TTR values plus trade ideas with trend analysis.
    """
    # Get metrics (already in correct format: day_of_week -> percentage)
    latest_wtr = WTR_DATA
    latest_ttr = TTR_DATA
    
    # Generate trade ideas with trend data
    trade_ideas_dict = generate_upcoming_trade_ideas(
        latest_wtr, 
        latest_ttr, 
        WTR_WEEKLY, 
        TTR_WEEKLY
    )
    trade_ideas = trade_ideas_dict.get("trade_ideas", [])
    prev_wtr = trade_ideas_dict.get("prev_wtr", {})
    prev_ttr = trade_ideas_dict.get("prev_ttr", {})
    
    return jsonify({
        "wtr": latest_wtr,
        "ttr": latest_ttr,
        "prev_wtr": prev_wtr,
        "prev_ttr": prev_ttr,
        "trade_ideas": trade_ideas,
    })


if __name__ == "__main__":
    print("Starting Flask server at http://localhost:5000")
    app.run(debug=True, port=5000)
