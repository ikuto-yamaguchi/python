from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Iterable


@dataclass
class CostLedger:
    parser_checks: int = 0
    fact_reads: int = 0
    fact_writes: int = 0
    tool_calls: int = 0
    candidate_evaluations: int = 0
    output_chars: int = 0

    def add(self, other: "CostLedger") -> None:
        self.parser_checks += other.parser_checks
        self.fact_reads += other.fact_reads
        self.fact_writes += other.fact_writes
        self.tool_calls += other.tool_calls
        self.candidate_evaluations += other.candidate_evaluations
        self.output_chars += other.output_chars


class IndexedFactStore:
    """Sparse exact state with direct relation/subject lookup."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, str], str] = {}
        self.reads = 0
        self.writes = 0

    def set(self, relation: str, subject: str, value: str) -> None:
        self._values[(relation, subject)] = value
        self.writes += 1

    def get(self, relation: str, subject: str) -> str | None:
        self.reads += 1
        return self._values.get((relation, subject))

    def items(self) -> Iterable[tuple[tuple[str, str], str]]:
        return self._values.items()

    @property
    def count(self) -> int:
        return len(self._values)

    def approximate_bits(self) -> int:
        symbols: set[str] = set()
        for (relation, subject), value in self._values.items():
            symbols.update((relation, subject, value))
        id_bits = max(1, math.ceil(math.log2(max(2, len(symbols)))))
        return self.count * 3 * id_bits


class ScanningFactStore:
    """Deliberately naive baseline that scans every fact."""

    def __init__(self) -> None:
        self._values: list[tuple[str, str, str]] = []
        self.reads = 0
        self.writes = 0

    def set(self, relation: str, subject: str, value: str) -> None:
        for index, (r, s, _v) in enumerate(self._values):
            self.reads += 1
            if r == relation and s == subject:
                self._values[index] = (relation, subject, value)
                self.writes += 1
                return
        self._values.append((relation, subject, value))
        self.writes += 1

    def get(self, relation: str, subject: str) -> str | None:
        for r, s, value in self._values:
            self.reads += 1
            if r == relation and s == subject:
                return value
        return None

    @property
    def count(self) -> int:
        return len(self._values)

    def approximate_bits(self) -> int:
        symbols: set[str] = set()
        for relation, subject, value in self._values:
            symbols.update((relation, subject, value))
        id_bits = max(1, math.ceil(math.log2(max(2, len(symbols)))))
        return self.count * 3 * id_bits


@dataclass
class ToyRepo:
    source: str = "def transform(x):\n    return x + 1\n"
    public_tests: tuple[tuple[int, int], ...] = ((0, 1), (1, 2))
    hidden_tests: tuple[tuple[int, int], ...] = ((2, 5), (3, 10))

    def _evaluate_source(self, x: int) -> int:
        if "x * x + 1" in self.source:
            return x * x + 1
        if "2 * x + 1" in self.source:
            return 2 * x + 1
        return x + 1

    def run_tests(self, include_hidden: bool) -> tuple[bool, list[tuple[int, int, int]]]:
        tests = self.public_tests + (self.hidden_tests if include_hidden else ())
        failures = []
        for x_value, expected in tests:
            actual = self._evaluate_source(x_value)
            if actual != expected:
                failures.append((x_value, expected, actual))
        return not failures, failures

    def patch(self, expression: str) -> None:
        self.source = f"def transform(x):\n    return {expression}\n"


@dataclass
class ConversationState:
    facts: object
    focus: str | None = None
    previous_location: tuple[str, str] | None = None
    repo: ToyRepo = field(default_factory=ToyRepo)
    ledger: CostLedger = field(default_factory=CostLedger)


class LiteralAgent:
    """First failed attempt: exact surface forms, scan store, no discourse state."""

    remember_pattern = re.compile(r"^(.+?)は(.+?)にあります[。.]?$")
    query_pattern = re.compile(r"^(.+?)はどこにありますか[？?]$")
    move_pattern = re.compile(r"^(.+?)を(.+?)に移してください[。.]?$")

    def __init__(self) -> None:
        self.state = ConversationState(facts=ScanningFactStore())

    def respond(self, text: str) -> str:
        for pattern, intent in (
            (self.remember_pattern, "remember"),
            (self.query_pattern, "query"),
            (self.move_pattern, "move"),
        ):
            self.state.ledger.parser_checks += 1
            match = pattern.match(text.strip())
            if not match:
                continue
            if intent == "remember":
                subject, location = match.groups()
                self.state.facts.set("location", subject, location)
                return f"{subject}は{location}にあります。"
            if intent == "query":
                subject = match.group(1)
                location = self.state.facts.get("location", subject)
                return f"{subject}は{location}にあります。" if location else "分かりません。"
            subject, location = match.groups()
            self.state.facts.set("location", subject, location)
            return f"{subject}を{location}に移しました。"
        return "理解できませんでした。"


class CanonicalConversationAgent:
    """Canonical intents, minimal discourse state, indexed facts and task loop."""

    expanded_normalization = True

    def __init__(self) -> None:
        self.state = ConversationState(facts=IndexedFactStore())

    def _clean(self, text: str) -> str:
        text = text.strip().replace("？", "?").replace("。", "").replace("！", "!")
        text = text.replace("へ", "に")
        replacements = (
            ("移してください", "移して"),
            ("移動してください", "移動して"),
            ("運んでください", "運んで"),
            ("置いてください", "置いて"),
            ("教えてください", "教えて"),
            ("確認してください", "確認して"),
            ("答えてください", "答えて"),
        )
        if self.expanded_normalization:
            for source, target in replacements:
                text = text.replace(source, target)
        text = re.sub(r"\s+", "", text)
        return text

    @staticmethod
    def _is_thanks(text: str) -> bool:
        return any(word in text for word in ("ありがとう", "助かった", "サンキュー"))

    def _resolve_subject(self, raw: str | None) -> str | None:
        if raw is None or raw in {"それ", "これ", "あれ", "さっきのもの", "その箱", "今のもの"}:
            return self.state.focus
        return raw

    def _remember(self, subject: str, location: str) -> str:
        old = self.state.facts.get("location", subject)
        if old is not None:
            self.state.previous_location = (subject, old)
        self.state.facts.set("location", subject, location)
        self.state.focus = subject
        return f"了解。{subject}は{location}にあります。"

    def _move(self, subject: str, location: str) -> str:
        old = self.state.facts.get("location", subject)
        if old is not None:
            self.state.previous_location = (subject, old)
        self.state.facts.set("location", subject, location)
        self.state.focus = subject
        return f"{subject}を{location}に移しました。"

    def _query(self, subject: str | None) -> str:
        subject = self._resolve_subject(subject)
        if subject is None:
            return "どの物についてか分かりません。"
        location = self.state.facts.get("location", subject)
        self.state.focus = subject
        return f"{subject}は{location}にあります。" if location else f"{subject}の場所は未登録です。"

    def _correct_location(self, location: str) -> str:
        subject = self.state.focus
        if subject is None:
            return "訂正する対象が分かりません。"
        return self._move(subject, location)

    def _run_repo_task(self) -> str:
        ledger = self.state.ledger
        ledger.tool_calls += 1
        source_before = self.state.repo.source
        candidates = ("x + 1", "2 * x + 1", "x * x + 1")
        passing_public: list[str] = []
        for expression in candidates:
            ledger.candidate_evaluations += 1
            self.state.repo.patch(expression)
            ok, _ = self.state.repo.run_tests(include_hidden=False)
            ledger.tool_calls += 1
            if ok:
                passing_public.append(expression)
        first = min(passing_public, key=len)
        self.state.repo.patch(first)
        ledger.tool_calls += 1
        hidden_ok, failures = self.state.repo.run_tests(include_hidden=True)
        if hidden_ok:
            return f"修正しました。`{first}`で全テストに成功しました。"
        for x_value, expected, actual in failures:
            self.state.facts.set("test_failure", str(x_value), f"{expected}:{actual}")
        valid: list[str] = []
        for expression in candidates:
            ledger.candidate_evaluations += 1
            self.state.repo.patch(expression)
            ledger.tool_calls += 1
            ok, _ = self.state.repo.run_tests(include_hidden=True)
            if ok:
                valid.append(expression)
        if not valid:
            self.state.repo.source = source_before
            return "修正候補を見つけられませんでした。"
        winner = min(valid, key=len)
        self.state.repo.patch(winner)
        ledger.tool_calls += 1
        final_ok, _ = self.state.repo.run_tests(include_hidden=True)
        if not final_ok:
            self.state.repo.source = source_before
            return "修正後の検証に失敗したため元に戻しました。"
        return (
            f"最初の `{first}` は隠しテストで失敗しました。"
            f"失敗を反映して `{winner}` に修正し、全テストに成功しました。"
        )

    def respond(self, text: str) -> str:
        clean = self._clean(text)
        output: str
        self.state.ledger.parser_checks += 1
        if self._is_thanks(clean):
            output = "どういたしまして。"
            self.state.ledger.output_chars += len(output)
            return output
        self.state.ledger.parser_checks += 1
        if "transform" in clean and any(word in clean for word in ("修正", "直して", "テスト")):
            output = self._run_repo_task()
            self.state.ledger.output_chars += len(output)
            return output
        self.state.ledger.parser_checks += 1
        match = re.match(r"^(?:いや、?|違う、?)(.+?)(?:じゃなくて|ではなく)(.+)$", clean)
        if match:
            output = self._correct_location(match.group(2))
            self.state.ledger.output_chars += len(output)
            return output
        match = re.match(r"^(.+?)に(?:して|変更)$", clean)
        if match and self.state.focus:
            output = self._correct_location(match.group(1))
            self.state.ledger.output_chars += len(output)
            return output
        self.state.ledger.parser_checks += 1
        compound_pattern = (
            r"^(.+?)を(.+?)に(?:移して|移動して|運んで)(?:から)?、?(?:どこにあるか|場所を)?(?:答えて|教えて|確認して)$"
            if self.expanded_normalization
            else r"^(.+?)を(.+?)に(?:移して|移動して|運んで)(?:から|、)?(?:どこにあるか|場所を)?(?:答えて|教えて|確認して)$"
        )
        match = re.match(compound_pattern, clean)
        if match:
            subject = self._resolve_subject(match.group(1))
            if subject is None:
                output = "移動する対象が分かりません。"
            else:
                self._move(subject, match.group(2))
                output = self._query(subject)
            self.state.ledger.output_chars += len(output)
            return output
        self.state.ledger.parser_checks += 1
        match = re.match(r"^(.+?)を(.+?)に(?:移して|移動して|運んで|置いて)$", clean)
        if match:
            subject = self._resolve_subject(match.group(1))
            output = self._move(subject, match.group(2)) if subject else "移動する対象が分かりません。"
            self.state.ledger.output_chars += len(output)
            return output
        self.state.ledger.parser_checks += 1
        match = re.match(r"^(.+?)は(.+?)に(?:ある|あります|置いてある|います)$", clean)
        if match:
            output = self._remember(match.group(1), match.group(2))
            self.state.ledger.output_chars += len(output)
            return output
        self.state.ledger.parser_checks += 1
        match = re.match(r"^(.+?)は(?:今)?どこ(?:にある|にありますか)?\??$", clean)
        if match:
            output = self._query(match.group(1))
            self.state.ledger.output_chars += len(output)
            return output
        if clean in {"今どこ?", "どこ?", "場所を教えて", "今の場所は?"}:
            output = self._query(None)
            self.state.ledger.output_chars += len(output)
            return output
        output = "理解できませんでした。"
        self.state.ledger.output_chars += len(output)
        return output


class CanonicalV1Agent(CanonicalConversationAgent):
    """Intermediate attempt before shared polite/compound normalization was added."""

    expanded_normalization = False


def seed_facts(agent: LiteralAgent | CanonicalConversationAgent, count: int) -> None:
    for index in range(count):
        agent.state.facts.set("location", f"物{index}", f"場所{index}")


class ResidualRewriteAgent(CanonicalConversationAgent):
    """Third attempt: compile only observed paraphrase residuals into surface rewrites."""

    residual_rule_count = 4

    def _clean(self, text: str) -> str:
        text = super()._clean(text)
        rewrites: tuple[tuple[re.Pattern[str], str], ...] = (
            (re.compile(r"^(.+)、たしか(.+)だったよね\?$"), r"\1はどこ?"),
            (re.compile(r"^(.+)、(.+)にお願い$"), r"\1を\2に移して"),
            (re.compile(r"^どこやったっけ\?$"), "今どこ?"),
            (re.compile(r"^(.+)、(.+)に持ってっといて$"), r"\1を\2に移して"),
        )
        for pattern, replacement in rewrites:
            if pattern.match(text):
                return pattern.sub(replacement, text)
        return text
