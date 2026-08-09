"""実験 3: C0(命令網羅)テスト生成特化エージェント。

「閉じたインターフェース + 極小モデル + 外部記憶 + 実行フィードバック」で、
1B 級の汎用モデルなしに C0 = 100% を達成できるかを検証する。

比較する 4 変種(いずれも同じ実行フィードバックループ):
  1. ランダム探索       : 条件を読まない(予算 2000 実行/関数)
  2. エージェント(素)  : ソルバなし・記憶なし = 乱数プローブのみ
  3. + ソルバ           : 条件バイト列を読む 0.7M パラメータの知能コア
  4. + ソルバ + 記憶    : 解けた条件を関数横断で記憶(勾配ゼロの経験蓄積)

使い方:
    python experiments/run_c0_benchmark.py
"""

import statistics
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mneme.c0 import C0Agent, ConditionMemory, ConditionSolver, gen_function, random_search

N_FUNCS = 40
AGENT_BUDGET = 80
RANDOM_BUDGET = 2000


def summarize(name: str, results: list[dict]) -> str:
    c0 = statistics.mean(r["c0"] for r in results)
    execs = statistics.mean(r["executions"] for r in results)
    full = sum(r["full"] for r in results)
    return f"{name:24s} | C0平均 {c0:6.1%} | 100%達成 {full:2d}/{len(results)} | 平均実行回数 {execs:7.1f}"


def main() -> None:
    torch.manual_seed(0)
    suite = [gen_function(seed) for seed in range(N_FUNCS)]

    print("=== 知能コア(条件充足ソルバ)を学習 ===")
    solver = ConditionSolver()
    t0 = time.time()
    solver.fit(steps=2500, batch=128, seed=0, verbose=True)
    acc = solver.accuracy(n=500)
    print(
        f"学習 {time.time() - t0:.0f}s / パラメータ数 {solver.param_count():,}"
        f" / ホールドアウト条件の充足率 {acc:.1%}\n"
    )

    rows = []

    results = [random_search(src, budget=RANDOM_BUDGET, seed=i) for i, src in enumerate(suite)]
    rows.append(("ランダム探索(2000実行)", results))
    print(summarize(*rows[-1]))

    agent = C0Agent(solver=None, memory=None, seed=0)
    results = [agent.cover(src, budget=AGENT_BUDGET) for src in suite]
    rows.append(("エージェント(素)", results))
    print(summarize(*rows[-1]))

    agent = C0Agent(solver=solver, memory=None, seed=0)
    solver_results = [agent.cover(src, budget=AGENT_BUDGET) for src in suite]
    rows.append(("+ ソルバ", solver_results))
    print(summarize(*rows[-1]))

    memory = ConditionMemory(solver)
    agent = C0Agent(solver=solver, memory=memory, seed=0)
    results = [agent.cover(src, budget=AGENT_BUDGET) for src in suite]
    rows.append(("+ ソルバ + 記憶", results))
    print(summarize(*rows[-1]))

    saved = sum(
        s["executions"] - m["executions"] for s, m in zip(solver_results, results)
    )
    print(
        f"\n記憶の効果(同一関数のペア比較): 総実行回数 "
        f"{sum(r['executions'] for r in solver_results)} → "
        f"{sum(r['executions'] for r in results)}(削減 {saved} 回)"
        f" / 記憶 {len(memory)} 件, ヒット {memory.hits} 回, 勾配 0 step"
    )

    print("\n=== 結果まとめ(Markdown) ===")
    print("| 方式 | C0 平均 | 100% 達成 | 平均実行回数 |")
    print("|---|---:|---:|---:|")
    for name, results in rows:
        c0 = statistics.mean(r["c0"] for r in results)
        execs = statistics.mean(r["executions"] for r in results)
        full = sum(r["full"] for r in results)
        print(f"| {name} | {c0:.1%} | {full}/{len(results)} | {execs:.1f} |")


if __name__ == "__main__":
    main()
