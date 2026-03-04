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
├── .gitignore
├── backtest_engine.py
├── config.py
├── data/
│   └── 20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20/
│       └── *.csv
├── data_loader.py
├── data_sample/
│   └── 20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20/
│       ├── 20200703.csv
│       ├── 20200706.csv
│       ├── 20200707.csv
│       ├── 20200708.csv
│       ├── 20200709.csv
│       ├── 20200710.csv
│       ├── 20200713.csv
│       ├── 20200714.csv
│       ├── 20200715.csv
│       ├── 20200716.csv
│       ├── 20200717.csv
│       ├── 20200720.csv
│       ├── 20200721.csv
│       ├── 20200722.csv
│       ├── 20200723.csv
│       ├── 20200724.csv
│       ├── 20200727.csv
│       ├── 20200728.csv
│       ├── 20200729.csv
│       ├── 20200730.csv
│       ├── 20200731.csv
│       └── alignment_log.csv
├── main.py
├── optimizer.py
├── outputs/
│   └── <RUN_TIMESTAMP>/
│       ├── daily_weights/
│       ├── run.log
│       ├── run_config.json
│       └── turnover_logs.csv
└── 组合优化示例说明文档.pdf
```

Notes:
- `data/` and `outputs/` are ignored by Git.
- `data_sample/` is intended for repo upload.

---

# 组合优化回测框架

## 项目概述

本项目实现了一个支持周期性调仓的投资组合回测系统 。其核心流程包括加载每日截面数据、使用 **CVXPY** 求解带有约束条件的优化问题、在非调仓日自动结转持仓，并生成每日持仓明细及换手率日志 。

## 核心功能

* 
**约束优化**：支持换手率控制、行业中性及市值暴露约束的单期组合优化 。


* **调仓日历**：通过 `config.py` 灵活配置具体的调仓日期。
* **数据导出**：自动导出每日持仓权重及换手率统计。
* **运行管理**：每次运行均会创建以时间戳命名的独立输出文件夹。

## 数据格式

输入文件为以日期命名的 CSV 文件（例如 `YYYYMMDD.csv`）。每个文件必须包含以下核心列：

* `code`：证券代码（唯一标识符）。
* `alpha`：预期收益率信号（因子打分） 。


* `industry_code`：行业分类代码（用于构建行业中性约束的 One-hot 编码） 。


* `mce`：市值因子风险暴露 。


* `wbench`：基准指数成分股权重 。



在数据加载过程中，`alpha`、`mce` 和 `wbench` 中的缺失值将被自动填充为 **0.0**。

## 示例数据

为了方便代码库的上传与测试，`data_sample/` 目录下提供了一组示例数据集。为了避免编码及体积问题，这些 CSV 文件仅保留了部分原始数据行。

若要运行完整的回测，请将完整数据存放在 `data/` 目录下，并确保文件夹名称与配置文件中的路径保持一致。

## 配置说明

您可以直接修改 `config.py` 来更新以下关键参数：

* `DATA_DIR`：原始数据文件夹路径。
* `REBALANCE_DATES`：需要执行调仓的日期列表。
* 
`MAX_WEIGHT`：个股权重上限（例如 0.01 代表 1%） 。


* 
`MAX_MCE_EXPOSURE`：市值因子的主动暴露上限（例如 0.5） 。


* 
`MAX_TURNOVER`：单次调仓的最大双边换手率限制（例如 0.20 代表 20%） 。



每次回测运行后都会自动生成 `run_config.json`，其中记录了该次运行的数据起止日期及相关参数快照。

## 运行命令示例

在终端中执行以下命令启动回测：

```bash
python main.py

```

## 项目结构
```
.
├── .gitignore
├── backtest_engine.py
├── config.py
├── data/
│   └── 20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20/
│       └── *.csv
├── data_loader.py
├── data_sample/
│   └── 20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20/
│       ├── 20200703.csv
│       ├── 20200706.csv
│       ├── 20200707.csv
│       ├── 20200708.csv
│       ├── 20200709.csv
│       ├── 20200710.csv
│       ├── 20200713.csv
│       ├── 20200714.csv
│       ├── 20200715.csv
│       ├── 20200716.csv
│       ├── 20200717.csv
│       ├── 20200720.csv
│       ├── 20200721.csv
│       ├── 20200722.csv
│       ├── 20200723.csv
│       ├── 20200724.csv
│       ├── 20200727.csv
│       ├── 20200728.csv
│       ├── 20200729.csv
│       ├── 20200730.csv
│       ├── 20200731.csv
│       └── alignment_log.csv
├── main.py
├── optimizer.py
├── outputs/
│   └── <RUN_TIMESTAMP>/
│       ├── daily_weights/
│       ├── run.log
│       ├── run_config.json
│       └── turnover_logs.csv
└── 组合优化示例说明文档.pdf
```

## 输出结果

每次运行会在 `outputs/` 目录下创建一个以当前时间戳命名的文件夹，包含以下内容：

* `daily_weights/`：存放在回测期间每日的持仓明细 CSV 文件。
* `turnover_logs.csv`：记录每日的换手率、是否为调仓日以及持仓股票数量。
* `run.log`：完整的运行日志，包含系统状态及错误捕获。
* `run_config.json`：本次回测运行的配置快照。

---

