"""C0(命令網羅)テスト生成特化エージェント。

「閉じたインターフェース + 極小モデル + 外部記憶 + 実行フィードバック」
という MNEME の特化エージェント設計方針の原理検証。

対象: 整数引数と比較条件の if/elif/else 木からなる部分言語の関数。
タスク: 全命令(文)を少なくとも一度実行するテスト入力集合を、
        できるだけ少ない実行回数で見つける(C0 = 100% を目指す)。
"""

from .codegen import gen_function
from .coverage import compile_function, executable_lines, guard_chains, run_with_coverage
from .solver import ConditionSolver
from .agent import C0Agent, ConditionMemory, random_search

__all__ = [
    "gen_function",
    "compile_function",
    "executable_lines",
    "guard_chains",
    "run_with_coverage",
    "ConditionSolver",
    "C0Agent",
    "ConditionMemory",
    "random_search",
]
