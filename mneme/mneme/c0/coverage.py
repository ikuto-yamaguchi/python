"""行カバレッジ計測とパス制約の抽出(エージェントの「環境」側)。

エージェントに与えられる観測は IDE やカバレッジツールが普通に提供する
情報と同じ: どの行が未実行か、その行に到達するための条件式のテキスト。
条件式を「理解」して充足値を出す部分だけがモデルの仕事になる。
"""

from __future__ import annotations

import ast
import sys
from typing import Callable

FILENAME = "<c0gen>"


def compile_function(src: str, name: str = "f") -> Callable:
    code = compile(src, FILENAME, "exec")
    ns: dict = {}
    exec(code, ns)
    return ns[name]


def executable_lines(src: str) -> set[int]:
    """関数本体の実行可能な文の行番号集合(C0 の分母)。"""
    fn = ast.parse(src).body[0]
    lines = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.stmt) and not isinstance(node, ast.FunctionDef):
            lines.add(node.lineno)
    return lines


def guard_chains(src: str) -> dict[int, list[tuple[str, bool]]]:
    """各行番号 → その行に到達するためのガード条件列 [(条件式, 否定か)]。"""
    fn = ast.parse(src).body[0]
    chains: dict[int, list[tuple[str, bool]]] = {}

    def walk(stmts: list[ast.stmt], active: list[tuple[str, bool]]) -> None:
        for st in stmts:
            chains[st.lineno] = list(active)
            if isinstance(st, ast.If):
                cond = ast.unparse(st.test)
                walk(st.body, active + [(cond, False)])
                walk(st.orelse, active + [(cond, True)])

    walk(fn.body, [])
    return chains


def run_with_coverage(func: Callable, kwargs: dict[str, int]) -> set[int]:
    """関数を 1 回実行し、実行された行番号集合を返す。"""
    lines: set[int] = set()

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None
        if event == "line":
            lines.add(frame.f_lineno)
        return tracer

    old = sys.gettrace()
    sys.settrace(tracer)
    try:
        func(**kwargs)
    finally:
        sys.settrace(old)
    return lines
