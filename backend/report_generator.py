"""
Generate weekly WTR/TTR report as HTML and return report data
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import fetch_spx_data
from metrics_calculator import (
    calculate_wtr,
    calculate_ttr,
    calculate_wtr_weekly_history,
    calculate_ttr_weekly_history,
    save_metrics,
    save_wtr_weekly_history,
    save_ttr_weekly_history,
)


def compute_and_save_metrics():
    """Compute WTR/TTR metrics from scratch and save to files"""
    try:
        print("[COMPUTE] Fetching SPX data from yfinance (120 days lookback)...")
        spx_df = fetch_spx_data(lookback_days=120)
        print(f"[COMPUTE] Got {len(spx_df)} SPX records")
        print(f"[COMPUTE] DataFrame columns: {spx_df.columns.tolist()}")
        print(f"[COMPUTE] DataFrame index: {spx_df.index[:3].tolist()} ... {spx_df.index[-3:].tolist()}")
        print(f"[COMPUTE] DataFrame shape: {spx_df.shape}")
        print(f"[COMPUTE] First row: {spx_df.iloc[0].to_dict() if len(spx_df) > 0 else 'empty'}")
        
        print("[COMPUTE] Calculating WTR...")
        wtr = calculate_wtr(spx_df)
        print(f"[COMPUTE] WTR: {wtr}")
        
        print("[COMPUTE] Calculating TTR...")
        ttr = calculate_ttr(spx_df)
        print(f"[COMPUTE] TTR: {ttr}")
        
        print("[COMPUTE] Calculating WTR weekly history...")
        wtr_weekly = calculate_wtr_weekly_history(spx_df)
        print(f"[COMPUTE] WTR weekly: {wtr_weekly}")
        
        print("[COMPUTE] Calculating TTR weekly history...")
        ttr_weekly = calculate_ttr_weekly_history(spx_df)
        print(f"[COMPUTE] TTR weekly: {ttr_weekly}")
        
        print("[COMPUTE] Saving metrics to JSON files...")
        save_metrics(wtr, ttr, {})
        save_wtr_weekly_history(wtr_weekly)
        save_ttr_weekly_history(ttr_weekly)
        print("[COMPUTE] Metrics saved!")
        
        return {
            "wtr": wtr,
            "ttr": ttr,
            "wtr_weekly": wtr_weekly,
            "ttr_weekly": ttr_weekly,
        }
    except Exception as e:
        print(f"[COMPUTE] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_metrics():
    """Load WTR/TTR data from JSON files or compute if missing"""
    data_dir = Path(__file__).parent.parent / "data"
    
    wtr_file = data_dir / "wtr_history.json"
    ttr_file = data_dir / "ttr_history.json"
    wtr_weekly_file = data_dir / "wtr_weekly_history.json"
    ttr_weekly_file = data_dir / "ttr_weekly_history.json"
    
    # If all files exist, load them
    if all(f.exists() for f in [wtr_file, ttr_file, wtr_weekly_file, ttr_weekly_file]):
        with open(wtr_file) as f:
            wtr_data = json.load(f)
        with open(ttr_file) as f:
            ttr_data = json.load(f)
        with open(wtr_weekly_file) as f:
            wtr_weekly = json.load(f)
        with open(ttr_weekly_file) as f:
            ttr_weekly = json.load(f)
        return {
            "wtr": wtr_data,
            "ttr": ttr_data,
            "wtr_weekly": wtr_weekly,
            "ttr_weekly": ttr_weekly,
        }
    
    # Otherwise compute from scratch
    return compute_and_save_metrics()


def generate_html_report(metrics):
    """Generate HTML report of WTR/TTR metrics"""
    if not metrics:
        return None
    
    wtr = metrics.get("wtr", {})
    ttr = metrics.get("ttr", {})
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Build table rows - convert day names to lowercase for JSON key lookup
    wtr_rows = "\n".join([
        f"<tr><td>{day}</td><td>{wtr.get(day.lower(), 'N/A')}%</td></tr>"
        for day in days
    ])
    
    ttr_rows = "\n".join([
        f"<tr><td>{day}</td><td>{ttr.get(day.lower(), 'N/A')}%</td></tr>"
        for day in days
    ])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPX WTR/TTR Weekly Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 900px;
            width: 100%;
            padding: 40px;
        }}
        h1 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 2rem;
        }}
        .timestamp {{
            color: #718096;
            font-size: 0.9rem;
            margin-bottom: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
        }}
        .metric-card h2 {{
            color: #2d3748;
            font-size: 1.3rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .metric-icon {{
            font-size: 1.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #edf2f7;
            color: #2d3748;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e0;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        .info-box {{
            background: #edf2f7;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 30px;
            border-radius: 4px;
            color: #2d3748;
            font-size: 0.95rem;
        }}
        .footer {{
            text-align: center;
            color: #718096;
            margin-top: 30px;
            font-size: 0.85rem;
        }}
        @media (max-width: 600px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SPX WTR/TTR Weekly Report</h1>
        <div class="timestamp">Generated on {datetime.now().strftime('%A, %B %d, %Y at %H:%M UTC')}</div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h2><span class="metric-icon">📈</span> Weekly Triumph Rate (WTR)</h2>
                <p style="color: #718096; margin-bottom: 12px; font-size: 0.9rem;">% of times SPX closed higher 7 days later</p>
                <table>
                    <thead>
                        <tr>
                            <th>Day</th>
                            <th>WTR %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {wtr_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="metric-card">
                <h2><span class="metric-icon">⏭️</span> Tomorrow's Triumph Rate (TTR)</h2>
                <p style="color: #718096; margin-bottom: 12px; font-size: 0.9rem;">% of times SPX closed higher next day</p>
                <table>
                    <thead>
                        <tr>
                            <th>Day</th>
                            <th>TTR %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ttr_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="info-box">
            <strong>ℹ️ Trading Signals Based On:</strong><br>
            • <strong>Monday/Thursday (7DTE):</strong> WTR ≥ 50% + 5SMA > 10SMA<br>
            • <strong>Wednesday (1DTE):</strong> TTR ≥ 60% + Trend Check + SPX > 20SMA<br>
            • <strong>Friday (3DTE):</strong> TTR ≥ 60% + Trend Check + SPX > 20SMA<br>
            All strategies: ATM Bull Put Spreads with $2.00+ credit targets
        </div>
        
        <div class="footer">
            <strong>Alpha Crunching</strong> • SPX Intraday Seasonality Indicator<br>
            Dashboard: <a href="https://xrichini.github.io/alphacrunching/index.html" style="color: #667eea;">https://xrichini.github.io/alphacrunching/</a>
        </div>
    </div>
</body>
</html>"""
    
    return html


def generate_text_report(metrics):
    """Generate plaintext report for Telegram"""
    if not metrics:
        return None
    
    wtr = metrics.get("wtr", {})
    ttr = metrics.get("ttr", {})
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    wtr_text = "\n".join([
        f"  {day}: {wtr.get(day.lower(), 'N/A')}%"
        for day in days
    ])
    
    ttr_text = "\n".join([
        f"  {day}: {ttr.get(day.lower(), 'N/A')}%"
        for day in days
    ])
    
    report = f"""📊 *SPX WTR/TTR Weekly Report*
Generated: {datetime.now().strftime('%A, %B %d, %Y')}

📈 *Weekly Triumph Rate (WTR)*
_% of times SPX closed higher 7 days later_
{wtr_text}

⏭️ *Tomorrow's Triumph Rate (TTR)*
_% of times SPX closed higher next day_
{ttr_text}

💡 *This Week's Trading Signals*
🔵 Mon/Thu (7DTE): WTR ≥ 50%
🟠 Wed (1DTE): TTR ≥ 60% + Trend Check
🟣 Fri (3DTE): TTR ≥ 60% + Trend Check

📌 All strategies: ATM Bull Put Spreads with $2.00+ credit targets

📊 Full Dashboard:
https://xrichini.github.io/alphacrunching/"""
    
    return report


def save_report(html_content, output_path):
    """Save HTML report to file"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html_content)
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    print("[MAIN] Starting WTR/TTR report generation workflow...")
    print(f"[MAIN] Working directory: {Path.cwd()}")
    
    try:
        # STEP 1: Compute fresh metrics from yfinance
        print("\n[MAIN] STEP 1: Computing metrics from fresh SPX data...")
        metrics = compute_and_save_metrics()
        if not metrics:
            print("[MAIN] ERROR: Failed to compute metrics")
            sys.exit(1)
        
        print(f"[MAIN] [OK] Metrics computed successfully!")
        print(f"[MAIN]   WTR: {metrics.get('wtr')}")
        print(f"[MAIN]   TTR: {metrics.get('ttr')}")
        
        # STEP 2: Generate HTML report
        print("\n[MAIN] STEP 2: Generating HTML report...")
        html = generate_html_report(metrics)
        if not html:
            print("[MAIN] ERROR: Failed to generate HTML")
            sys.exit(1)
        
        # STEP 3: Generate Telegram text
        print("[MAIN] STEP 3: Generating Telegram message...")
        text = generate_text_report(metrics)
        if not text:
            print("[MAIN] ERROR: Failed to generate text")
            sys.exit(1)
        
        # STEP 4: Save HTML report to docs/
        print("[MAIN] STEP 4: Saving HTML report...")
        project_root = Path(__file__).parent.parent
        output_path = project_root / "docs" / "report.html"
        save_report(html, output_path)
        
        print(f"[MAIN] [OK] HTML report saved to: {output_path}")
        print(f"[MAIN] Report timestamp: {datetime.now().strftime('%A, %B %d, %Y at %H:%M UTC')}")
        
        # STEP 5: Display Telegram message for verification
        print("\n[MAIN] STEP 5: Telegram message (for workflow logs):")
        print("=" * 60)
        print(text)
        print("=" * 60)
        
        print("\n[MAIN] [OK] Report generation workflow completed successfully!")
        
    except Exception as e:
        print(f"\n[MAIN] [ERROR] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
