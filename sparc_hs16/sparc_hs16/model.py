from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import time
from dataclasses import dataclass, field
from pathlib import Path


_JA_PUNCT = str.maketrans({"　": " ", "，": ",", "．": ".", "？": "?", "！": "!", "＝": "=", "＋": "+", "－": "-", "×": "*", "÷": "/"})


def normalize(text: str) -> str:
    text = text.translate(_JA_PUNCT).strip().lower()
    text = re.sub(r"\s+", "", text)
    return text


def char_ngrams(text: str, n_values: tuple[int, ...] = (2, 3, 4)) -> set[str]:
    t = f"^{normalize(text)}$"
    out: set[str] = set()
    for n in n_values:
        out.update(t[i : i + n] for i in range(max(0, len(t) - n + 1)))
    return out


@dataclass(slots=True)
class SparseExample:
    prompt: str
    response: str
    signature: tuple[int, ...]


@dataclass
class SparseMemory:
    bits: int = 1 << 16
    active_bits: int = 128
    examples: list[SparseExample] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def _hash(self, token: str) -> int:
        digest = hashlib.blake2s(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "little") % self.bits

    def signature(self, text: str) -> tuple[int, ...]:
        hashed = sorted({self._hash(g) for g in char_ngrams(text)})
        if len(hashed) <= self.active_bits:
            return tuple(hashed)
        step = len(hashed) / self.active_bits
        return tuple(hashed[min(len(hashed) - 1, int(i * step))] for i in range(self.active_bits))

    def teach(self, prompt: str, response: str) -> None:
        self.examples.append(SparseExample(prompt, response, self.signature(prompt)))

    def teach_fact(self, subject: str, value: str) -> None:
        self.facts[normalize(subject)] = value.strip()

    def recall(self, prompt: str, threshold: float = 0.18) -> tuple[str | None, float]:
        if not self.examples:
            return None, 0.0
        query = set(self.signature(prompt))
        best: SparseExample | None = None
        best_score = 0.0
        for example in self.examples:
            candidate = set(example.signature)
            union = len(query | candidate)
            score = len(query & candidate) / union if union else 0.0
            if score > best_score:
                best, best_score = example, score
        if best is None or best_score < threshold:
            return None, best_score
        return best.response, best_score

    def to_dict(self) -> dict:
        return {
            "bits": self.bits,
            "active_bits": self.active_bits,
            "examples": [
                {"prompt": e.prompt, "response": e.response, "signature": list(e.signature)}
                for e in self.examples
            ],
            "facts": self.facts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SparseMemory":
        memory = cls(bits=int(data["bits"]), active_bits=int(data["active_bits"]))
        memory.examples = [
            SparseExample(str(e["prompt"]), str(e["response"]), tuple(int(x) for x in e["signature"]))
            for e in data.get("examples", [])
        ]
        memory.facts = {str(k): str(v) for k, v in data.get("facts", {}).items()}
        return memory


class SafeArithmetic:
    _allowed_binops = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        ast.Pow: lambda a, b: a**b,
    }
    _allowed_unary = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}

    @classmethod
    def eval(cls, expression: str, variables: dict[str, float] | None = None) -> float:
        variables = variables or {}
        tree = ast.parse(expression, mode="eval")

        def visit(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                return visit(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            if isinstance(node, ast.Name) and node.id in variables:
                return float(variables[node.id])
            if isinstance(node, ast.BinOp) and type(node.op) in cls._allowed_binops:
                left, right = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Pow) and abs(right) > 12:
                    raise ValueError("exponent too large")
                return cls._allowed_binops[type(node.op)](left, right)
            if isinstance(node, ast.UnaryOp) and type(node.op) in cls._allowed_unary:
                return cls._allowed_unary[type(node.op)](visit(node.operand))
            raise ValueError(f"unsupported expression node: {type(node).__name__}")

        value = visit(tree)
        if not math.isfinite(value):
            raise ValueError("non-finite result")
        return value


@dataclass(slots=True)
class SolveResult:
    answer: str
    mechanism: str
    confidence: float
    elapsed_ms: float


class SparcHS16:
    """Small non-Transformer sparse-program research baseline."""

    UNIT_SCALE = {
        "mm": ("length", 0.001),
        "cm": ("length", 0.01),
        "m": ("length", 1.0),
        "km": ("length", 1000.0),
        "mg": ("mass", 0.000001),
        "g": ("mass", 0.001),
        "kg": ("mass", 1.0),
        "ml": ("volume", 0.000001),
        "l": ("volume", 0.001),
        "s": ("time", 1.0),
        "min": ("time", 60.0),
        "h": ("time", 3600.0),
    }

    def __init__(self, memory: SparseMemory | None = None) -> None:
        self.memory = memory or SparseMemory()
        self._bootstrap_dialogue()

    def _bootstrap_dialogue(self) -> None:
        if self.memory.examples:
            return
        pairs = [
            ("こんにちは", "こんにちは。今日は何を一緒に考えましょうか？"),
            ("ありがとう", "どういたしまして。役に立ててうれしいです。"),
            ("疲れた", "お疲れさまです。状況を整理しながら、負担の少ない進め方を考えましょう。"),
            ("分からない", "大丈夫です。前提、途中式、結論の順に分解して説明します。"),
            ("間違っている", "指摘ありがとう。前提と計算を再確認し、誤りを具体的に直します。"),
        ]
        for prompt, response in pairs:
            self.memory.teach(prompt, response)

    @staticmethod
    def _fmt(value: float) -> str:
        if abs(value - round(value)) < 1e-10:
            return str(int(round(value)))
        return f"{value:.10g}"

    def solve(self, text: str) -> SolveResult:
        started = time.perf_counter()
        normalized = normalize(text)
        attempts = [
            self._solve_linear_equation,
            self._solve_unit_conversion,
            self._solve_syllogism,
            self._solve_arithmetic,
            self._solve_fact,
        ]
        for solver in attempts:
            result = solver(text, normalized)
            if result is not None:
                elapsed = (time.perf_counter() - started) * 1000
                return SolveResult(result[0], result[1], result[2], elapsed)

        response, score = self.memory.recall(text)
        elapsed = (time.perf_counter() - started) * 1000
        if response is not None:
            return SolveResult(response, "sparse-dialogue-recall", min(0.9, 0.4 + score), elapsed)
        return SolveResult(
            "この入力を確実に解くための機構をまだ獲得していません。分野や条件を追加してください。",
            "calibrated-abstention",
            0.0,
            elapsed,
        )

    def _solve_arithmetic(self, text: str, normalized: str) -> tuple[str, str, float] | None:
        match = re.search(r"(?:計算|求め|いくつ|答え)?[はを:]?([0-9\.\+\-\*\/\(\)\^]+)(?:ですか|を計算|はいくつ|\?|$)", normalized)
        if not match:
            return None
        expression = match.group(1).replace("^", "**")
        if not re.search(r"[+\-*/]", expression):
            return None
        try:
            value = SafeArithmetic.eval(expression)
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            return None
        return f"{self._fmt(value)}です。", "verified-arithmetic", 1.0

    def _solve_linear_equation(self, text: str, normalized: str) -> tuple[str, str, float] | None:
        match = re.search(r"(?:方程式)?([0-9x\.\+\-\*\/\(\)]+)=([0-9x\.\+\-\*\/\(\)]+)", normalized)
        if not match or "x" not in match.group(0):
            return None
        left, right = match.group(1), match.group(2)
        try:
            l0, l1 = SafeArithmetic.eval(left, {"x": 0}), SafeArithmetic.eval(left, {"x": 1})
            r0, r1 = SafeArithmetic.eval(right, {"x": 0}), SafeArithmetic.eval(right, {"x": 1})
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            return None
        a = (l1 - l0) - (r1 - r0)
        b = r0 - l0
        if abs(a) < 1e-12:
            answer = "恒等式です。" if abs(b) < 1e-12 else "解はありません。"
        else:
            x = b / a
            if abs(SafeArithmetic.eval(left, {"x": x}) - SafeArithmetic.eval(right, {"x": x})) > 1e-8:
                return None
            answer = f"x={self._fmt(x)}です。"
        return answer, "verified-linear-equation", 1.0

    def _solve_unit_conversion(self, text: str, normalized: str) -> tuple[str, str, float] | None:
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)(mm|cm|km|m|mg|kg|g|ml|l|min|h|s)(?:は|を)(mm|cm|km|m|mg|kg|g|ml|l|min|h|s)", normalized)
        if not match:
            return None
        value, source, target = float(match.group(1)), match.group(2), match.group(3)
        s_dim, s_scale = self.UNIT_SCALE[source]
        t_dim, t_scale = self.UNIT_SCALE[target]
        if s_dim != t_dim:
            return "次元が異なるため変換できません。", "dimension-check", 1.0
        converted = value * s_scale / t_scale
        return f"{self._fmt(converted)}{target}です。", "verified-unit-conversion", 1.0

    def _solve_syllogism(self, text: str, normalized: str) -> tuple[str, str, float] | None:
        rules = re.findall(r"すべての(.+?)は(.+?)(?:です|である)?[。.]", text)
        statements = [part.strip() for part in re.split(r"[。.]", text) if part.strip()]
        facts: list[tuple[str, str]] = []
        for statement in statements[:-1]:
            if statement.startswith("すべての"):
                continue
            fact = re.fullmatch(r"(.+?)は(.+?)(?:です|である)", statement)
            if fact:
                facts.append((fact.group(1), fact.group(2)))
        query_text = statements[-1] if statements else text.strip()
        query = re.fullmatch(r"(.+?)は(.+?)(?:ですか|か)[?？]?", query_text)
        if not rules or not facts or not query:
            return None
        graph: dict[str, set[str]] = {}
        for src, dst in rules:
            graph.setdefault(normalize(src), set()).add(normalize(dst))
        entity, initial = facts[-1]
        q_entity, target = query.group(1), query.group(2)
        if normalize(entity) != normalize(q_entity):
            return None
        seen = {normalize(initial)}
        frontier = list(seen)
        while frontier:
            current = frontier.pop()
            for nxt in graph.get(current, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
        entailed = normalize(target) in seen
        return ("はい、導けます。" if entailed else "いいえ、その前提だけからは導けません。", "verified-syllogism", 1.0)

    def _solve_fact(self, text: str, normalized: str) -> tuple[str, str, float] | None:
        teach = re.match(r"(.+?)は(.+?)と覚えて", text.strip())
        if teach:
            self.memory.teach_fact(teach.group(1), teach.group(2))
            return "覚えました。", "online-fact-learning", 1.0
        question = re.match(r"(.+?)(?:は何|って何|とは)[?？]?\s*$", text.strip())
        if not question:
            return None
        key = normalize(question.group(1))
        if key in self.memory.facts:
            return self.memory.facts[key], "sparse-fact-memory", 1.0
        return None

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.memory.to_dict(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SparcHS16":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(SparseMemory.from_dict(data))
