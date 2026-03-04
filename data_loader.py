# -*- coding: utf-8 -*-
"""
Data loading and processing: read cross-sectional features, align stock universe.
"""
import os
import pandas as pd
import numpy as np
import config

def load_data(date_str):
    """
    Read CSV for a given date, extract required fields, and one-hot encode industries.
    """
    file_path = os.path.join(config.DATA_DIR, f"{date_str}.csv") # 拼接路径
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    df = pd.read_csv(file_path)

    required_cols = ["code", "alpha", "industry_code", "mce", "wbench"] # 数据中的 industry_name 不读取
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in {file_path}: {col}")

    df = df[required_cols].copy()
    df[["alpha", "mce", "wbench"]] = df[["alpha", "mce", "wbench"]].fillna(0.0) # 将这三个数值列中的缺失值（NaN）填充为 0.0，确保后续数学计算不会报错 。
    df.set_index("code", inplace=True) # 将股票代码设为索引，方便后续按代码进行数据对齐 。

    industry_dummies = pd.get_dummies(df["industry_code"], prefix="ind", dtype=float) # 将分类的行业代码转换为多个二进制列 。相当于通过扩充行数来使用0-1变量表示行业。
    industry_cols = industry_dummies.columns.tolist() # 提取所有新生成的行业列名（即 $IE$ 矩阵的组成部分） 
    df = pd.concat([df, industry_dummies], axis=1) # 把原来的 DataFrame 和新生成的行业哑变量 DataFrame 按列（axis=1）拼接在一起，形成一个新的 DataFrame。这个新的 DataFrame 既包含了原来的数值特征（如 alpha、mce、wbench），也包含了行业的二进制特征（ind_XXX 列）。
    # 原有的 industry_code 列并没有被删掉，而是在拼接的过程中没有被选中。
    return df, industry_cols

def align_universe(current_df, previous_weights_dict):
    """
    计算被迫换手 + 把“昨天的持仓”按照“今天的名单”重新排好队，这个旧的权重是输入到资产配置优化的基础
    align_universe 的作用就是把“昨天的持仓”按照“今天的名单”重新排好队，并算出那些“消失的股票”给你带来了多少被迫的换手 。是持仓情况的对比，而不是股票池做差集。
    """
    if not previous_weights_dict: # 检查是否有旧持仓。如果你是回测的第一天，这个字典是空的。
        aligned_prev_weights = pd.Series(0.0, index=current_df.index) # ：创建一个全为 0.0 的向量（Series），长度和索引与今天的股票池（current_df）完全一致，并返回换手率为 0.0。
        return aligned_prev_weights, 0.0
    # 分别获取“今天名单里的股票”和“昨天手里持有的股票”，并将它们转换成 Python 的集合（set）。
    current_stocks = set(current_df.index)
    prev_stocks = set(previous_weights_dict.keys())

    removed_stocks = prev_stocks - current_stocks # 集合运算（比如求差集）速度极快，适合处理成千上万只股票。
    forced_turnover = sum(previous_weights_dict[code] for code in removed_stocks) # 计算被动换手：把这些消失股票的权重加起来。
    # 迁移旧权重：按照“今天的名单”重新排好队。对于那些昨天持有但今天不在名单里的股票，默认权重为 0.0。
    aligned_prev_weights = pd.Series(
        [previous_weights_dict.get(code, 0.0) for code in current_df.index],
        index=current_df.index,
    )

    return aligned_prev_weights, forced_turnover

if __name__ == "__main__":
    print("=" * 50)
    print("Data Loader Test")
    print("=" * 50)
    test_date = config.REBALANCE_DATES[0]
    print(f"1. Loading {test_date}.csv ...")
    try:
        df, ind_cols = load_data(test_date)
        print(f"   Loaded: {len(df)} stocks, {len(ind_cols)} industries")
        print("   Preview:")
        print(df.head(2))
        print("-" * 50)
        print("2. Testing universe alignment...")
        mock_prev_weights = {
            "000001.SZ": 0.005,
            "000002.SZ": 0.008,
            "999999.SZ": 0.012,
        }
        print(f"   Mock prev holdings: {mock_prev_weights}")
        aligned_weights, f_turnover = align_universe(df, mock_prev_weights)
        print(f"   Forced turnover from removals: {f_turnover:.4f}")
        print(f"   Prev weight for 000001.SZ: {aligned_weights.get('000001.SZ', 'Error')}" )
        print(f"   Prev weight for 000004.SZ: {aligned_weights.get('000004.SZ', 'Error')}" )
    except Exception as e:
        print(f"   Test error: {e}")
    print("=" * 50)
