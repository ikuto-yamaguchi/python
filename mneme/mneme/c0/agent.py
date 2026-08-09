"""C0 カバレッジ達成エージェント。

ループ: 未カバー行を選ぶ → 到達に必要な条件列を観測 → 各条件の充足値を
「記憶 → ソルバ → 乱数プローブ」の順で提案 → 実行してカバレッジを観測 →
成功した (条件, 値) を外部記憶へ書き込む。

- 記憶ヒットもソルバも使えない場合の乱数プローブは「条件テキストを
  読まない」ベースラインに相当し、等値条件(x == c)にはほぼ当たらない。
- 記憶は関数をまたいで持ち越すため、スイートを進むほど勾配ゼロで
  賢くなる(経験の蓄積 = 学習ではなく記憶)。
"""

from __future__ import annotations

import itertools
import random

import torch
import torch.nn.functional as F

from .coverage import compile_function, executable_lines, guard_chains, run_with_coverage
from .solver import ConditionSolver


class ConditionMemory:
    """(条件テキストの潜在ベクトル, 充足値) の外部エピソード記憶。"""

    def __init__(self, solver: ConditionSolver, threshold: float = 0.999):
        self.solver = solver
        self.threshold = threshold
        self.keys = torch.empty(0, solver.offset_head.in_features)
        self.values: list[int] = []
        self.texts: list[str] = []
        self.hits = 0

    def __len__(self) -> int:
        return len(self.values)

    def lookup(self, text: str) -> int | None:
        if not self.values:
            return None
        q = F.normalize(self.solver.encode([text]), dim=-1)
        k = F.normalize(self.keys, dim=-1)
        sims = (q @ k.T).squeeze(0)
        best = int(sims.argmax())
        if float(sims[best]) >= self.threshold:
            self.hits += 1
            return self.values[best]
        return None

    def write(self, text: str, value: int) -> None:
        if text in self.texts:
            return
        self.keys = torch.cat([self.keys, self.solver.encode([text])], dim=0)
        self.values.append(value)
        self.texts.append(text)


class C0Agent:
    """未カバー行を潰していく実行フィードバックループ。"""

    def __init__(
        self,
        solver: ConditionSolver | None = None,
        memory: ConditionMemory | None = None,
        seed: int = 0,
        max_combos_per_line: int = 24,
    ):
        self.solver = solver
        self.memory = memory
        self.rng = random.Random(seed)
        self.max_combos = max_combos_per_line

    def _var_of(self, cond: str) -> str:
        return cond.split()[0]

    def _candidates(self, cond: str, negated: bool) -> list[int]:
        """1 条件に対する候補値リスト(境界のずれに備え ±1 も試す)。"""
        text = f"!({cond})" if negated else cond
        vals: list[int] = []
        if self.memory is not None:
            m = self.memory.lookup(text)
            if m is not None:
                vals.append(m)
        if self.solver is not None:
            v = self.solver.predict(text)
            if v is not None:
                vals += [v, v + 1, v - 1]
        if not vals:  # 条件を「読まない」提案 = 乱数プローブ
            vals = [self.rng.randint(-999, 999) for _ in range(3)]
        seen: set[int] = set()
        return [v for v in vals if not (v in seen or seen.add(v))]

    def _plan(self, chain: list[tuple[str, bool]]) -> list[dict[str, int]]:
        """条件列から試行する入力割り当ての列を作る。"""
        by_var: dict[str, list[int]] = {}
        for cond, neg in chain:
            var = self._var_of(cond)
            by_var.setdefault(var, [])
            by_var[var] += self._candidates(cond, neg)
        variables = list(by_var)
        combos = itertools.product(*(by_var[v] for v in variables))
        return [
            dict(zip(variables, combo))
            for combo in itertools.islice(combos, self.max_combos)
        ]

    def cover(self, src: str, budget: int = 80) -> dict:
        func = compile_function(src)
        target_lines = executable_lines(src)
        chains = guard_chains(src)
        argnames = ["a", "b", "c"]

        covered = run_with_coverage(func, {n: 0 for n in argnames})
        executions = 1
        plans: dict[int, list[dict[str, int]]] = {}
        attempts: dict[int, int] = {}
        dead: set[int] = set()

        while executions < budget:
            uncovered = target_lines - covered - dead
            if not uncovered:
                break
            # 深い(ガードが多い)行を優先: 到達の途中で浅い行も踏む
            line = max(uncovered, key=lambda ln: (len(chains[ln]), -ln))
            if line not in plans:
                plans[line] = self._plan(chains[line])
                attempts[line] = 0
            if attempts[line] >= len(plans[line]):
                dead.add(line)
                continue
            assignment = plans[line][attempts[line]]
            attempts[line] += 1
            kwargs = {n: 0 for n in argnames} | assignment
            covered |= run_with_coverage(func, kwargs)
            executions += 1
            if line in covered and self.memory is not None:
                for cond, neg in chains[line]:
                    text = f"!({cond})" if neg else cond
                    self.memory.write(text, kwargs[self._var_of(cond)])

        c0 = len(covered & target_lines) / len(target_lines)
        return {"c0": c0, "executions": executions, "full": c0 == 1.0}


def random_search(src: str, budget: int = 2000, seed: int = 0) -> dict:
    """条件を読まないランダム探索ベースライン。"""
    rng = random.Random(seed)
    func = compile_function(src)
    target_lines = executable_lines(src)
    covered: set[int] = set()
    executions = 0
    while executions < budget:
        if target_lines <= covered:
            break
        kwargs = {n: rng.randint(-999, 999) for n in ["a", "b", "c"]}
        covered |= run_with_coverage(func, kwargs)
        executions += 1
    c0 = len(covered & target_lines) / len(target_lines)
    return {"c0": c0, "executions": executions, "full": c0 == 1.0}
