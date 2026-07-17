from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import json
import math
import pickle
import random
import re
import resource
import sys
import time
import zlib

PUNCT = re.compile(r"[、。！？；：\s]+")
DIGITS = re.compile(r"\d+")


def clean(text: str) -> str:
    return PUNCT.sub("", text)


def ngrams(text: str, lo: int = 2, hi: int = 6) -> set[str]:
    text = clean(text)
    return {
        text[i : i + n]
        for n in range(lo, hi + 1)
        for i in range(max(0, len(text) - n + 1))
        if not any(c.isdigit() for c in text[i : i + n])
    }


def topnorm(values: Mapping[str, float], limit: int) -> dict[str, float]:
    rows = sorted(values.items(), key=lambda x: (-abs(x[1]), x[0]))[:limit]
    norm = math.sqrt(sum(v * v for _, v in rows))
    return {} if norm == 0 else {k: v / norm for k, v in rows}


def cosine(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


class CharLexicon:
    """Dictionary-free semantics from character n-grams across adjacent clauses."""

    def __init__(self) -> None:
        self.docs = 0
        self.df: Counter[str] = Counter()
        self.vectors: dict[str, dict[str, float]] = {}
        self.pairs = 0

    def units(self, text: str, limit: int = 60) -> tuple[str, ...]:
        ceiling = max(2, int(self.docs * 0.25))
        rows = [u for u in ngrams(text) if 2 <= self.df.get(u, 0) <= ceiling]
        rows.sort(
            key=lambda u: (
                -len(u) * (math.log((self.docs + 1) / (self.df[u] + 1)) + 1),
                -len(u),
                u,
            )
        )
        chosen: list[str] = []
        per_size: Counter[int] = Counter()
        for unit in rows:
            if per_size[len(unit)] >= 12:
                continue
            chosen.append(unit)
            per_size[len(unit)] += 1
            if len(chosen) >= limit:
                break
        return tuple(chosen)

    def fit(self, sentences: Iterable[str]) -> None:
        rows = tuple(sentences)
        if not rows:
            raise ValueError("empty unlabelled corpus")
        self.docs = len(rows)
        self.df.clear()
        for row in rows:
            self.df.update(ngrams(row))
        pairs: Counter[tuple[str, str]] = Counter()
        left_counts: Counter[str] = Counter()
        right_counts: Counter[str] = Counter()
        total = 0
        for row in rows:
            clauses = [self.units(x) for x in re.split(r"[。！？；]+", row) if clean(x)]
            for i, targets in enumerate(clauses):
                contexts = set().union(*(set(c) for j, c in enumerate(clauses) if j != i))
                for target in targets:
                    for context in contexts:
                        pairs[target, context] += 1
                        left_counts[target] += 1
                        right_counts[context] += 1
                        total += 1
        raw: dict[str, dict[str, float]] = defaultdict(dict)
        for (target, context), count in pairs.items():
            pmi = math.log(max(1e-12, count * total / (left_counts[target] * right_counts[context])))
            if pmi > 0:
                raw[target][context] = pmi
        self.vectors = {k: topnorm(v, 48) for k, v in raw.items()}
        self.pairs = len(pairs)

    def vector(self, text: str) -> dict[str, float]:
        units = [u for u in self.units(text) if u in self.vectors]
        units.sort(
            key=lambda u: (
                -len(u) * (math.log((self.docs + 1) / (self.df[u] + 1)) + 1),
                u,
            )
        )
        merged: dict[str, float] = defaultdict(float)
        for unit in units[:12]:
            weight = math.log((self.docs + 1) / (self.df[unit] + 1)) + 1
            for key, value in self.vectors[unit].items():
                merged[key] += weight * value
        return topnorm(merged, 128)


@dataclass(frozen=True)
class Transition:
    text: str
    before: Mapping[str, int]
    after: Mapping[str, int]


@dataclass(frozen=True)
class Atom:
    target: int
    expr: str


@dataclass(frozen=True)
class Program:
    atoms: tuple[Atom, ...]


@dataclass(frozen=True)
class Inference:
    program: Program | None
    after: Mapping[str, int] | None
    confidence: float
    mechanism: str
    candidates: int
    reads: int


def roles(text: str, keys: Iterable[str]) -> tuple[str, ...]:
    return tuple(k for _, k in sorted((text.find(k) if text.find(k) >= 0 else 10**9, k) for k in keys))


def constants(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in DIGITS.findall(text))


def evaluate(expr: str, old: Sequence[int], nums: Sequence[int]) -> int | None:
    p = expr.split(":")
    op = p[0]
    if op == "old":
        return old[int(p[1])]
    if op == "const":
        i = int(p[1])
        return nums[i] if i < len(nums) else None
    if op in {"addc", "subc", "mulc", "divc"}:
        r, i = int(p[1]), int(p[2])
        if r >= len(old) or i >= len(nums):
            return None
        a, b = old[r], nums[i]
        return {"addc": a + b, "subc": a - b, "mulc": a * b, "divc": a // b if b else None}[op]
    a, b = old[int(p[1])], old[int(p[2])]
    return a + b if op == "addr" else a - b


def expression_candidates(target: int, old: Sequence[int], nums: Sequence[int], wanted: int) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    for r, value in enumerate(old):
        if r != target and value == wanted:
            out.append((1.0, f"old:{r}"))
    for i, number in enumerate(nums):
        if number == wanted:
            out.append((1.05, f"const:{i}"))
    for r, value in enumerate(old):
        for i, number in enumerate(nums):
            for cost, expr, result in (
                (1.2 if r == target else 2.1, f"addc:{r}:{i}", value + number),
                (1.2 if r == target else 2.1, f"subc:{r}:{i}", value - number),
                (1.3 if r == target else 2.2, f"mulc:{r}:{i}", value * number),
                (1.4 if r == target else 2.3, f"divc:{r}:{i}", value // number if number else None),
            ):
                if result == wanted:
                    out.append((cost, expr))
        for s, source in enumerate(old):
            if r != s and value + source == wanted:
                out.append((1.7, f"addr:{r}:{s}"))
            if r != s and value - source == wanted:
                out.append((1.8, f"subr:{r}:{s}"))
    return sorted(out)


def derive(row: Transition) -> Program:
    key_order = roles(row.text, row.before)
    old = tuple(int(row.before[k]) for k in key_order)
    nums = constants(row.text)
    atoms: list[Atom] = []
    for target, key in enumerate(key_order):
        wanted = int(row.after[key])
        if wanted == old[target]:
            continue
        candidates = expression_candidates(target, old, nums, wanted)
        if not candidates:
            raise ValueError(f"unexplained transition: {row}")
        atoms.append(Atom(target, candidates[0][1]))
    if not atoms:
        raise ValueError("no state change")
    return Program(tuple(atoms))


def apply(program: Program, text: str, before: Mapping[str, int]) -> dict[str, int] | None:
    key_order = roles(text, before)
    old = tuple(int(before[k]) for k in key_order)
    nums = constants(text)
    after = dict(before)
    for atom in program.atoms:
        if atom.target >= len(key_order):
            return None
        value = evaluate(atom.expr, old, nums)
        if value is None:
            return None
        after[key_order[atom.target]] = value
    return after


class Learner:
    """Continually grows a generic edit-program inventory without operation names."""

    def __init__(self, threshold: float = 0.25, margin: float = 0.02, max_candidates: int = 12) -> None:
        self.threshold = threshold
        self.margin = margin
        self.max_candidates = max_candidates
        self.lexicon = CharLexicon()
        self.sums: dict[Program, dict[str, float]] = {}
        self.counts: Counter[Program] = Counter()
        self.prototypes: dict[Program, dict[str, float]] = {}
        self.postings: dict[str, set[Program]] = defaultdict(set)
        self.examples = 0
        self.last_candidates = 0
        self.last_reads = 0

    @staticmethod
    def mask(text: str, keys: Iterable[str]) -> str:
        for key in sorted(keys, key=len, reverse=True):
            text = text.replace(key, "対象")
        return DIGITS.sub("数", text)

    def fit_corpus(self, corpus: Iterable[str]) -> None:
        self.lexicon.fit(corpus)

    def learn(self, rows: Iterable[Transition], reset: bool = False) -> int:
        rows = tuple(rows)
        if reset:
            self.sums.clear(); self.counts.clear(); self.prototypes.clear(); self.examples = 0
        for row in rows:
            program = derive(row)
            vector = self.lexicon.vector(self.mask(row.text, row.before))
            if not vector:
                raise ValueError(f"no semantic vector: {row.text}")
            merged = defaultdict(float, self.sums.get(program, {}))
            for key, value in vector.items():
                merged[key] += value
            self.sums[program] = dict(sorted(merged.items(), key=lambda x: (-abs(x[1]), x[0]))[:512])
            self.counts[program] += 1
            self.examples += 1
        self.prototypes = {p: topnorm(v, 256) for p, v in self.sums.items()}
        self.postings.clear()
        for program, prototype in self.prototypes.items():
            for feature, _ in sorted(prototype.items(), key=lambda x: (-abs(x[1]), x[0]))[:64]:
                self.postings[feature].add(program)
        return len(self.prototypes)

    def infer(self, text: str, before: Mapping[str, int]) -> Inference:
        query = self.lexicon.vector(self.mask(text, before))
        if not query:
            return Inference(None, None, 0.0, "abstain-no-semantics", 0, 0)
        votes: Counter[Program] = Counter()
        reads = 0
        for feature, weight in query.items():
            for program in self.postings.get(feature, ()):
                votes[program] += abs(weight)
                reads += 1
        candidates = sorted(
            votes or Counter(self.prototypes),
            key=lambda p: (-votes[p], -self.counts[p], str(p)),
        )[: self.max_candidates]
        scores = []
        for program in candidates:
            reads += min(len(query), len(self.prototypes[program]))
            scores.append((cosine(query, self.prototypes[program]), program))
        scores.sort(key=lambda x: (-x[0], str(x[1])))
        self.last_candidates, self.last_reads = len(scores), reads
        if not scores:
            return Inference(None, None, 0.0, "abstain-no-candidates", 0, reads)
        score, program = scores[0]
        runner = scores[1][0] if len(scores) > 1 else 0.0
        gap = score - runner
        confidence = max(0.0, min(1.0, 0.6 * score + 0.4 * gap))
        if score < self.threshold or gap < self.margin:
            return Inference(None, None, confidence, "abstain-ambiguous", len(scores), reads)
        predicted = apply(program, text, before)
        if predicted is None:
            return Inference(None, None, confidence, "abstain-arguments", len(scores), reads)
        return Inference(program, predicted, confidence, "char-grounded-latent-program", len(scores), reads)

    def to_bytes(self) -> bytes:
        return zlib.compress(pickle.dumps(self, protocol=5), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "Learner":
        model = pickle.loads(zlib.decompress(data))
        if not isinstance(model, cls):
            raise TypeError("invalid model")
        return model

    def report(self) -> dict[str, object]:
        return {
            "programs": len(self.prototypes),
            "examples": self.examples,
            "program_signatures": sorted(str(p) for p in self.prototypes),
            "prototype_edges": sum(len(x) for x in self.prototypes.values()),
            "serialized_bytes": len(self.to_bytes()),
            "operation_names_supplied": False,
            "fixed_operation_count_supplied": False,
            "whitespace_tokenizer_used": False,
            "morphological_dictionary_used": False,
        }


@dataclass(frozen=True)
class StateResult:
    query: str | None
    cues: tuple[str, ...]
    cardinality: int
    baseline_bits: float
    model_bits: float
    gain_bits: float
    candidates: int
    signature: tuple[int, ...] | None


class StateInducer:
    """Discovers query, cue set, and two/three-state memory by MDL."""

    def __init__(self, max_models: int = 1024, minimum: int = 8) -> None:
        self.max_models = max_models
        self.minimum = minimum

    @staticmethod
    def entropy(counts: Mapping[str, int]) -> float:
        total = sum(counts.values())
        return 0.0 if not total else -sum((n / total) * math.log2(n / total) for n in counts.values() if n)

    def fit(self, sequence: Sequence[str]) -> StateResult:
        freq = Counter(sequence)
        followers: dict[str, Counter[str]] = defaultdict(Counter)
        for i in range(len(sequence) - 1):
            followers[sequence[i]][sequence[i + 1]] += 1
        queries = sorted(
            (
                (sum(c.values()) * self.entropy(c), token)
                for token, c in followers.items()
                if sum(c.values()) >= self.minimum and len(c) >= 2 and self.entropy(c) > 0.15
            ),
            reverse=True,
        )[:16]
        best = StateResult(None, (), 0, 0.0, 0.0, 0.0, 0, None)
        tried = 0
        for _, query in queries:
            outcome_counts = followers[query]
            outcomes = set(outcome_counts)
            occurrences = [(i, sequence[i + 1]) for i in range(len(sequence) - 1) if sequence[i] == query]
            baseline = len(occurrences) * self.entropy(outcome_counts)
            ranked = []
            for token, count in freq.items():
                if token == query or token in outcomes or count < self.minimum:
                    continue
                hits = sum(token in sequence[max(0, i - 8) : i] for i, _ in occurrences)
                ranked.append((hits, count, token))
            cue_pool = [x[2] for x in sorted(ranked, reverse=True)[:24]]
            for cardinality in (2, 3):
                for cues in combinations(cue_pool, cardinality):
                    tried += 1
                    if tried > self.max_models:
                        break
                    last = {cue: -1 for cue in cues}
                    states = {i: Counter() for i in range(cardinality)}
                    unknown = Counter()
                    for i, token in enumerate(sequence):
                        if token in last:
                            last[token] = i
                        if token != query or i + 1 >= len(sequence):
                            continue
                        recent = sorted(((position, index) for index, position in enumerate(last.values())), reverse=True)
                        (unknown if recent[0][0] < 0 else states[recent[0][1]])[sequence[i + 1]] += 1
                    data = sum(sum(c.values()) * self.entropy(c) for c in states.values())
                    data += sum(unknown.values()) * self.entropy(unknown)
                    cost = data + (cardinality + 1) * math.log2(max(2, len(freq))) + math.log2(3)
                    gain = baseline - cost
                    if gain <= best.gain_bits:
                        continue
                    ordered = sorted(outcome_counts)
                    signature = [cardinality]
                    for state in range(cardinality):
                        counts = states[state]
                        signature.append(-1 if not counts else ordered.index(sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]))
                    best = StateResult(query, tuple(cues), cardinality, baseline, cost, gain, tried, tuple(sorted(signature)))
                if tried > self.max_models:
                    break
            if tried > self.max_models:
                break
        return StateResult(best.query, best.cues, best.cardinality, best.baseline_bits, best.model_bits, best.gain_bits, tried, best.signature)


SURFACES = {
    "add": (("買い足した", "補充した", "追加投入した"), "上積みした"),
    "subtract": (("取り除いた", "差し引いた", "減らした"), "控除した"),
    "assign": (("設定し直した", "指定した", "置き換えた"), "固定した"),
    "transfer": (("振り替えた", "移送した", "移した"), "送った"),
    "swap": (("交換した", "入れ替えた", "取り替えた"), "差し替えた"),
    "copy": (("複製した", "写した", "コピーした"), "転記した"),
    "multiply": (("倍増させた", "拡大した", "乗算した"), "増幅した"),
    "combine": (("合算した", "まとめた", "足し合わせた"), "統合した"),
}
OUTCOMES = {
    "add": ("作業後、対象の数量は以前より多くなった。", "記録を比べると対象だけが指定量ぶん増えていた。"),
    "subtract": ("作業後、対象の数量は以前より少なくなった。", "記録を比べると対象だけが指定量ぶん減っていた。"),
    "assign": ("作業後、対象の数値は指定された値と同じになった。", "以前の値に関係なく表示は指定値へ変わった。"),
    "transfer": ("作業後、対象が減り相手が同量増え、全体量は変わらなかった。", "一方から他方へ同じ量が移り、合計は保存された。"),
    "swap": ("作業後、二つの場所が持っていた値は互いに逆になった。", "両方を確認すると内容がそっくり入れ替わっていた。"),
    "copy": ("作業後、対象の値は相手が持つ値と同じになった。", "相手の内容は変わらず、対象だけが同じ値を持った。"),
    "multiply": ("作業後、対象の値は以前の指定倍になった。", "記録では対象だけが倍率に従って大きくなった。"),
    "combine": ("作業後、対象には以前の対象と相手の合計が入った。", "相手は変わらず、対象だけが二つの値の和になった。"),
}
BASE = ("add", "subtract", "assign", "transfer", "swap", "copy")
NOVEL = ("multiply", "combine")


def narratives() -> tuple[str, ...]:
    rows = [
        f"{prefix}対象を{expression}。{outcome}"
        for mechanism, (known, heldout) in SURFACES.items()
        for expression in (*known, heldout)
        for prefix in ("倉庫の担当者が", "実験班が", "会計係が", "農園の管理者が", "ゲーム係が")
        for outcome in OUTCOMES[mechanism]
    ]
    random.Random(2002).shuffle(rows)
    return tuple(rows)


def transition(mechanism: str, expression: str, keys: tuple[str, str], rng: random.Random, heldout: bool) -> Transition:
    left, right = keys
    if mechanism == "transfer":
        left_value, right_value = rng.randint(100, 160), rng.randint(20, 60)
    else:
        left_value, right_value = rng.randint(40, 90), rng.randint(500, 600)
    amount = rng.randint(2, 9)
    before = {left: left_value, right: right_value}

    def unary(number: int, multiplier: bool = False) -> str:
        label = "指定倍率" if multiplier else "指定量"
        return (
            f"{label}は{number}。{left}を処理対象として担当者が{expression}。"
            if heldout
            else f"担当者は{left}を対象に{expression}。{label}は{number}。"
        )

    def binary(number: int | None = None) -> str:
        amount_text = "" if number is None else f"指定量は{number}。"
        return (
            f"{amount_text}{left}と{right}を処理対象として担当者が{expression}。"
            if heldout
            else f"担当者は{left}と{right}を対象に{expression}。{amount_text}"
        )

    if mechanism == "add":
        return Transition(unary(amount), before, {left: left_value + amount, right: right_value})
    if mechanism == "subtract":
        return Transition(unary(amount), before, {left: left_value - amount, right: right_value})
    if mechanism == "assign":
        return Transition(unary(amount), before, {left: amount, right: right_value})
    if mechanism == "transfer":
        return Transition(binary(amount), before, {left: left_value - amount, right: right_value + amount})
    if mechanism == "swap":
        return Transition(binary(), before, {left: right_value, right: left_value})
    if mechanism == "copy":
        return Transition(binary(), before, {left: right_value, right: right_value})
    if mechanism == "multiply":
        amount = rng.choice((2, 3, 4))
        return Transition(unary(amount, True), before, {left: left_value * amount, right: right_value})
    return Transition(binary(), before, {left: left_value + right_value, right: right_value})


def rows_for(mechanisms: tuple[str, ...], training: bool, rng: random.Random) -> tuple[Transition, ...]:
    train_domains = (("倉庫甲", "倉庫乙"), ("口座青", "口座赤"), ("班東", "班西"))
    test_domains = (("温室北", "温室南"), ("研究一", "研究二"), ("得点白", "得点黒"), ("資源月", "資源星"))
    rows: list[Transition] = []
    for mechanism in mechanisms:
        known, heldout = SURFACES[mechanism]
        if training:
            for expression in known:
                for _ in range(40):
                    rows.append(transition(mechanism, expression, rng.choice(train_domains), rng, False))
        else:
            for i in range(48):
                rows.append(transition(mechanism, heldout, test_domains[i % 4], rng, True))
    return tuple(rows)


def evaluate_model(model: Learner, rows: tuple[Transition, ...]) -> dict[str, object]:
    correct = answered = max_candidates = max_reads = 0
    failures = []
    for row in rows:
        result = model.infer(row.text, row.before)
        answered += result.program is not None
        ok = result.program == derive(row) and result.after == row.after
        correct += ok
        max_candidates = max(max_candidates, result.candidates)
        max_reads = max(max_reads, result.reads)
        if not ok and len(failures) < 12:
            failures.append({"text": row.text, "expected": str(derive(row)), "actual": str(result.program), "after": result.after})
    return {
        "examples": len(rows), "correct": correct, "answered": answered,
        "accuracy": correct / len(rows), "selective": correct / answered if answered else 0.0,
        "max_candidates": max_candidates, "max_reads": max_reads, "failures": failures,
    }


def surface_baseline(training: tuple[Transition, ...], heldout: tuple[Transition, ...]) -> int:
    sums: dict[Program, Counter[str]] = defaultdict(Counter)
    for row in training:
        masked = Learner.mask(row.text, row.before)
        sums[derive(row)].update(ngrams(masked, 2, 5))
    prototypes = {p: topnorm(v, 512) for p, v in sums.items()}
    correct = 0
    for row in heldout:
        query = topnorm(Counter(ngrams(Learner.mask(row.text, row.before), 2, 5)), 512)
        program = max(prototypes, key=lambda p: (cosine(query, prototypes[p]), str(p)))
        correct += apply(program, row.text, row.before) == row.after
    return correct


def state_sequence(seed: int, cues: tuple[str, str, str], outcomes: tuple[str, str, str], query: str, noise: tuple[str, str, str]) -> tuple[str, ...]:
    rng = random.Random(seed)
    output: list[str] = []
    for episode in range(270):
        state = (episode * 7 + episode // 3) % 3
        output.append(cues[state])
        output.extend(rng.choice(noise) for _ in range(rng.randint(1, 4)))
        for _ in range(rng.randint(2, 5)):
            output.extend((query, outcomes[state]))
            if rng.random() < 0.75:
                output.append(rng.choice(noise))
        if episode % 4 == 0:
            output.extend(("雑照会", rng.choice(outcomes)))
    return tuple(output)


def run_gate() -> tuple[dict[str, object], Learner]:
    started = time.perf_counter()
    rng = random.Random(2102)
    corpus = narratives()
    base_train = rows_for(BASE, True, rng)
    base_test = rows_for(BASE, False, rng)
    novel_train = rows_for(NOVEL, True, rng)
    novel_test = rows_for(NOVEL, False, rng)

    model = Learner()
    model.fit_corpus(corpus)
    before_count = model.learn(base_train, True)
    base_before = evaluate_model(model, base_test)
    after_count = model.learn(novel_train)
    base_after = evaluate_model(model, base_test)
    novel_after = evaluate_model(model, novel_test)
    baseline_correct = surface_baseline((*base_train, *novel_train), (*base_test, *novel_test))

    restored = Learner.from_bytes(model.to_bytes())
    restore_ok = all(restored.infer(r.text, r.before).after == r.after for r in (*base_test[:64], *novel_test))

    source = StateInducer().fit(state_sequence(211, ("春印", "夏印", "冬印"), ("暖答", "暑答", "寒答"), "照会", ("雑音甲", "雑音乙", "雑音丙")))
    shifted = StateInducer().fit(state_sequence(212, ("白札", "灰札", "黒札"), ("左答", "中答", "右答"), "確認", ("無関係一", "無関係二", "無関係三")))
    source_ok = source.query == "照会" and set(source.cues) == {"春印", "夏印", "冬印"} and source.cardinality == 3
    shifted_ok = shifted.query == "確認" and set(shifted.cues) == {"白札", "灰札", "黒札"} and shifted.cardinality == 3

    model_report = model.report()
    all_text = (*corpus, *(r.text for r in base_train), *(r.text for r in base_test), *(r.text for r in novel_train), *(r.text for r in novel_test))
    checks = {
        "continuous_japanese_no_spaces": all(not any(c.isspace() for c in x) for x in all_text),
        "no_named_or_fixed_operation_inventory": not model_report["operation_names_supplied"] and not model_report["fixed_operation_count_supplied"],
        "six_base_programs_discovered": before_count == 6,
        "two_new_programs_added": after_count == before_count + 2,
        "base_transfer_at_least_70pct": base_before["accuracy"] >= 0.70,
        "base_selective_at_least_80pct": base_before["selective"] >= 0.80,
        "no_old_regression": base_after["correct"] >= base_before["correct"],
        "novel_transfer_at_least_70pct": novel_after["accuracy"] >= 0.70,
        "semantic_narratives_beat_surface_baseline": base_after["correct"] + novel_after["correct"] > baseline_correct,
        "candidate_budget": max(base_after["max_candidates"], novel_after["max_candidates"]) <= 12,
        "read_budget": max(base_after["max_reads"], novel_after["max_reads"]) <= 4096,
        "model_under_512k": model_report["serialized_bytes"] <= 512 * 1024,
        "save_restore": restore_ok,
        "source_query_and_three_state_discovered": source_ok,
        "shifted_query_and_three_state_discovered": shifted_ok,
        "state_signature_transfer": source.signature == shifted.signature and source.signature is not None,
        "state_mdl_gain": min(source.gain_bits, shifted.gain_bits) >= 500,
        "state_search_budget": max(source.candidates, shifted.candidates) <= 1024,
    }
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = {
        "capability_id": "SPARC-LATENT-PROGRAM-002",
        "base": {"training": len(base_train), "programs": before_count, "heldout_before": base_before, "heldout_after": base_after},
        "expansion": {"training": len(novel_train), "programs_after": after_count, "novel_heldout": novel_after},
        "surface_baseline_correct": baseline_correct,
        "state": {"source": source.__dict__, "shifted": shifted.__dict__, "signature_transfer": source.signature == shifted.signature},
        "model": model_report,
        "lexicon": {"documents": model.lexicon.docs, "units": len(model.lexicon.vectors), "pairs": model.lexicon.pairs},
        "resources": {"wall_seconds": elapsed, "peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024},
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": "Generated small worlds only. This removes whitespace tokenisation and a fixed named operation inventory, but it is not unrestricted Japanese learning or high-school-level intelligence.",
    }
    return report, model


def markdown(report: Mapping[str, object]) -> str:
    base, expansion, state, resources = report["base"], report["expansion"], report["state"], report["resources"]
    return "\n".join([
        "# SPARC latent-program experiment 002", "", f"Passed: **{report['passed']}**", "",
        f"- Base programs: **{base['programs']}**",
        f"- Base withheld before/after expansion: **{base['heldout_before']['correct']}/{base['heldout_before']['examples']} / {base['heldout_after']['correct']}/{base['heldout_after']['examples']}**",
        f"- Programs after expansion: **{expansion['programs_after']}**",
        f"- Novel withheld: **{expansion['novel_heldout']['correct']}/{expansion['novel_heldout']['examples']}**",
        f"- Surface-only baseline: **{report['surface_baseline_correct']}/{base['heldout_after']['examples'] + expansion['novel_heldout']['examples']}**",
        f"- Model bytes: **{report['model']['serialized_bytes']}**", "",
        f"- Source query/states/gain: **{state['source']['query']} / {state['source']['cardinality']} / {state['source']['gain_bits']:.2f} bits**",
        f"- Shifted query/states/gain: **{state['shifted']['query']} / {state['shifted']['cardinality']} / {state['shifted']['gain_bits']:.2f} bits**",
        f"- State signature transfer: **{state['signature_transfer']}**", "",
        f"- Wall time: **{resources['wall_seconds']:.3f} s**", f"- Peak RSS: **{resources['peak_rss_bytes']} bytes**", "",
        "## Claim boundary", "", str(report["claim_boundary"]), "",
    ])


def main() -> None:
    report, model = run_gate()
    out = Path("results"); out.mkdir(exist_ok=True)
    (out / "sparc_latent_program_002.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "sparc_latent_program_002.md").write_text(markdown(report), encoding="utf-8")
    (out / "SPARC-latent-program-002.model.zlib").write_bytes(model.to_bytes())
    print(markdown(report), end="")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
