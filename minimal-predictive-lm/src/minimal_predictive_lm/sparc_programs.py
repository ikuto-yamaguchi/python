from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .sparc_language import ReplyResult
from .sparc_raw_induction import RawCurriculumModel

_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _normalise(text: str) -> str:
    text = text.strip().replace("?", "？").replace("!", "！")
    return re.sub(r"\s+", "", text).strip("。！")


def _numbers(text: str) -> tuple[float, ...]:
    return tuple(float(value) for value in _NUMBER_RE.findall(_normalise(text)))


def _answer_number(text: str | float | int) -> float:
    if isinstance(text, (float, int)):
        return float(text)
    found = _numbers(str(text))
    if not found:
        raise ValueError("answer contains no numeric value")
    return found[0]


def _numeric_template(text: str) -> tuple[str, int]:
    index = 0

    def replace(_match: re.Match[str]) -> str:
        nonlocal index
        token = "{N" + str(index) + "}"
        index += 1
        return token

    return _NUMBER_RE.sub(replace, _normalise(text)), index


def _literal_anchors(template: str) -> set[str]:
    literal = re.sub(r"\{N\d+\}", " ", template)
    pieces = [piece for piece in literal.split() if piece]
    anchors: set[str] = set()
    for piece in pieces:
        for size in (5, 4, 3, 2):
            if len(piece) >= size:
                anchors.update(piece[i : i + size] for i in range(len(piece) - size + 1))
        if piece:
            anchors.add(piece)
    return anchors


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.10f}".rstrip("0").rstrip(".")


@dataclass(frozen=True)
class NumericProgram:
    name: str
    arity: int
    complexity: int
    explanation: str

    def run(self, values: Sequence[float]) -> float:
        x = tuple(float(value) for value in values)
        if len(x) != self.arity:
            raise ValueError("program arity mismatch")
        if self.name == "identity0":
            return x[0]
        if self.name == "add2":
            return x[0] + x[1]
        if self.name == "sub01":
            return x[0] - x[1]
        if self.name == "sub10":
            return x[1] - x[0]
        if self.name in {"mul2", "rate_times_time"}:
            return x[0] * x[1]
        if self.name == "div01":
            return x[0] / x[1]
        if self.name == "div10":
            return x[1] / x[0]
        if self.name == "half_product":
            return x[0] * x[1] / 2.0
        if self.name == "percent_of":
            return x[0] * x[1] / 100.0
        if self.name == "discount":
            return x[0] * (1.0 - x[1] / 100.0)
        if self.name == "increase_percent":
            return x[0] * (1.0 + x[1] / 100.0)
        if self.name == "sum3":
            return x[0] + x[1] + x[2]
        if self.name == "mean3":
            return (x[0] + x[1] + x[2]) / 3.0
        if self.name == "product3":
            return x[0] * x[1] * x[2]
        if self.name == "linear_ax_plus_b_eq_c":
            return (x[2] - x[1]) / x[0]
        if self.name == "linear_ax_minus_b_eq_c":
            return (x[2] + x[1]) / x[0]
        raise ValueError(f"unknown program: {self.name}")


PROGRAM_LIBRARY: tuple[NumericProgram, ...] = (
    NumericProgram("identity0", 1, 1, "与えられた値をそのまま使います"),
    NumericProgram("add2", 2, 2, "2つの値を足します"),
    NumericProgram("sub01", 2, 2, "1つ目から2つ目を引きます"),
    NumericProgram("sub10", 2, 2, "2つ目から1つ目を引きます"),
    NumericProgram("mul2", 2, 2, "2つの値を掛けます"),
    NumericProgram("rate_times_time", 2, 2, "割合または速さに時間・量を掛けます"),
    NumericProgram("div01", 2, 2, "1つ目を2つ目で割ります"),
    NumericProgram("div10", 2, 2, "2つ目を1つ目で割ります"),
    NumericProgram("half_product", 2, 3, "2つの値を掛けて2で割ります"),
    NumericProgram("percent_of", 2, 3, "基準値に割合を掛けます"),
    NumericProgram("discount", 2, 4, "基準値から指定割合を引きます"),
    NumericProgram("increase_percent", 2, 4, "基準値に指定割合を加えます"),
    NumericProgram("sum3", 3, 3, "3つの値を足します"),
    NumericProgram("mean3", 3, 4, "3つの値を足して3で割ります"),
    NumericProgram("product3", 3, 3, "3つの値を掛けます"),
    NumericProgram("linear_ax_plus_b_eq_c", 3, 4, "右辺から定数項を引き、係数で割ります"),
    NumericProgram("linear_ax_minus_b_eq_c", 3, 4, "右辺に定数項を足し、係数で割ります"),
)
_PROGRAM_BY_NAME = {program.name: program for program in PROGRAM_LIBRARY}


@dataclass(frozen=True)
class ProgramSchema:
    template: str
    program_name: str
    arity: int
    support: int
    mean_absolute_error: float


@dataclass(frozen=True)
class ProgramInductionResult:
    template: str
    program_name: str
    examples: int
    mean_absolute_error: float
    competing_programs: int


class SparseProgramBank:
    """Sparse local bank of numeric microprograms induced from answers."""

    def __init__(self, max_schemas: int = 100_000, max_candidates: int = 32) -> None:
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.schemas: list[ProgramSchema] = []
        self.template_to_schema: dict[str, int] = {}
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.last_candidates = 0
        self.last_anchor_reads = 0
        self.last_programs_executed = 0

    @staticmethod
    def _fit_program(
        values_and_answers: Sequence[tuple[tuple[float, ...], float]],
    ) -> tuple[NumericProgram, float, int]:
        if not values_and_answers:
            raise ValueError("examples must not be empty")
        arity = len(values_and_answers[0][0])
        viable: list[tuple[float, int, str, NumericProgram]] = []
        for program in PROGRAM_LIBRARY:
            if program.arity != arity:
                continue
            errors: list[float] = []
            valid = True
            for values, answer in values_and_answers:
                try:
                    predicted = program.run(values)
                except (ValueError, ZeroDivisionError, OverflowError):
                    valid = False
                    break
                if not math.isfinite(predicted):
                    valid = False
                    break
                errors.append(abs(predicted - answer))
            if not valid:
                continue
            mae = sum(errors) / len(errors)
            scale = max(
                1.0,
                sum(abs(answer) for _values, answer in values_and_answers)
                / len(values_and_answers),
            )
            normalised = mae / scale
            if normalised <= 1e-8:
                viable.append((normalised, program.complexity, program.name, program))
        if not viable:
            raise ValueError("no numeric microprogram matches all demonstrations")
        viable.sort(key=lambda row: (row[0], row[1], row[2]))
        chosen = viable[0]
        return chosen[3], chosen[0], len(viable)

    def teach(
        self,
        examples: Iterable[tuple[str, str | float | int]],
    ) -> ProgramInductionResult:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two demonstrations are required")
        grouped: dict[str, list[tuple[tuple[float, ...], float]]] = defaultdict(list)
        for problem, answer in rows:
            template, arity = _numeric_template(problem)
            values = _numbers(problem)
            if arity != len(values):
                raise AssertionError("numeric extraction mismatch")
            grouped[template].append((values, _answer_number(answer)))
        if len(grouped) != 1:
            raise ValueError("all demonstrations must share one numeric surface skeleton")
        template, values_and_answers = next(iter(grouped.items()))
        program, mae, competing = self._fit_program(values_and_answers)
        existing = self.template_to_schema.get(template)
        if existing is not None:
            previous = self.schemas[existing]
            self.schemas[existing] = ProgramSchema(
                template=template,
                program_name=program.name,
                arity=program.arity,
                support=previous.support + len(rows),
                mean_absolute_error=mae,
            )
        else:
            if len(self.schemas) >= self.max_schemas:
                raise MemoryError("program schema capacity reached")
            schema_id = len(self.schemas)
            self.schemas.append(
                ProgramSchema(
                    template=template,
                    program_name=program.name,
                    arity=program.arity,
                    support=len(rows),
                    mean_absolute_error=mae,
                )
            )
            self.template_to_schema[template] = schema_id
            for anchor in _literal_anchors(template) or {template}:
                self.postings[anchor].add(schema_id)
        return ProgramInductionResult(template, program.name, len(rows), mae, competing)

    def _candidate_ids(self, text: str) -> list[int]:
        template, _arity = _numeric_template(text)
        routed = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _literal_anchors(template)
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        routes = 0
        for posting_size, neg_length, anchor in routed:
            if votes and posting_size > self.max_candidates * 4:
                break
            weight = (-neg_length) ** 2 / max(1, posting_size)
            for schema_id in self.postings[anchor]:
                votes[schema_id] += weight
                reads += 1
            routes += 1
            if routes >= 8 or len(votes) >= self.max_candidates:
                break
        self.last_anchor_reads = reads
        candidates = [schema_id for schema_id, _score in votes.most_common(self.max_candidates)]
        self.last_candidates = len(candidates)
        return candidates

    def solve(self, problem: str) -> ReplyResult | None:
        template, arity = _numeric_template(problem)
        values = _numbers(problem)
        candidates = self._candidate_ids(problem)
        self.last_programs_executed = 0
        for schema_id in candidates:
            schema = self.schemas[schema_id]
            if schema.template != template or schema.arity != arity:
                continue
            program = _PROGRAM_BY_NAME[schema.program_name]
            try:
                answer = program.run(values)
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            if not math.isfinite(answer):
                continue
            self.last_programs_executed += 1
            return ReplyResult(
                text=f"{_format_number(answer)}です。{program.explanation}。",
                confidence=min(0.99, 0.72 + math.log2(schema.support + 1) * 0.06),
                mechanism="induced-local-microprogram",
                candidates_inspected=len(candidates),
                active_bits=arity,
                estimated_sparse_operations=(
                    self.last_anchor_reads + len(candidates) + program.complexity
                ),
            )
        return None

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-program-hs5",
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "schemas": [asdict(schema) for schema in self.schemas],
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseProgramBank":
        payload = json.loads(zlib.decompress(data))
        bank = cls(int(payload["max_schemas"]), int(payload["max_candidates"]))
        for row in payload["schemas"]:
            schema = ProgramSchema(**row)
            schema_id = len(bank.schemas)
            bank.schemas.append(schema)
            bank.template_to_schema[schema.template] = schema_id
            for anchor in _literal_anchors(schema.template) or {schema.template}:
                bank.postings[anchor].add(schema_id)
        return bank

    def report(self) -> dict[str, int | bool]:
        return {
            "program_schemas": len(self.schemas),
            "anchor_edges": sum(len(ids) for ids in self.postings.values()),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_programs_executed": self.last_programs_executed,
            "global_program_scan_used": False,
        }


class SPARCHS5Model:
    """Shared raw-curriculum memory plus sparse induced numeric programs."""

    def __init__(self, base: RawCurriculumModel | None = None) -> None:
        self.base = base or RawCurriculumModel()
        self.programs = SparseProgramBank()

    def teach_math(
        self,
        examples: Iterable[tuple[str, str | float | int]],
    ) -> ProgramInductionResult:
        return self.programs.teach(examples)

    def reply(self, text: str):
        if _numbers(text):
            solved = self.programs.solve(text)
            if solved is not None:
                return solved
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs5",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "programs": base64.b85encode(self.programs.to_bytes()).decode("ascii"),
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS5Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(RawCurriculumModel.from_bytes(base64.b85decode(payload["base"])))
        model.programs = SparseProgramBank.from_bytes(
            base64.b85decode(payload["programs"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS5Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "raw_curriculum": self.base.report(),
            "programs": self.programs.report(),
            "serialized_bytes": len(self.to_bytes()),
            "shared_model": True,
            "dense_program_network_used": False,
        }
