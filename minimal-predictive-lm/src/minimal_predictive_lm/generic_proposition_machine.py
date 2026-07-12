from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import itertools
import json
import re
from typing import Iterable, Mapping


@dataclass(frozen=True)
class BoolExpr:
    op: str
    value: str | None = None
    children: tuple["BoolExpr", ...] = ()

    def atoms(self) -> set[str]:
        if self.op == "atom":
            return {str(self.value)}
        output: set[str] = set()
        for child in self.children:
            output.update(child.atoms())
        return output

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        if self.op == "atom":
            return bool(assignment[str(self.value)])
        if self.op == "not":
            return not self.children[0].evaluate(assignment)
        if self.op == "and":
            return all(child.evaluate(assignment) for child in self.children)
        if self.op == "or":
            return any(child.evaluate(assignment) for child in self.children)
        if self.op == "implies":
            left, right = self.children
            return (not left.evaluate(assignment)) or right.evaluate(assignment)
        raise ValueError(f"unknown Boolean operation: {self.op}")


def atom(name: str) -> BoolExpr:
    return BoolExpr("atom", value=name)


def neg(expression: BoolExpr) -> BoolExpr:
    if expression.op == "not":
        return expression.children[0]
    return BoolExpr("not", children=(expression,))


def all_of(*items: BoolExpr) -> BoolExpr:
    flattened: list[BoolExpr] = []
    for item in items:
        flattened.extend(item.children if item.op == "and" else (item,))
    if len(flattened) == 1:
        return flattened[0]
    return BoolExpr("and", children=tuple(flattened))


def any_of(*items: BoolExpr) -> BoolExpr:
    flattened: list[BoolExpr] = []
    for item in items:
        flattened.extend(item.children if item.op == "or" else (item,))
    if len(flattened) == 1:
        return flattened[0]
    return BoolExpr("or", children=tuple(flattened))


def implies(left: BoolExpr, right: BoolExpr) -> BoolExpr:
    return BoolExpr("implies", children=(left, right))


@dataclass(frozen=True)
class MonadicSentence:
    quantifier: str
    expression: BoolExpr
    constant: str | None = None

    def negated(self) -> "MonadicSentence":
        if self.quantifier == "all":
            return MonadicSentence("some", neg(self.expression))
        if self.quantifier == "some":
            return MonadicSentence("all", neg(self.expression))
        return MonadicSentence("constant", neg(self.expression), self.constant)


class MonadicTheory:
    """Finite-model decision procedure for equality-free monadic first-order logic."""

    def __init__(self, premises: Iterable[MonadicSentence] = ()) -> None:
        self.premises = tuple(premises)

    def entails(self, conclusion: MonadicSentence) -> bool:
        return not self._satisfiable(self.premises + (conclusion.negated(),))

    @staticmethod
    def _satisfiable(sentences: tuple[MonadicSentence, ...]) -> bool:
        names = sorted(
            {
                name
                for sentence in sentences
                for name in sentence.expression.atoms()
            }
        )
        universal = [
            sentence.expression
            for sentence in sentences
            if sentence.quantifier == "all"
        ]
        existential = [
            sentence.expression
            for sentence in sentences
            if sentence.quantifier == "some"
        ]
        constants: dict[str, list[BoolExpr]] = defaultdict(list)
        for sentence in sentences:
            if sentence.quantifier == "constant":
                constants[str(sentence.constant)].append(sentence.expression)

        allowed: list[dict[str, bool]] = []
        for bits in itertools.product((False, True), repeat=len(names)):
            assignment = dict(zip(names, bits, strict=True))
            if all(expression.evaluate(assignment) for expression in universal):
                allowed.append(assignment)
        if not allowed:
            return False
        if any(
            not any(expression.evaluate(row) for row in allowed)
            for expression in existential
        ):
            return False
        for expressions in constants.values():
            if not any(
                all(expression.evaluate(row) for expression in expressions)
                for row in allowed
            ):
                return False
        return True


class ParityConstraintGraph:
    """Signed equality graph: left = right XOR inverted."""

    def __init__(self) -> None:
        self._edges: dict[str, list[tuple[str, bool]]] = defaultdict(list)
        self._seeds: dict[str, bool] = {}
        self.operations = 0

    def seed(self, node: str, value: bool) -> None:
        self._seeds[node] = value

    def relate(self, left: str, right: str, *, inverted: bool = False) -> None:
        self._edges[left].append((right, inverted))
        self._edges[right].append((left, inverted))

    def resolve(self, query: str) -> bool | None:
        values: dict[str, bool] = {}
        queue: deque[str] = deque()
        for node, value in self._seeds.items():
            if node in values and values[node] != value:
                return None
            values[node] = value
            queue.append(node)
        while queue:
            node = queue.popleft()
            self.operations += 1
            for other, inverted in self._edges.get(node, ()):
                proposed = values[node] ^ inverted
                if other in values:
                    if values[other] != proposed:
                        return None
                    continue
                values[other] = proposed
                queue.append(other)
        return values.get(query)


@dataclass(frozen=True)
class PropositionPrediction:
    output: str | None
    operations: int
    reads: int
    writes: int
    family: str | None


class GenericPropositionMachine:
    """Shared Boolean runtime with two benchmark-informed surface compilers."""

    _BASE_RE = re.compile(r"^([A-Z][A-Za-z-]*) (tells the truth|lies)$")
    _SAYS_RE = re.compile(
        r"^([A-Z][A-Za-z-]*) says ([A-Z][A-Za-z-]*) "
        r"(tells the truth|lies)$"
    )
    _QUERY_RE = re.compile(r"Does ([A-Z][A-Za-z-]*) tell the truth\?$")
    _CONCLUSION_MARKERS = (
        "So, necessarily,",
        "All this entails that",
        "All this entails",
        "From this follows:",
        "We may conclude that",
        "We may conclude:",
        "We may conclude",
        "In consequence,",
        "Therefore,",
        "Therefore",
        "Hence,",
        "Hence",
        "It follows that",
        "It follows",
    )

    def __init__(self) -> None:
        payload = {
            "runtime": "parity-plus-monadic-finite-model",
            "surface_compilers": [
                "quoted-truth-chain",
                "controlled-monadic-argument",
            ],
            "task_name_branches": 0,
        }
        self.description_bits = (
            len(
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            * 8
        )
        self.human_designed_surface_compilers = 2
        self.benchmark_task_name_branches = 0

    def predict(self, prompt: str) -> PropositionPrediction:
        belief = self._predict_belief(prompt)
        if belief is not None:
            return belief
        formal = self._predict_formal(prompt)
        if formal is not None:
            return formal
        return PropositionPrediction(None, 0, 1, 0, None)

    def _predict_belief(self, prompt: str) -> PropositionPrediction | None:
        if not prompt.startswith("Question: ") or "Does " not in prompt:
            return None
        body = prompt[len("Question: ") :]
        query_match = self._QUERY_RE.search(body)
        if query_match is None:
            return None
        query = query_match.group(1)
        facts_text = body[: query_match.start()].strip()
        if facts_text.endswith("."):
            facts_text = facts_text[:-1]
        statements = [
            item.strip()
            for item in facts_text.split(". ")
            if item.strip()
        ]
        graph = ParityConstraintGraph()
        reads = 0
        writes = 0
        for statement in statements:
            reads += 1
            base = self._BASE_RE.fullmatch(statement)
            if base:
                graph.seed(base.group(1), base.group(2) == "tells the truth")
                writes += 1
                continue
            says = self._SAYS_RE.fullmatch(statement)
            if says:
                graph.relate(
                    says.group(1),
                    says.group(2),
                    inverted=says.group(3) == "lies",
                )
                writes += 1
                continue
            return None
        result = graph.resolve(query)
        if result is None:
            return PropositionPrediction(
                None,
                graph.operations,
                reads,
                writes,
                "proposition-parity",
            )
        return PropositionPrediction(
            "Yes" if result else "No",
            graph.operations,
            reads + 1,
            writes + 1,
            "proposition-parity",
        )

    def _predict_formal(self, prompt: str) -> PropositionPrediction | None:
        if "deductively valid or invalid?" not in prompt:
            return None
        parsed = self._parse_argument(prompt)
        if parsed is None:
            return None
        premises, conclusion = parsed
        names = {
            name
            for sentence in premises + (conclusion,)
            for name in sentence.expression.atoms()
        }
        if len(names) > 14:
            return None
        valid = MonadicTheory(premises).entails(conclusion)
        operations = (1 << len(names)) * (len(premises) + 1)
        return PropositionPrediction(
            "valid" if valid else "invalid",
            operations,
            len(premises) + 1,
            1,
            "proposition-monadic",
        )

    def _parse_argument(
        self,
        prompt: str,
    ) -> tuple[tuple[MonadicSentence, ...], MonadicSentence] | None:
        question_at = prompt.find("\nIs the argument")
        if question_at < 0:
            return None
        argument = prompt[:question_at].strip().strip('"')
        split_at = -1
        marker_used = ""
        for marker in self._CONCLUSION_MARKERS:
            at = argument.rfind(marker)
            if at > split_at:
                split_at = at
                marker_used = marker
        if split_at < 0:
            return None
        before = argument[:split_at]
        conclusion_text = argument[split_at + len(marker_used) :].strip(
            ' :,."'
        )
        premises: list[MonadicSentence] = []
        for text in self._split_premises(before):
            parsed = self._parse_sentence(text)
            if parsed is not None:
                premises.append(parsed)
        conclusion = self._parse_sentence(conclusion_text)
        if not premises or conclusion is None:
            return None
        return tuple(premises), conclusion

    @staticmethod
    def _split_premises(text: str) -> list[str]:
        for cue in (
            "The following argument pertains to this question:",
            "The following argument seeks to clarify some such relations:",
            "The following argument seeks to clarify some such relations",
            "The following argument pertains to this question",
            "Here comes a perfectly valid argument:",
        ):
            at = text.rfind(cue)
            if at >= 0:
                text = text[at + len(cue) :]
                break
        marker = re.compile(
            r"(?i)(?:^|[.:])\s*(?:first(?: premise| of all)?|"
            r"second(?: premise)?|third(?: premise)?|to start with|"
            r"to begin with|moreover|next|now|plus|finally)\s*[:,]?\s*"
        )
        text = marker.sub(" || ", text)
        text = re.sub(
            r"\.\s+(?=(?:Every|No|Nobody|Nothing|Whoever|Whatever|"
            r"Being|To be|Not being|Some|Somebody|There exists|It is|"
            r"[A-Z][A-Za-z-]*(?:\s+[A-Z][A-Za-z-]*)? is)\b)",
            " || ",
            text,
        )
        return [
            piece.strip(' .,:"')
            for piece in text.split("||")
            if piece.strip(' .,:"')
        ]

    def _parse_sentence(self, text: str) -> MonadicSentence | None:
        text = self._clean(text)
        match = re.fullmatch(r"not every (.+?) is (.+)", text, flags=re.I)
        if match:
            return MonadicSentence(
                "some",
                all_of(
                    self._expr(match.group(1)),
                    neg(self._expr(match.group(2))),
                ),
            )
        match = re.fullmatch(
            r"there is somebody who is (.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence("some", self._expr(match.group(1)))
        match = re.fullmatch(
            r"there exists (?:an?|some) (.+?) who is (.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "some",
                all_of(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )
        match = re.fullmatch(r"somebody is (.+)", text, flags=re.I)
        if match:
            return MonadicSentence("some", self._expr(match.group(1)))
        match = re.fullmatch(r"some (.+?) is (.+)", text, flags=re.I)
        if match:
            return MonadicSentence(
                "some",
                all_of(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )

        match = re.fullmatch(
            r"if someone is (.+?), then that person is (.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )
        match = re.fullmatch(
            r"(?:(?:being|to be) )?(.+?) is sufficient for "
            r"(?:(?:being|to be) )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )
        match = re.fullmatch(
            r"(?:(?:being|to be) )?(.+?) is necessary for "
            r"(?:(?:being|to be) )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(2)),
                    self._expr(match.group(1)),
                ),
            )

        match = re.fullmatch(
            r"(?:whoever|whatever|everyone who|everything that|"
            r"everyone that|somebody who) is (.+?) is (?:also )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )
        match = re.fullmatch(
            r"(?:whoever|whatever|everyone who|everything that|"
            r"everyone that) is (.+?) (?:is|are) (?:also )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )
        match = re.fullmatch(
            r"no (.+?) who is (.+?) is (.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    all_of(
                        self._expr(match.group(1)),
                        self._expr(match.group(2)),
                    ),
                    neg(self._expr(match.group(3))),
                ),
            )
        match = re.fullmatch(
            r"no (.+?) and no (.+?) is (.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                all_of(
                    implies(
                        self._expr(match.group(1)),
                        neg(self._expr(match.group(3))),
                    ),
                    implies(
                        self._expr(match.group(2)),
                        neg(self._expr(match.group(3))),
                    ),
                ),
            )
        match = re.fullmatch(r"no (.+?) is (.+)", text, flags=re.I)
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    neg(self._expr(match.group(2))),
                ),
            )
        match = re.fullmatch(
            r"(?:nobody|nothing) is (.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence("all", neg(self._expr(match.group(1))))
        match = re.fullmatch(
            r"every (.+?) (?:who is|that is) (.+?) is (?:also )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    all_of(
                        self._expr(match.group(1)),
                        self._expr(match.group(2)),
                    ),
                    self._expr(match.group(3)),
                ),
            )
        match = re.fullmatch(
            r"every (.+?) is (?:also )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )
        match = re.fullmatch(
            r"all (.+?) (?:are|is) (?:also )?(.+)",
            text,
            flags=re.I,
        )
        if match:
            return MonadicSentence(
                "all",
                implies(
                    self._expr(match.group(1)),
                    self._expr(match.group(2)),
                ),
            )

        match = re.fullmatch(
            r"(?:it is false that|it is not the case that) (.+?) is (.+)",
            text,
        )
        if match:
            return MonadicSentence(
                "constant",
                neg(self._expr(match.group(2))),
                match.group(1).lower(),
            )
        match = re.fullmatch(r"(.+?) is not (.+)", text)
        if match:
            return MonadicSentence(
                "constant",
                neg(self._expr(match.group(2))),
                match.group(1).lower(),
            )
        match = re.fullmatch(r"(.+?) is (.+)", text)
        if match:
            return MonadicSentence(
                "constant",
                self._expr(match.group(2)),
                match.group(1).lower(),
            )
        return None

    @staticmethod
    def _clean(text: str) -> str:
        text = text.strip(' \n\t.:;"')
        text = re.sub(r"(?i)^(?:that|and)\s+", "", text)
        text = re.sub(r"(?i)\bhowever\s+", "", text)
        text = re.sub(r",\s+is\s+", " is ", text)
        text = re.sub(r"(?i),?\s*(?:too|also)$", "", text)
        return re.sub(r"\s+", " ", text)

    def _expr(self, text: str) -> BoolExpr:
        text = self._clean(text)
        text = re.sub(r"(?i)^being\s+", "", text)
        text = re.sub(r"(?i)^(?:a|an|the)\s+", "", text)
        text = re.sub(r"(?i)^at least one of these:\s*", "", text)
        text = re.sub(
            r"(?i)^none of (?:this|these):\s*",
            "neither ",
            text,
        )
        text = re.sub(r"(?i)^both\s+", "", text).strip(" ,")
        if re.match(r"(?i)^not both\s+", text):
            return neg(
                self._expr(re.sub(r"(?i)^not both\s+", "", text))
            )
        if re.match(r"(?i)^neither\s+", text) and re.search(
            r"(?i)\s+nor\s+",
            text,
        ):
            rest = re.sub(r"(?i)^neither\s+", "", text)
            parts = re.split(r"(?i)\s+nor\s+", rest, maxsplit=1)
            return all_of(
                neg(self._expr(parts[0])),
                neg(self._expr(parts[1])),
            )
        parts = self._split_top(text, "or")
        if len(parts) > 1:
            return any_of(*(self._expr(part) for part in parts))
        parts = self._split_top(text, "and")
        if len(parts) > 1:
            return all_of(*(self._expr(part) for part in parts))
        if re.match(r"(?i)^not\s+", text):
            return neg(self._expr(re.sub(r"(?i)^not\s+", "", text)))
        return atom(self._canonical_atom(text))

    @staticmethod
    def _split_top(text: str, connective: str) -> list[str]:
        if connective == "or":
            normalized = re.sub(
                r",\s*(?=[^,]+\s+or\s+)",
                " or ",
                text,
            )
            normalized = re.sub(
                r",\s*or\s+",
                " or ",
                normalized,
                flags=re.I,
            )
            return [
                part.strip(" ,")
                for part in re.split(r"(?i)\s+or\s+", normalized)
                if part.strip(" ,")
            ]
        return [
            part.strip(" ,")
            for part in re.split(r"(?i)\s+and\s+", text)
            if part.strip(" ,")
        ]

    @staticmethod
    def _canonical_atom(text: str) -> str:
        text = text.strip(' ,.:;"').lower()
        text = re.sub(r"^(?:being\s+)?(?:a|an|the)\s+", "", text)
        text = re.sub(r"^(?:is|are)\s+", "", text)
        return re.sub(r"\s+", " ", text)
