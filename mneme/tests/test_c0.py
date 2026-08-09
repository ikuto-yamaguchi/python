"""C0 特化エージェントのスモークテスト。"""

import re
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mneme.c0 import (
    C0Agent,
    ConditionMemory,
    ConditionSolver,
    compile_function,
    executable_lines,
    gen_function,
    guard_chains,
    random_search,
    run_with_coverage,
)
from mneme.c0.codegen import satisfying_candidates

SRC = """def f(a, b, c):
    r = 0
    if a > 10:
        r += 1
    elif a == -5:
        r += 2
    else:
        r += 3
    return r
"""


class OracleSolver:
    """テスト用の完全ソルバ(正規表現でパースして正準解を返す)。"""

    def predict(self, text: str) -> int | None:
        m = re.match(r"(!?)\(?\s*(\w+)\s*(==|!=|<=|>=|<|>)\s*(-?\d+)\s*\)?", text)
        if not m:
            return None
        neg, _, op, c = m.group(1) == "!", m.group(2), m.group(3), int(m.group(4))
        return satisfying_candidates(op, c, neg)[0]


def test_gen_functions_compile_and_have_lines():
    for seed in range(10):
        src = gen_function(seed)
        func = compile_function(src)
        assert func(a=0, b=0, c=0) is not None
        assert len(executable_lines(src)) >= 6


def test_coverage_tracer():
    func = compile_function(SRC)
    lines = run_with_coverage(func, {"a": 20, "b": 0, "c": 0})
    assert 4 in lines  # r += 1 (a > 10 の腕)
    assert 6 not in lines and 8 not in lines


def test_guard_chains_elif_negation():
    chains = guard_chains(SRC)
    assert chains[4] == [("a > 10", False)]
    assert chains[6] == [("a > 10", True), ("a == -5", False)]
    assert chains[8] == [("a > 10", True), ("a == -5", True)]


def test_agent_reaches_full_coverage_with_oracle():
    agent = C0Agent(solver=OracleSolver(), seed=0)
    for seed in range(8):
        result = agent.cover(gen_function(seed), budget=80)
        assert result["full"], f"seed={seed} c0={result['c0']:.2f}"


def test_random_search_struggles_with_equality():
    src = "def f(a, b, c):\n    r = 0\n    if a == 742:\n        r += 1\n    return r\n"
    result = random_search(src, budget=200, seed=0)
    assert not result["full"]  # 等値分岐は条件を読まないと実質見つからない


def test_memory_reuse_without_solver():
    torch.manual_seed(0)
    solver = ConditionSolver(latent_dim=32, emb_dim=32, hidden=64)  # 未学習でも符号化は決定的
    memory = ConditionMemory(solver)
    memory.write("a == 742", 742)
    assert memory.lookup("a == 742") == 742
    assert memory.lookup("a == 743") in (None, 742)  # 別条件は原則ミス(実行検証で回収)


def test_solver_smoke_loss_decreases():
    torch.manual_seed(0)
    solver = ConditionSolver(latent_dim=48, emb_dim=32, hidden=96)
    losses = solver.fit(steps=80, batch=32, seed=1)
    assert losses[-1] < losses[0]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok: {name}")
