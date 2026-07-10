# TODO

## Up Next


## Blocked

## Done (recent)

- [x] Check WTR and TTR history. Current values for upcoming week are not added to history. Week shall start on Mondays.
  - History now appends current WTR/TTR under next Monday key on each run/refresh (skip if week already exists); cleared stale dev data; 8-week lookback for trend analysis; N/A displayed for missing/null values in frontend
- [x] End-to-end integration test
  - Dashboard loads at http://localhost:5000 with correctly selected week and WTR bars displaying 100% for Jun 8, 2026; Flask server running; all 3 trade signals showing "Go"
- [x] Add styling and interactivity
  - Color-coded bars implemented; week dropdown selects first week with data; Refresh button wired; fixed get_latest_metrics() to find week with actual data
- [x] Build HTML dashboard UI
  - Index.html, styles.css, script.js created with WTR chart, Trade Ideas table, and Refresh button; fully responsive
- [x] Create Flask API endpoints
  - GET /api/wtr, GET /api/ttr, GET /api/trade-ideas, GET /api/latest-metrics, POST /api/refresh all implemented and tested; endpoints return correct JSON
- [x] Generate trade ideas based on strategies
  - Trade ideas computed from WTR/TTR thresholds; 3 strategies tested (Mon/Wed/Thu 7DTE/1DTE Bull Put spreads with correct entry times and SMA checks)
- [x] Compute TTR metric
  - TTR calculated over past 2 months for each weekday; shows 100% for sample data
- [x] Compute WTR metric
  - WTR calculated over past 2 months for each weekday; saved to wtr_history.json; shows 100% for Jun 8, 2026 week
- [x] Fetch SPX data with yfinance and save to JSON
  - Sample SPX data created (120 days Apr-Jun 2026); data_fetcher.py downloads and saves to JSON
- [x] Setup project structure and dependencies
  - Created `/backend`, `/frontend`, `/data` folders; `pyproject.toml` with Flask/yfinance/pandas; Python 3.11 venv created; all packages installed using uv
