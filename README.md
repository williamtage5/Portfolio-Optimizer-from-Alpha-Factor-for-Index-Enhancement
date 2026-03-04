# Optimizer Backtest Framework

## Overview
This project runs a simple portfolio backtest with periodic rebalances. It loads daily cross-sectional data, solves a constrained linear optimization problem (CVXPY), carries holdings forward on non-rebalance days, and writes per-day holdings plus turnover logs.

## Key Features
- Single-period linear optimization with turnover, industry, and market-cap exposure constraints.
- Rebalance calendar controlled in `config.py`.
- Daily holdings export and turnover logs per run.
- Per-run output folders with timestamped names.

## Data Format
Input files are CSVs named by date (e.g., `YYYYMMDD.csv`). Each file must include the following columns:

- `code`: security identifier
- `alpha`: expected return signal
- `industry_code`: industry classification (used for one-hot exposure constraints)
- `mce`: market-cap exposure factor
- `wbench`: benchmark weight

Missing values in `alpha`, `mce`, and `wbench` are filled with 0.0 during loading.

## Sample Data
To make the repository uploadable, a sample dataset is provided in `data_sample/`. Each CSV there keeps only one row copied from the original raw data to avoid encoding issues.

If you want to run with full data, place it under `data/` using the same folder name as in the config.

## Configuration
Edit `config.py` to update:
- `DATA_DIR`: raw data folder path
- `REBALANCE_DATES`: list of rebalance dates
- `MAX_WEIGHT`, `MAX_MCE_EXPOSURE`, `MAX_TURNOVER`: constraint parameters

`run_config.json` is generated for each run and includes the data date range.

## Run Command Example
```bash
python main.py
```

## Outputs
Each run creates a timestamped folder under `outputs/`:
- `daily_weights/`: per-day holdings
- `turnover_logs.csv`: turnover and holdings count
- `run.log`: full runtime log
- `run_config.json`: configuration snapshot for the run

## Project Structure
```
.
??? .gitignore
??? backtest_engine.py
??? config.py
??? data/
?   ??? 20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20/
?       ??? *.csv
??? data_loader.py
??? data_sample/
?   ??? 20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20/
?       ??? 20200703.csv
?       ??? 20200706.csv
?       ??? 20200707.csv
?       ??? 20200708.csv
?       ??? 20200709.csv
?       ??? 20200710.csv
?       ??? 20200713.csv
?       ??? 20200714.csv
?       ??? 20200715.csv
?       ??? 20200716.csv
?       ??? 20200717.csv
?       ??? 20200720.csv
?       ??? 20200721.csv
?       ??? 20200722.csv
?       ??? 20200723.csv
?       ??? 20200724.csv
?       ??? 20200727.csv
?       ??? 20200728.csv
?       ??? 20200729.csv
?       ??? 20200730.csv
?       ??? 20200731.csv
?       ??? alignment_log.csv
??? main.py
??? optimizer.py
??? outputs/
?   ??? <RUN_TIMESTAMP>/
?       ??? daily_weights/
?       ??? run.log
?       ??? run_config.json
?       ??? turnover_logs.csv
??? ??????????.pdf
```

Notes:
- `data/` and `outputs/` are ignored by Git.
- `data_sample/` is intended for repo upload.
