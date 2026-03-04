# -*- coding: utf-8 -*-
"""
Project entry: wiring config and engine, set up logging, run full backtest.
"""
import os
import logging
import pandas as pd
from backtest_engine import BacktestEngine
import config

# ==========================================
# 1. Global logging
# ==========================================
log_file = os.path.join(config.RUN_DIR, "run.log") # 拼接一个完整的路径决定日志文件保存在哪里

# Log to both console and file
logging.basicConfig(
    level=logging.INFO, # Python 的日志分为五个严重等级（从低到高）：DEBUG -> INFO -> WARNING -> ERROR -> CRITICAL。设置为 INFO 意味着，所有 INFO 及以上级别的日志都会被记录，而那些用来排查底层代码逻辑的极度琐碎的 DEBUG 级信息会被静音，防止日志文件被塞满垃圾信息。
    format='%(asctime)s - [%(levelname)s] - %(message)s', # 设定每一行日志的“长相”（格式化字符串）。 %(asctime)s：自动抓取当前精确到毫秒的时间。%(levelname)s：自动填入这条日志的级别（如 INFO、ERROR）。%(message)s：你在代码里实际写的那句提示语。
    handlers=[ # handlers 就是“处理器”，它决定了日志要被发送到哪些终端。 一个决定写入，一个决定打印出
        logging.FileHandler(log_file, encoding="utf-8"), # 把日志永久写入本地硬盘。它拿到了第一行生成的 log_file 路径，并在后台默默地把每一条生成的日志文本追加写进去。encoding="utf-8" 是为了防止你在写中文备注时出现乱码。
        logging.StreamHandler() # 把日志实时打印在控制台（屏幕）上。
    ]
)

def main():
    logging.info("=" * 50)
    logging.info("人为设定调仓日得到资产配置...")
    logging.info(f"数据输入目录（因子值）: {config.DATA_DIR}")
    logging.info(f"调仓结果存储在: {config.RUN_DIR}")
    logging.info("=" * 50)

    try:
        # 2. Persist this run configuration
        config.write_config_json()

        # 3. Instantiate engine and run
        engine = BacktestEngine() # 实例化（创建）回测引擎对象。这会触发 backtest_engine.py 中的 __init__ 方法，准备好记录持仓和换手率的内部变量。
        logging.info("开始进行因子值到资产组合的回测...")

        # Core loop (backtest_engine uses print for progress output)
        engine.run()

        # 4. Read results and compute simple stats
        log_path = config.TURNOVER_LOG_PATH
        if os.path.exists(log_path):
            # 到这里已经生成了每日的持仓数据和换手率数据，做一些简单的统计打印出来
            df_log = pd.read_csv(log_path)

            # 从日志中过滤掉不调仓（换手率为 0）的日子，只保留真正的“调仓大日子”，并计算总调仓次数。
            rebalance_days = df_log[df_log['is_rebalance_day'] == True].copy()
            total_rebalances = len(rebalance_days)

            # Average turnover (exclude the first day 100% turnover)
            if total_rebalances > 1: # 计算平均换手率
                avg_turnover = rebalance_days.iloc[1:]['turnover'].mean() # 由于第一天建仓（从 0 到满仓）换手率通常是 $100\%$，会极大拉高均值。这里使用 iloc[1:] 剔除第一天，计算后续日常调仓的平均换手压力。
            else:
                avg_turnover = rebalance_days['turnover'].mean() if total_rebalances > 0 else 0.0 # 没啥意义，保护性编程

            logging.info("=" * 50)
            logging.info("Backtest finished")
            logging.info(f"总调仓次数是: {total_rebalances}")
            logging.info(f"平均调仓比例是（除去第一天的初始化）: {avg_turnover:.4f}")
            logging.info(f"日志文件记录在: {log_file}")
            logging.info("=" * 50)
        else:
            logging.warning("Turnover log not found; stats skipped.")

    except Exception as e:
        # 5. Capture fatal error and stack trace
        logging.error(f"Fatal error during backtest: {e}", exc_info=True)

if __name__ == "__main__":
    main()
