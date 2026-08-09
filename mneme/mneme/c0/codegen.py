"""C0 テスト対象の合成関数生成(閉じた部分言語)。

対象言語: 整数引数 a, b, c と「変数 比較演算子 定数」の条件だけからなる
if/elif/else 木。各分岐アームには到達を記録する文(r += k)が入るため、
C0(命令網羅)= 全アームの実行と等価になる。

生成時に全アームの到達可能性(パス制約の充足可能性)を検査するので、
生成された関数は必ず C0 = 100% を達成できる。
"""

from __future__ import annotations

import itertools
import random

OPS = ["==", "!=", "<", "<=", ">", ">="]
NEG = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}
DOMAIN_CONSTS = [0, 1, -1, 7, 42, 100, -100, 255, 500, -500]


def eval_op(v: int, op: str, c: int) -> bool:
    return {
        "==": v == c,
        "!=": v != c,
        "<": v < c,
        "<=": v <= c,
        ">": v > c,
        ">=": v >= c,
    }[op]


def satisfying_candidates(op: str, c: int, negated: bool) -> list[int]:
    """条件を満たす代表値(境界値)の候補。先頭が第一候補。"""
    if negated:
        op = NEG[op]
    return {
        "==": [c],
        "!=": [c + 1, c - 1],
        ">": [c + 1],
        ">=": [c],
        "<": [c - 1],
        "<=": [c],
    }[op]


def _chain_satisfiable(constraints: list[tuple[str, str, int, bool]]) -> bool:
    """同一パス上の制約(var, op, c, negated)の連言が充足可能か。

    制約は単変数比較のみなので、境界値 ±1 の全候補走査で厳密に判定できる。
    """
    by_var: dict[str, list[tuple[str, int, bool]]] = {}
    for var, op, c, neg in constraints:
        by_var.setdefault(var, []).append((op, c, neg))
    for conds in by_var.values():
        candidates: set[int] = set()
        for op, c, neg in conds:
            for v in satisfying_candidates(op, c, neg):
                candidates.update((v - 1, v, v + 1))
        ok = any(
            all(eval_op(v, op, c) != neg for op, c, neg in conds)
            for v in candidates
        )
        if not ok:
            return False
    return True


def _gen_cond(rng: random.Random) -> tuple[str, int]:
    op = rng.choice(OPS)
    c = rng.choice(DOMAIN_CONSTS) if rng.random() < 0.4 else rng.randint(-999, 999)
    return op, c


def _gen_chain(
    rng: random.Random,
    var: str,
    nest_var: str | None,
    path: list[tuple[str, str, int, bool]],
    counter: "itertools.count[int]",
    indent: str,
) -> list[str]:
    """1 つの if/elif/else 連鎖を生成する。全アームの充足可能性を保証する。"""
    for _ in range(200):
        op1, c1 = _gen_cond(rng)
        use_elif = rng.random() < 0.5
        op2, c2 = _gen_cond(rng) if use_elif else (None, None)

        arm1 = path + [(var, op1, c1, False)]
        arms = [arm1]
        if use_elif:
            arm2 = path + [(var, op1, c1, True), (var, op2, c2, False)]
            arm_else = path + [(var, op1, c1, True), (var, op2, c2, True)]
            arms += [arm2, arm_else]
        else:
            arm_else = path + [(var, op1, c1, True)]
            arms.append(arm_else)
        if all(_chain_satisfiable(a) for a in arms):
            break
    else:
        raise RuntimeError("充足可能な分岐を生成できませんでした")

    def body(arm_path: list[tuple[str, str, int, bool]]) -> list[str]:
        lines = [f"{indent}    r += {next(counter)}"]
        if nest_var is not None and rng.random() < 0.6:
            lines += _gen_chain(rng, nest_var, None, arm_path, counter, indent + "    ")
        return lines

    out = [f"{indent}if {var} {op1} {c1}:"]
    out += body(arm1)
    if use_elif:
        out.append(f"{indent}elif {var} {op2} {c2}:")
        out += body(arm2)
    out.append(f"{indent}else:")
    out += body(arm_else)
    return out


def gen_function(seed: int) -> str:
    """合成対象関数のソースコードを返す。

    パス上の各変数は高々 1 つの if/elif 連鎖でしか使われないため、
    パス制約は「変数ごとに独立した単変数制約の集合」になる。
    """
    rng = random.Random(seed)
    counter = itertools.count(1)
    lines = ["def f(a, b, c):", "    r = 0"]
    lines += _gen_chain(rng, "a", "b", [], counter, "    ")
    lines += _gen_chain(rng, "c", "b", [], counter, "    ")
    lines.append("    return r")
    return "\n".join(lines) + "\n"
