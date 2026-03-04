# -*- coding: utf-8 -*-
"""
Optimization core: build and solve a linear model with CVXPY.
"""
import numpy as np
import pandas as pd
import cvxpy as cp
import config

def run_optimization(df, previous_weights_series, base_turnover):
    '''
    run_optimization 的 Docstring
    
    :param df: 包含股票 Alpha、基准权重、行业因子和市值暴露的 DataFrame。
    :param previous_weights_series: 经过 align_universe 对齐后的前一期持仓权重。
    :param base_turnover: 由停牌或退市导致的被动换手率。
    '''
    n = len(df) # 获取当前股票池中的股票总数。在研报数学模型中，这对应于向量的维度 $N$
    alpha = df["alpha"].values # 提取预期收益率向量（Alpha 打分）。在研报公式中通常记作 $f$ 。 这是优化的目标：在满足约束的前提下，让组合的 $\alpha$ 收益最大化。
    wbench = df["wbench"].values # 提取基准指数的个股权重（Benchmark weights），代码中简写为 wbench 。 用于计算主动权重。
    mce = df["mce"].values # 提取个股的市值因子风险暴露度（Market Cap Exposure） 。研报要求对市值主动暴露进行限制（例如不超过 0.5），以防止组合过度偏向大盘或小盘股 。我觉得这个设置的很随意，可以后续更精确的控制市值暴露的描述。
    x_prev = previous_weights_series.values # 将前一期的持仓权重（Series 类型）转化为 NumPy 数组。

    ind_cols = [c for c in df.columns if c.startswith("ind_")] # 行业的0-1变量均以ind_开头，原来的code列已经被删去
    IE = df[ind_cols].values

    # 1. Decision variables
    w = cp.Variable(n) # 定义决策变量 $w$，代表 $N$ 只股票的主动权重（即策略组合权重减去基准权重） 。
    # 定义两个辅助变量 $b^+$（买入量）和 $b^-$（卖出量），且都必须为非负数 。这是为了处理换手率约束中的绝对值运算，将非线性问题转化为线性规划问题 。
    b_plus = cp.Variable(n, nonneg=True)
    b_minus = cp.Variable(n, nonneg=True)

    # 定义 $x$ 为实际持仓权重。数学关系为：实际权重 = 主动权重 + 基准权重 。
    x = w + wbench

    # 2. Objective 目标：最大化组合的主动超额收益（Alpha）。逻辑是：将每只股票的预期收益率 $\alpha$（即 $f$）与其主动权重 $w$ 相乘并求和 。
    objective = cp.Maximize(alpha @ w)

    # 3. Constraints

    r'''
    1. 总权重中性约束
    **代码：** `cp.abs(cp.sum(w)) <= 0.0001`
    * 
    **实际意义：** 保证你的投资组合是“满仓”且“不加杠杆”的。在研报的模型定义中，$w$ 表示 $N$ 个股票的主动权重，也就是个股在策略组合中的权重减去其在基准指数中的权重，显然有 $\Sigma_{i=1}^{N}w_{i}=0$ 。这意味着你买入超配的股票权重，必须完全来自于你卖出低配的股票权重。
    * **实现方法：** `cp.sum(w)` 将所有股票的主动权重加总。理论上它应该严格等于 0，但在数值优化求解器（如 OSQP 或 SCS）中，要求绝对的 `== 0` 经常会导致无解或计算非常缓慢。因此，采用 `<= 0.0001`（万分之一的容忍度）是一个非常聪明的工程化妥协，既保证了总权重的严谨性，又给求解器留了呼吸的空间。

    2. 行业中性约束
    **代码：** `cp.abs(IE.T @ w) <= 0.005`
    * 
    **实际意义：** 防止策略在某个特定行业上“押重注”。例如，如果中证 500 指数里有 10% 是医药股，那么你的组合里医药股的总权重也必须在 10% 左右。约束条件限定了行业中性，也就说每个行业里面个股的主动权重之和等于 0 。
    * **实现方法：**
    * 
    $IE$ 是行业因子风险暴露矩阵 。因为我们之前用 One-hot 编码将行业转成了 0-1 矩阵，所以 `IE.T @ w` （即矩阵的转置乘以权重向量）的结果，正是**每个行业内所有股票主动权重的加总**。
    * 研报指出，为提高写代码效率，可以把等式约束条件改成不等式约束 $|IE\cdot w|\le\epsilon$，让向量的每个元素取值很小即可 。这里的 `0.005`（千分之五）就是那个 $\epsilon$，允许组合在单个行业上有极小幅度的偏离，从而换取更高的 Alpha 收益。

    3. 市值风险暴露控制
    **代码：** `cp.abs(mce @ w) <= config.MAX_MCE_EXPOSURE`
    * 
    **实际意义：** 在 A 股市场，很多 Alpha 因子（比如反转、换手率因子）天然会偏好小盘股。如果不加限制，优化器为了追求最大的 Alpha，会疯狂买入小微盘股，导致你的组合变成了“小盘股基金”，偏离了基准指数的市值风格。这个约束要求策略组合的市值主动暴露不超过 0.5 。
    * 
    **实现方法：** * MCE 是一个 $1\times N$ 向量，表示个股的市值因子风险暴露度 。
    * `mce @ w` 是两个向量的点乘（Dot Product），计算出的是**整个组合在市值因子上的主动暴露偏离值**。
    * 通过将其绝对值限制在 `MAX_MCE_EXPOSURE`（你在 `config.py` 里设定的是 0.5）以内，确保了组合的市值风格特征与基准指数高度相似。
    
    注意这里还没有考虑到换手的部分。
    '''

    constraints = [
        x >= 0, # 禁止裸卖空：确保组合中每只股票的实际持仓权重不为负数 。
        x <= config.MAX_WEIGHT, # 个股权重上限：限制单只股票在组合中的总权重不超过设定值（如 0.01，即 1%） 。
        cp.abs(cp.sum(w)) <= 0.0001, # 总权重中性：要求所有股票的主动权重之和为 0，即组合的总权重必须等于基准指数的总权重 。
        cp.abs(IE.T @ w) <= 0.005, # 行业中性约束：限制组合在各行业上的主动暴露。
        cp.abs(mce @ w) <= config.MAX_MCE_EXPOSURE, # 市值风险暴露控制：限制组合相对于基准在市值因子上的主动偏离。研报中要求该暴露不超过 0.5 。
    ]

    # 应对第一天没有前一天权重（都为0的情况），如果是初始情况，不加换手率约束计算出一个结果当作第一天的资产配置组合
    is_initial_construction = (np.sum(x_prev) < 1e-4) # x_prev 是你昨天的持仓权重。如果所有股票的旧权重加起来几乎等于 0（小于万分之一），说明你目前是空仓状态。
    # 如果是初次建仓，约束就直接是上面的约束
    # 如果不是初次建仓，约束要加一个换手率约束
    if not is_initial_construction: # 如果不是初次建仓（也就是正常的换仓日），那么我们需要严格控制换手率，进入下面的计算环节。
        available_turnover = config.MAX_TURNOVER - base_turnover # 减去被动换手得到可用的换手额度
        constraints.extend([ 
            x - x_prev == b_plus - b_minus, # 强行定义买入量和卖出量的关系：新权重减去旧权重等于买入量减去卖出量。这个等式确保了 $b^+$ 和 $b^-$ 正确地反映了每只股票的买入和卖出情况。
            # 在 cvxpy（凸优化库）里，这里的 == 和 <= 不是在做计算，而是在给优化器“立规矩”（写约束条件）。
            # 数学上是前后两期的差的绝对值要小于一个值，这是一个V的折线，不好求导和计算
            cp.sum(b_plus + b_minus) <= available_turnover,
        ])

        r'''
        `x - x_prev == b_plus - b_minus`

        **这句规矩的意思是：真实权重的变化量，必须严格等于“买入量”减去“卖出量”。**

        * `x` 是今天准备调整到的目标权重，`x_prev` 是昨天的老权重。
        * `b_plus` 代表**买入增加的权重**（必须 $\ge 0$）。
        * `b_minus` 代表**卖出减少的权重**（必须 $\ge 0$）。

        **举个极端的例子，优化器在算某只股票 A 时，会面临三种情况：**

        1. **我想加仓：** 昨天权重是 1%，今天我想买到 3%。
        * 变化量 `x - x_prev` = 3% - 1% = **+2%**
        * 为了满足这个等式，优化器会自动分配：`b_plus = 2%`，`b_minus = 0%`。
        * 完美符合：2% = 2% - 0%


        2. **我想减仓：** 昨天权重是 3%，今天我想减到 1%。
        * 变化量 `x - x_prev` = 1% - 3% = **-2%**
        * 为了满足等式，优化器会自动分配：`b_plus = 0%`，`b_minus = 2%`。
        * 完美符合：-2% = 0% - 2%


        3. **我按兵不动：** 昨天权重是 2%，今天还是 2%。
        * 变化量 `x - x_prev` = 2% - 2% = **0%**
        * 优化器会自动分配：`b_plus = 0%`，`b_minus = 0%`。
        * 完美符合：0% = 0% - 0%



        **总结：** 这一步就是强行定义出了纯粹的“买入动作（`b_plus`）”和“卖出动作（`b_minus`）”。

        ---

        第二句规矩：`cp.sum(b_plus + b_minus) <= available_turnover`

        **这句规矩的意思是：全市场所有股票的“总买入量”加上“总卖出量”，必须小于等于可用换手率额度。**

        在第一步里，我们已经把每一只股票的买卖动作分离出来了。

        * 注意看，这里是 `b_plus + b_minus` （**加号！**）。
        * 不管你是买（情况1，2%+0%=2%），还是卖（情况2，0%+2%=2%），只要你动了这只股票，你就会产生 `2%` 的真实交易额（绝对值）。
        * `cp.sum(...)` 就是把全市场几千只股票的这种真实交易额全部累加起来。
        * `<= available_turnover` 就是给总交易额踩刹车：你随便怎么买卖，但总折腾的量不能超过我的预算（比如剩余的 18% 换手率）。
        
        '''
    else:
        print("   -> 检测到空仓状态，初始建仓不加换手率约束求解")

    # 4. Solve 打包成正确的格式求解，如果一个求解不出来则尝试其他求解器。
    prob = cp.Problem(objective, constraints)
    try:
        # 研报中指出，这类组合优化问题属于标准的凸二次规划问题，有非常成熟和快速的算法求解 。考虑到求解凸二次规划算法的高效性，这类问题通常能在极短时间内得出精确解 。
        prob.solve(solver=cp.OSQP, 
                   max_iter=60000, 
                   eps_abs=1e-4, 
                   eps_rel=1e-4) # 它把你前面定义的“最大化 Alpha 目标（objective）”和“所有的规矩（constraints，包括行业、市值、换手率限制等）”打包在一起，生成一个标准的优化问题对象 prob。
    except Exception as e:
        print(f"OSQP 求解器出错 error: {e}. 尝试 SCS 求解器...")
        try:
            prob.solve(solver=cp.SCS, max_iters=60000)
        except Exception as e2:
            print(f"SCS 求解器出错 error: {e2}")
            pass

    # 5. Parse results 解析结果, 检查作业：算完之后，检查 prob.status（求解状态）。
    if prob.status not in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]: # 如果状态不是 OPTIMAL（完美最优解）或者 OPTIMAL_INACCURATE（找到了解，但精度稍微差一丢丢），说明求解失败了（最常见的是 INFEASIBLE，意思是你的约束条件互相打架，比如既要求不买股票，又要求满仓）。
        print(f"优化失败。求解器状态为: {prob.status}")
        # 如果失败，直接返回一个带有 False 标签和空字典的失败报告。我们在 backtest_engine.py 里看到过，一旦收到 False，引擎就会保持昨天的旧持仓不动。
        return {
            "success": False,
            "weights": {},
            "turnover": 0.0,
            "status": prob.status,
        }

    # 如果能够成功求解
    final_weights = x.value # 提取答案：x.value 就是求解器算出来的、每只股票的最终持仓权重（一个 NumPy 数组）。
    final_weights[final_weights < 1e-6] = 0.0 # 抹除浮点数噪音：计算机算数学题会有微小的精度误差，比如它可能算出某只股票的权重是 0.0000000012（本质上就是不想买）。这行代码把所有小于 1e-6（百万分之一）的微小权重全部强制归零，防止生成一大堆毫无意义的“灰尘仓位”。
    codes = df.index.tolist() # 字典化：df.index 里面存的是股票代码。这里使用了一个优雅的 Python 字典推导式，把股票代码和刚刚算出来的权重一一对应起来。
    weights_dict = {
        # 顺序对应股票，并且舍弃掉权重为 0 的股票：
        codes[i]: float(final_weights[i]) for i in range(n) if final_weights[i] > 0 # 剔除 0 权重：if final_weights[i] > 0 保证了字典里只存真正买入的股票。这不仅节省内存，也是后面引擎进行交易记录的标准格式。
    }

    # 由于舍弃掉了灰尘仓位，需要再次计算真实的换手率
    # 如果是初始化仓位，则记换手率为1
    if is_initial_construction:
        actual_turnover = 1.0
    else:
        # 日常调仓：把今天算出的新权重（final_weights）减去昨天的旧权重（x_prev），取绝对值并求和，这就是模型主动交易的量。然后再加上我们在前面算出来的、因为退市停牌导致的被动换手率（base_turnover），得到今天真正的、包含所有动作的总换手率 actual_turnover。
        actual_turnover = float(np.sum(np.abs(final_weights - x_prev)) + base_turnover)

    return {
        "success": True,
        "weights": weights_dict,
        "turnover": actual_turnover,
        "status": prob.status,
        "objective_value": float(prob.value),
    }

if __name__ == "__main__":
    print("=" * 50)
    print("Optimizer Test - Real Data")
    print("=" * 50)
    from data_loader import load_data
    test_date = config.REBALANCE_DATES[0]
    print(f"Loading {test_date}.csv for optimization...")
    try:
        df, _ = load_data(test_date)
        prev_weights_mock = pd.Series(0.0, index=df.index)
        res = run_optimization(df, prev_weights_mock, base_turnover=0.0)
        print("-" * 50)
        print(f"Status: {res['status']}")
        print(f"Success: {res['success']}")
        if res["success"]:
            print(f"Objective value: {res['objective_value']:.6f}")
            print(f"Actual turnover: {res['turnover']:.4f}")
            print(f"Selected holdings: {len(res['weights'])}")
            sum_w = sum(res["weights"].values())
            max_w = max(res["weights"].values())
            print(f"Sum of weights: {sum_w:.4f} (expected ~1.0000)")
            print(f"Max single weight: {max_w:.4f} (limit {config.MAX_WEIGHT})")
    except Exception as e:
        print(f"Test error: {e}")
    print("=" * 50)
