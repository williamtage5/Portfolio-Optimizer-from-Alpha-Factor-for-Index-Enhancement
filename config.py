# -*- coding: utf-8 -*-
"""
Configuration: paths, optimization constraints, and rebalance schedule.
"""
import os
import json
import re
from datetime import datetime

# ==========================================
# 1. Path configurations
# ==========================================
# Project root directory
PROJECT_ROOT = r"E:\GuotaiHaitong Security\optimizer"

# Input data directory
DATA_DIR = os.path.join(
    PROJECT_ROOT,
    r"data\20260226_144947_raw_lgbm_lambdarank_topk31_mv_100-20-20"
)

# Output base directory
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

# Per-run timestamp (YYYYMMDD_HHMMSS)
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Per-run output directory
RUN_DIR = os.path.join(OUTPUT_DIR, RUN_TIMESTAMP)
DAILY_WEIGHTS_DIR = os.path.join(RUN_DIR, "daily_weights")
TURNOVER_LOG_PATH = os.path.join(RUN_DIR, "turnover_logs.csv")
CONFIG_JSON_PATH = os.path.join(RUN_DIR, "run_config.json")

# Ensure output directories exist
os.makedirs(DAILY_WEIGHTS_DIR, exist_ok=True)

# ==========================================
# 2. Optimization constraints
# ==========================================
# Max weight per stock (e.g., 0.01 means 1%)
MAX_WEIGHT = 0.01

# Max market-cap exposure
MAX_MCE_EXPOSURE = 0.5

# Max turnover per rebalance (e.g., 0.20 means 20%)
MAX_TURNOVER = 0.20

# ==========================================
# 3. Rebalance schedule
# ==========================================
# Dates must match CSV filenames
REBALANCE_DATES = [
    "20200703",
    "20200717",
    "20200731"
]

def get_config_dict():
    '''
    在记录结果的时候把起止日期也一并写在参数配置里面
    '''
    data_dates = list_data_dates() # 调用了同文件中的辅助函数 list_data_dates()。这个函数的作用是扫描你的数据目录（DATA_DIR），找出所有符合日期命名规范的 .csv 文件，并将这些日期提取出来，组合成一个从小到大排好序的列表，赋值给变量 data_dates。
    data_start, data_end, data_count = get_data_date_range(data_dates) # 将上一步获取的日期列表传给 get_data_date_range() 函数。该函数会解析这个列表，提取出回测数据的“起始日期”、“结束日期”以及“数据总天数”。这里使用了 Python 的多变量赋值（解包）特性，将返回的三个结果分别赋给 data_start、data_end 和 data_count。
    return {
        "PROJECT_ROOT": PROJECT_ROOT,
        "DATA_DIR": DATA_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "RUN_TIMESTAMP": RUN_TIMESTAMP,
        "RUN_DIR": RUN_DIR,
        "DAILY_WEIGHTS_DIR": DAILY_WEIGHTS_DIR,
        "TURNOVER_LOG_PATH": TURNOVER_LOG_PATH,
        "DATA_START_DATE": data_start,
        "DATA_END_DATE": data_end,
        "DATA_DATE_COUNT": data_count,
        "MAX_WEIGHT": MAX_WEIGHT,
        "MAX_MCE_EXPOSURE": MAX_MCE_EXPOSURE,
        "MAX_TURNOVER": MAX_TURNOVER,
        "REBALANCE_DATES": REBALANCE_DATES,
    }

def list_data_dates():
    '''
    读取数据目录下的所有csv文件，按照.拆分，得到日期列表
    '''
    try:
        files = os.listdir(DATA_DIR)
    except FileNotFoundError:
        return []
    dates = []
    for name in files:
        if not name.endswith(".csv"):
            continue
        stem = name.split(".")[0]
        if re.fullmatch(r"\d{8}", stem):
            dates.append(stem)
    dates = sorted(dates)
    return dates

def get_data_date_range(dates=None):
    '''
    从日期列表中得到开始日期、结束日期和天数
    '''
    if dates is None:
        dates = list_data_dates()
    if not dates:
        return None, None, 0
    return dates[0], dates[-1], len(dates)

def write_config_json(path=CONFIG_JSON_PATH): # 将当前回测的环境配置（路径、参数限制等）保存为一个易于阅读的 JSON 文件
    config_dict = get_config_dict() # 调用了当前文件中定义的另一个函数 get_config_dict()。这个函数的作用是把所有的全局配置变量（比如项目路径、最大权重限制、调仓日期等）打包成一个 Python 字典（Dictionary），并赋值给变量 config_dict。
    with open(path, "w", encoding="utf-8") as f: # 调用 json 模块的 dump 方法，将 config_dict 这个字典数据序列化并写入到文件对象 f 中。
        json.dump(config_dict, 
                  f, 
                  ensure_ascii=False, # ensure_ascii=False：告诉 json 库不要把非 ASCII 字符（如中文）转义成 \uXXXX 格式，而是直接以原字符输出，保持文件的高可读性。
                  indent=2) # indent=2：设置 JSON 文件的缩进级别为 2 个空格。这能让输出的 JSON 文件结构层次分明，像代码一样方便人类阅读。

if __name__ == "__main__":
    print("=" * 50)
    print("Configuration Check")
    print("=" * 50)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Input data dir: {DATA_DIR}")
    print(f"Output base dir: {OUTPUT_DIR}")
    print(f"Data dir exists: {os.path.exists(DATA_DIR)}")
    print("-" * 50)
    print("Optimization parameters:")
    print(f"  MAX_WEIGHT       = {MAX_WEIGHT}")
    print(f"  MAX_MCE_EXPOSURE = {MAX_MCE_EXPOSURE}")
    print(f"  MAX_TURNOVER     = {MAX_TURNOVER}")
    print("-" * 50)
    print(f"Rebalance dates: {REBALANCE_DATES}")
    print("=" * 50)
