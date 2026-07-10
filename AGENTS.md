# AGENTS.md

Guidance for Kilo sessions working in this repo.

## What this project is

SPX options dashboard. Computes two indicators from Yahoo Finance SPX (`^GSPC`) daily closes:
- **WTR** — % of times SPX closed higher 7 days later, per weekday (Mon/Tue/Thu threshold ≥ 50%).
- **TTR** — % of times SPX closed higher the next trading day, per weekday (Wed/Fri threshold ≥ 60% + flat-or-higher trend vs previous week).

See `README.md` for the 4 documented strategies (Mon/Thu 7DTE, Wed 1DTE, Fri 3DTE). `generate_trade_ideas` in `metrics_calculator.py` also emits a Tuesday row not documented in the README.

## Stack & layout

- Python (Flask + pandas + yfinance) backend, vanilla JS/HTML/CSS frontend.
- `uv` for deps (`pyproject.toml` + `uv.lock`); declares `>=3.9` but CI uses 3.11.
- `backend/` — `app.py` (Flask API + serves `frontend/`), `data_fetcher.py`, `metrics_calculator.py`, `report_generator.py`, plus manual debug/test scripts.
- `frontend/` — static `index.html` / `script.js` / `styles.css`, served by Flask at `/`.
- `data/` — JSON caches (`wtr_history.json`, `ttr_history.json`, `wtr_weekly_history.json`, `ttr_weekly_history.json`, `spx_history.json`, `trade_ideas_upcoming.json`).
- `docs/report.html` — generated weekly report, deployed to GitHub Pages.

## Commands

Run from project root (cwd matters — see gotchas):

```bash
uv sync                                  # install deps into .venv
uv run python backend/app.py             # dashboard at http://localhost:5000 (debug mode)
uv run python backend/data_fetcher.py    # fetch SPX data → data/spx_history.json
uv run python backend/metrics_calculator.py  # recompute WTR/TTR + save to data/
uv run python backend/report_generator.py # generate docs/report.html (CI entrypoint)
```

No test framework, no lint, no typecheck. `backend/test_calc.py`, `backend/debug_wtr.py`, `backend/debug_detailed.py` are ad-hoc print-based scripts run directly with `python`; do not treat them as a suite.

## Gotchas

- **Run from project root.** `metrics_calculator.save_*` functions write to a relative `data/` path (`Path("data")`), while readers in `app.py`/`report_generator.py` resolve `data/` via `Path(__file__).parent.parent`. Running `metrics_calculator.py` or `data_fetcher.py` from another cwd silently writes to the wrong place.
- **Flat imports, not a package.** Backend modules do `sys.path.insert(0, backend_dir)` and `from data_fetcher import ...` (flat, no `backend.` prefix). Don't switch to package-qualified imports without reworking these path hacks.
- **yfinance multi-index columns.** `data_fetcher.fetch_spx_data` flattens yfinance's MultiIndex columns to level 0 and lowercases all column names. Metrics code expects lowercase `date`/`close`. This was a recurring bug source (see git log); preserve the flattening.
- **Lowercase weekday keys.** All JSON and dict keys use lowercase day names (`monday`, ...). `report_generator` converts Title-case day labels back to lowercase for lookups — a previous bug fix. Don't introduce mixed-case keys.
- **TTR skips weekends/holidays.** TTR searches forward up to 7 days for the next *trading* date in the dataset; WTR uses a fixed `+7 days`. Don't "simplify" TTR to `+1 day`.
- **`data/*.json` and `docs/report.html` are gitignored** (`.gitignore`) but already-tracked files remain tracked. New JSON files under `data/` won't be added by `git add .` unless force-added.
- **8-week rolling lookback.** WTR/TTR use the last `lookback_weeks*5` trading days (default 8 weeks). `calculate_wtr`/`calculate_ttr` are aliases for the `_for_lookback` variants; weekly-history variants key by `week_end.strftime("%Y-%m-%d")`.
- **History is append-only, keyed by next Monday.** Each app run/refresh appends current WTR/TTR values to `wtr_weekly_history.json`/`ttr_weekly_history.json` under the next Monday's date (via `get_next_monday()` + `append_weekly_history()`). If the week key already exists, the write is skipped. `load_weekly_history()` returns the last 8 weeks sorted descending. `None` values (no data pairs) are stored as JSON `null` and displayed as "N/A" in the frontend.
- **In-memory cache.** `app.py` loads metrics once at import (`WTR_DATA`, `TTR_DATA`, ... module globals). `/api/refresh` re-fetches and reassigns the globals; edits to data files require a refresh or restart.

## CI / deployment

`.github/workflows/weekly-report.yml` runs Sundays 18:00 UTC (and on dispatch): installs `yfinance` + `requests` via pip (not uv), runs `backend/report_generator.py`, copies `docs/report.html` → `pages/index.html`, deploys to GitHub Pages at `https://xrichini.github.io/alphacrunching/`. Optional Telegram notification requires repo secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

## API endpoints (Flask)

`GET /` (index.html), `GET /api/wtr`, `GET /api/ttr`, `GET /api/trade-ideas`, `GET /api/latest-metrics`, `GET /api/ttr-history`, `POST /api/refresh`.

## Task tracking

`TODO.md` uses the Up Next / Blocked / Done sections convention. Update it when picking up or finishing work rather than relying on memory.
