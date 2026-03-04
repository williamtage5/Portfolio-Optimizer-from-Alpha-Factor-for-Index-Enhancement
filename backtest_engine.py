# -*- coding: utf-8 -*-
"""
Backtest engine: timeline loop and state machine, controls rebalance and holdings carryover.
"""
import os
import pandas as pd
import config
from data_loader import load_data, align_universe
from optimizer import run_optimization

class BacktestEngine: # 这就相当于画了一张“回测引擎”的设计图纸。在这张图纸里，规定了这个引擎应该具备哪些属性（比如内部记录表）和功能（比如上一问提到的 run() 方法）。
    def __init__(self):
        """
        在 Python 里，__init__ 是一个非常特殊的魔法方法（双下划线开头和结尾）。当有人拿着设计图纸真正造出一台“回测引擎”的瞬间，这个方法就会被自动触发运行一次。self：代表的是“引擎本身”。就像你对自己说“我的手臂”、“我的大脑”一样，程序里用 self.xxx 来表示“属于这个引擎自己的数据”。
        """
        # Current holdings: {code: weight}
        self.current_holdings = {} # 在引擎启动的瞬间，给它发一个空白的字典 {}（Dictionary），命名为 self.current_holdings。用来记录当前投资组合里有哪些股票以及它们的权重。
        # Daily turnover records for final log output
        self.turnover_records = [] # 创建换手率流水账：在引擎启动瞬间，给它发一个空白的列表 []（List），命名为 self.turnover_records。回测的每一天，不管调没调仓，都会把当天的换手率、是否是调仓日等信息打包塞进这个列表里。回测结束时，直接把这个列表转换成数据表（DataFrame）并保存为 turnover_logs.csv。

    def get_all_dates(self):
        """
        获取数据目录下的所有日期（按文件名解析），并返回一个排序好的列表。
        """
        files = os.listdir(config.DATA_DIR)
        dates = sorted([f.split(".")[0] for f in files if f.endswith(".csv")])
        return dates

    def save_daily_weights(self, date):
        """
        保存时间区间的每一天的权重
        """
        if not self.current_holdings: # 安全性检查：检查当前持仓字典 self.current_holdings 是否为空。逻辑意义：如果还没开始建仓（例如回测的第一天之前），或者优化器没选出任何股票，就直接退出函数，不生成空文件。
            return  # skip if empty (e.g., before first build)

        out_path = os.path.join(config.DAILY_WEIGHTS_DIR, f"{date}.csv") # 确定存储路径
        df_out = pd.DataFrame.from_dict(self.current_holdings, orient="index", columns=["weight"]) # 数据格式转换：将 Python 字典 {股票代码: 权重} 转换为 Pandas 的 DataFrame 表格对象。orient="index"：表示将字典的键（股票代码）作为表格的行索引。columns=["weight"]：将字典的值（权重数值）那一列命名为 "weight"。
        df_out.index.name = "code" # 明确给表格的第一列（即存储股票代码的索引列）起个名字叫 "code"。
        df_out.to_csv(out_path)

    def run(self):
        """
        Run the backtest main loop.
        """
        dates = self.get_all_dates() # 扫描数据文件夹，获取所有按日期命名的 CSV 文件名，并按时间先后排好序。 请使用我（这个引擎自身）内部自带的那个名为 get_all_dates 的工具。”get_all_dates() （如果不加 self.）：如果你直接这么写，Python 会认为这是一个游离在类外面的全局函数（就像内置的 print() 或者 len() 一样）。
        print("=" * 50)
        print(f"时间区间一共有 {len(dates)} 天")
        print(f"自己设定的调仓日期是: {config.REBALANCE_DATES}")
        print("=" * 50)

        for date in dates:
            print(f"正在处理[{date}] ...")

            if date in config.REBALANCE_DATES:
                print("  -> 判断这一天是调仓日，开始进行优化计算...")
                try:
                    # 1. 从硬盘读取今天的行情和因子数据（如 Alpha 打分、行业代码等） 。
                    df, _ = load_data(date) 

                    # 2. 被动换手：如果昨天持有的股票今天退市或不在池子里了，计算这部分“被迫卖出”产生的换手率 base_turnover
                    # 根据今天股票池的情况，迁移昨天的持仓，方便构建优化模型的输入。
                    aligned_prev_weights, base_turnover = align_universe(df, self.current_holdings)

                    # 3. 在控制行业中性、市值暴露和换手率的前提下，寻找 Alpha 最大的组合 。
                    res = run_optimization(df, aligned_prev_weights, base_turnover)
                    # 如果优化成功，self.current_holdings = res["weights"] 会把引擎的“记忆”更新为今天算出来的最新权重。
                    if res["success"]:
                        # 4. Update state
                        self.current_holdings = res["weights"]
                        turnover = res["turnover"] # 总换手率 = 被动换手率 + 主动换手率
                        print(f"  -> 优化计算成功。总换手率为: {turnover:.4f}, 当前的持仓情况是: {len(self.current_holdings)}")
                    else:
                        print(f"  -> [WARN] 优化计算失败。失败状态为: {res['status']}。保险起见，取上一期的持仓作为当天的持仓情况。")
                        turnover = 0.0 # 优化失败了，就不换仓了，继续拿着上一期的持仓过日子，所以当天的换手率就是 0。
                except Exception as e: # 如果计算过程中数学模型崩溃或代码报错，程序不会死掉，而是打印错误信息并保持原有持仓不变（turnover = 0.0），确保回测能跑完
                    print(f"  -> [ERROR] 出现未知错误: {e}。保险起见，取上一期的持仓作为当天的持仓情况。")
                    turnover = 0.0
            else:
                print("  -> 非调仓日，不用进行运筹优化计算，资产组合为前一日的持仓情况。")
                turnover = 0.0

            self.turnover_records.append({
                "date": date,
                "turnover": turnover,
                "is_rebalance_day": date in config.REBALANCE_DATES,
                "holdings_count": len(self.current_holdings),
            })

            self.save_daily_weights(date)

        # Save turnover log
        log_df = pd.DataFrame(self.turnover_records)
        log_df.to_csv(config.TURNOVER_LOG_PATH, index=False)
        print("=" * 50)
        print("时间段运筹优化求解持仓完成")
        print(f"时间区间的每天的权重保存在: {config.DAILY_WEIGHTS_DIR}")
        print(f"换手率信息保存在: {config.TURNOVER_LOG_PATH}")
        print("=" * 50)

if __name__ == "__main__":
    engine = BacktestEngine()
    engine.run()
