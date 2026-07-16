from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import zlib
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .meci_chat import DialogueRecord

_COPULA_RE = re.compile(r"^(.+?)は(.+?)(?:です|だ|である)[。.!！]*$")
_PROPERTY_RE = re.compile(r"^(.+?)の([^は]+?)は(.+?)(?:です|だ|である)?[。.!！]*$")
_CAUSE_RE = re.compile(r"^(.+?)(?:なの|であるの)?は(.+?)(?:から|ため)(?:です)?[。.!！]*$")
_NAME_RE = re.compile(r"^(?:私|ぼく|僕|わたし)の名前は(.+?)(?:です|だ)?[。.!！]*$")
_WHAT_RE = re.compile(r"^(.+?)は(?:何|誰)(?:ですか|なの|だ|？|\?)?[。.!！]*$")
_PROPERTY_Q_RE = re.compile(r"^(.+?)の(.+?)は(?:何|誰)(?:ですか|なの|だ|？|\?)?[。.!！]*$")
_YESNO_RE = re.compile(r"^(.+?)は(.+?)(?:ですか|なの|か|？|\?)$")
_WHY_RE = re.compile(r"^(.+?)(?:なの|であるの)?は(?:なぜ|どうして)(?:ですか|なの|？|\?)?[。.!！]*$")
_REMEMBER_RE = re.compile(r"^(?:覚えて|記憶して)[:：]?\s*(.+)$")


def _normalize(text: str) -> str:
    text = text.strip().replace("?", "？")
    text = re.sub(r"\s+", " ", text)
    return text


def _entity(text: str) -> str:
    return text.strip(" 。.!！?？\"'「」『』")


def _hash_feature(token: str, dimensions: int) -> tuple[int, int]:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    code = int.from_bytes(digest, "little")
    return code % dimensions, 1 if code >> 63 else -1


def _ngrams(text: str, widths: Sequence[int] = (1, 2, 3, 4)) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    result: list[str] = []
    for width in widths:
        result.extend(
            compact[index : index + width]
            for index in range(max(0, len(compact) - width + 1))
        )
    return result


def _vectorize(text: str, dimensions: int) -> dict[int, float]:
    values: dict[int, float] = defaultdict(float)
    for token in _ngrams(_normalize(text)):
        index, sign = _hash_feature(token, dimensions)
        values[index] += float(sign)
    norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
    return {index: value / norm for index, value in values.items()}


def _dot(left: dict[int, float], right: dict[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


@dataclass(frozen=True)
class Fact:
    subject: str
    relation: str
    object: str
    confidence: float = 1.0
    source: str = "conversation"


@dataclass(frozen=True)
class Episode:
    user: str
    assistant: str


@dataclass(frozen=True)
class AgentReply:
    text: str
    mechanism: str
    confidence: float
    supporting_facts: tuple[Fact, ...] = ()


class SafeArithmetic:
    _OPS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        ast.Pow: lambda a, b: a**b,
        ast.USub: lambda a: -a,
        ast.UAdd: lambda a: a,
    }

    @classmethod
    def evaluate(cls, text: str) -> int | float | None:
        expression = text.translate(str.maketrans("０１２３４５６７８９＋－×÷", "0123456789+-*/"))
        expression = expression.replace("は？", "").replace("は?", "").replace("？", "")
        expression = expression.strip()
        if not re.fullmatch(r"[0-9+\-*/%(). ]{1,80}", expression):
            return None
        try:
            tree = ast.parse(expression, mode="eval")
            value = cls._walk(tree.body)
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            return None
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    @classmethod
    def _walk(cls, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in cls._OPS:
            left = cls._walk(node.left)
            right = cls._walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("power too large")
            return cls._OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls._OPS:
            return cls._OPS[type(node.op)](cls._walk(node.operand))
        raise ValueError("unsupported expression")


class SparseEpisodeMemory:
    def __init__(self, dimensions: int = 16384) -> None:
        self.dimensions = dimensions
        self.episodes: list[Episode] = []
        self.vectors: list[dict[int, float]] = []

    def add(self, user: str, assistant: str) -> None:
        self.episodes.append(Episode(_normalize(user), assistant.strip()))
        self.vectors.append(_vectorize(user, self.dimensions))

    def retrieve(self, user: str, threshold: float = 0.48) -> tuple[Episode | None, float]:
        if not self.episodes:
            return None, 0.0
        query = _vectorize(user, self.dimensions)
        scores = [_dot(query, vector) for vector in self.vectors]
        index = max(range(len(scores)), key=scores.__getitem__)
        if scores[index] < threshold:
            return None, scores[index]
        return self.episodes[index], scores[index]


class MECICognitiveAgent:
    """Small non-neural conversational cognition prototype.

    The executable state is split into semantic facts, episodic examples and a
    bounded working memory. Responses are selected by explicit reasoning
    mechanisms before sparse episode retrieval. This is deliberately auditable
    and online-learnable; it is not yet a claim of high-school-level ability.
    """

    def __init__(self, *, dimensions: int = 16384, working_turns: int = 24) -> None:
        self.dimensions = dimensions
        self.episodes = SparseEpisodeMemory(dimensions)
        self.facts: dict[tuple[str, str], list[Fact]] = defaultdict(list)
        self.turns: deque[tuple[str, str]] = deque(maxlen=working_turns)
        self.last_subject: str | None = None

    def fit(self, records: Iterable[DialogueRecord]) -> "MECICognitiveAgent":
        for record in records:
            self.episodes.add(record.user, record.assistant)
            self._learn_from_text(record.user, source="training-user")
            self._learn_from_text(record.assistant, source="training-assistant")
        return self

    def teach(self, user: str, assistant: str) -> None:
        self.episodes.add(user, assistant)

    def add_fact(self, subject: str, relation: str, obj: str, *, source: str = "conversation") -> Fact:
        fact = Fact(_entity(subject), relation.strip(), _entity(obj), 1.0, source)
        key = (fact.subject, fact.relation)
        if all(existing.object != fact.object for existing in self.facts[key]):
            self.facts[key].append(fact)
        self.last_subject = fact.subject
        return fact

    def _learn_from_text(self, text: str, *, source: str) -> list[Fact]:
        text = _normalize(text)
        learned: list[Fact] = []
        name = _NAME_RE.match(text)
        if name:
            learned.append(self.add_fact("ユーザー", "名前", name.group(1), source=source))
            return learned
        cause = _CAUSE_RE.match(text)
        if cause:
            learned.append(self.add_fact(cause.group(1), "理由", cause.group(2), source=source))
            return learned
        prop = _PROPERTY_RE.match(text)
        if prop:
            learned.append(self.add_fact(prop.group(1), prop.group(2), prop.group(3), source=source))
            return learned
        copula = _COPULA_RE.match(text)
        if copula and not text.endswith("？"):
            learned.append(self.add_fact(copula.group(1), "is", copula.group(2), source=source))
        return learned

    def _resolve_subject(self, subject: str) -> str:
        subject = _entity(subject)
        if subject in {"それ", "その人", "そのもの", "彼", "彼女"} and self.last_subject:
            return self.last_subject
        if subject in {"私", "わたし", "僕", "ぼく"}:
            return "ユーザー"
        return subject

    def _direct(self, subject: str, relation: str) -> list[Fact]:
        return list(self.facts.get((subject, relation), ()))

    def _is_path(self, subject: str, target: str, max_depth: int = 5) -> tuple[Fact, ...] | None:
        queue: deque[tuple[str, tuple[Fact, ...]]] = deque([(subject, ())])
        visited = {subject}
        while queue:
            current, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for fact in self._direct(current, "is"):
                next_path = path + (fact,)
                if fact.object == target:
                    return next_path
                if fact.object not in visited:
                    visited.add(fact.object)
                    queue.append((fact.object, next_path))
        return None

    def _answer_fact_question(self, text: str) -> AgentReply | None:
        property_question = _PROPERTY_Q_RE.match(text)
        if property_question:
            subject = self._resolve_subject(property_question.group(1))
            relation = _entity(property_question.group(2))
            facts = self._direct(subject, relation)
            self.last_subject = subject
            if facts:
                values = "、".join(fact.object for fact in facts)
                return AgentReply(f"{subject}の{relation}は{values}です。", "semantic-recall", 1.0, tuple(facts))
            return AgentReply(f"{subject}の{relation}は、まだ教わっていません。", "known-unknown", 1.0)

        what = _WHAT_RE.match(text)
        if what:
            subject = self._resolve_subject(what.group(1))
            facts = self._direct(subject, "is")
            self.last_subject = subject
            if facts:
                values = "、".join(fact.object for fact in facts)
                return AgentReply(f"{subject}は{values}です。", "semantic-recall", 1.0, tuple(facts))
            return AgentReply(f"{subject}については、まだ十分に知りません。", "known-unknown", 1.0)

        why = _WHY_RE.match(text)
        if why:
            subject = self._resolve_subject(why.group(1))
            facts = self._direct(subject, "理由")
            self.last_subject = subject
            if facts:
                return AgentReply(f"{facts[0].object}からです。", "causal-recall", 1.0, tuple(facts[:1]))
            return AgentReply(f"{subject}の理由は、まだ分かりません。", "known-unknown", 1.0)

        yesno = _YESNO_RE.match(text)
        if yesno:
            subject = self._resolve_subject(yesno.group(1))
            target = _entity(yesno.group(2))
            path = self._is_path(subject, target)
            self.last_subject = subject
            if path:
                if len(path) == 1:
                    explanation = f"{path[0].subject}は{path[0].object}だと教わっています。"
                else:
                    chain = "、".join(f"{fact.subject}は{fact.object}" for fact in path)
                    explanation = f"{chain}とつながるためです。"
                return AgentReply(f"はい。{explanation}", "transitive-reasoning", 0.98, path)
            direct = self._direct(subject, "is")
            if direct:
                return AgentReply(
                    f"今の知識だけでは、{subject}が{target}だとは確認できません。",
                    "open-world-rejection",
                    0.8,
                    tuple(direct),
                )
        return None

    def reply(self, user_text: str) -> AgentReply:
        text = _normalize(user_text)
        remember = _REMEMBER_RE.match(text)
        if remember:
            learned = self._learn_from_text(remember.group(1), source="explicit-memory")
            response = "覚えました。" if learned else "その内容は、まだ事実の形に整理できませんでした。"
            result = AgentReply(response, "online-semantic-learning", 1.0 if learned else 0.2, tuple(learned))
            self.turns.append((text, result.text))
            return result

        arithmetic = SafeArithmetic.evaluate(text)
        if arithmetic is not None:
            result = AgentReply(f"{arithmetic}です。", "symbolic-arithmetic", 1.0)
            self.turns.append((text, result.text))
            return result

        fact_answer = self._answer_fact_question(text)
        if fact_answer is not None:
            self.turns.append((text, fact_answer.text))
            return fact_answer

        learned = self._learn_from_text(text, source="live-conversation")
        if learned:
            result = AgentReply("分かりました。覚えておきます。", "online-semantic-learning", 1.0, tuple(learned))
            self.turns.append((text, result.text))
            return result

        if text in {"こんにちは", "やあ", "おはよう", "こんばんは"}:
            result = AgentReply("こんにちは。何について一緒に考えましょうか？", "social-program", 1.0)
            self.turns.append((text, result.text))
            return result

        episode, score = self.episodes.retrieve(text)
        if episode is not None:
            result = AgentReply(episode.assistant, "sparse-episodic-retrieval", score)
            self.turns.append((text, result.text))
            return result

        result = AgentReply(
            "まだその質問に答えるための知識や推論方法を持っていません。分かった答えを教えてもらえれば学習します。",
            "calibrated-unknown",
            max(0.0, min(1.0, score)),
        )
        self.turns.append((text, result.text))
        return result

    def to_bytes(self) -> bytes:
        payload = {
            "format": "meci-cognitive-001",
            "dimensions": self.dimensions,
            "facts": [asdict(fact) for facts in self.facts.values() for fact in facts],
            "episodes": [asdict(episode) for episode in self.episodes.episodes],
            "turns": list(self.turns),
            "last_subject": self.last_subject,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "MECICognitiveAgent":
        payload = json.loads(zlib.decompress(data))
        agent = cls(dimensions=int(payload["dimensions"]))
        for fact in payload.get("facts", []):
            agent.add_fact(fact["subject"], fact["relation"], fact["object"], source=fact.get("source", "artifact"))
        for episode in payload.get("episodes", []):
            agent.episodes.add(episode["user"], episode["assistant"])
        agent.turns.extend(tuple(turn) for turn in payload.get("turns", []))
        agent.last_subject = payload.get("last_subject")
        return agent

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "MECICognitiveAgent":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, int | float]:
        return {
            "dimensions": self.dimensions,
            "semantic_facts": sum(len(facts) for facts in self.facts.values()),
            "episodes": len(self.episodes.episodes),
            "working_turns": len(self.turns),
            "artifact_bytes": len(self.to_bytes()),
        }
