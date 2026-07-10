from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import log2
import random
import struct

import numpy as np

ALPHABET_SIZE = 256
MAGIC = b"MPLM1"


def _encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be non-negative")
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def _decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError("truncated varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")


def make_micro_corpus(line_count: int, seed: int) -> bytes:
    """Deterministic Japanese/English/code corpus with unseen test combinations."""
    rng = random.Random(seed)
    names = ["太郎", "花子", "山口", "佐藤", "鈴木", "田中", "アリス", "ボブ"]
    topics = ["最小メモリ", "ニューラルネット", "言語モデル", "画像認識", "Python", "数学", "圧縮", "推論"]
    actions = ["説明します", "検証します", "実装します", "比較します", "最適化します", "分析します"]
    objects = ["状態", "規則", "メモリ", "計算量", "予測誤差", "プログラム"]
    lines: list[str] = []
    for index in range(line_count):
        kind = rng.randrange(5)
        name = rng.choice(names)
        topic = rng.choice(topics)
        action = rng.choice(actions)
        obj = rng.choice(objects)
        if kind == 0:
            lines.append(
                f"ユーザー: {name}さん、{topic}について教えてください。\n"
                f"AI: {topic}の{obj}を{action}。\n"
            )
        elif kind == 1:
            x = rng.randrange(2, 100)
            y = rng.randrange(2, 100)
            lines.append(
                f"def calc_{index % 17}(x: int) -> int:\n"
                f"    return x * {x} + {y}\n\n"
            )
        elif kind == 2:
            status = "ok" if index % 3 else "retry"
            lines.append(f"[{index % 13:02d}] {topic} | {obj} | status={status}\n")
        elif kind == 3:
            bits = "".join(rng.choice("01") for _ in range(16))
            lines.append(
                f"WRITE key={index % 8} value={index % 2}; "
                f"QUERY key={index % 8}; answer={index % 2}; bits={bits}\n"
            )
        else:
            lines.append(f"{topic}では、{obj}が小さいほど効率的です。次に{obj}を{action}。\n")
    return "".join(lines).encode("utf-8")


def _collect_counts(data: bytes, maximum_order: int) -> list[dict[bytes, Counter[int]]]:
    tables: list[dict[bytes, Counter[int]]] = [defaultdict(Counter) for _ in range(maximum_order + 1)]
    for index, symbol in enumerate(data):
        tables[0][b""][symbol] += 1
        for order in range(1, min(maximum_order, index) + 1):
            tables[order][data[index - order:index]][symbol] += 1
    return tables


@dataclass(frozen=True)
class Distribution:
    counts: dict[int, int]
    total: int

    def probability(self, symbol: int, alpha: float) -> float:
        return (self.counts.get(symbol, 0) + alpha) / (self.total + alpha * ALPHABET_SIZE)


@dataclass(frozen=True)
class SelectedRule:
    context: bytes
    distribution: Distribution
    parent: bytes
    validation_gain_bits: float
    description_bits: int


class SparseResidualTrainer:
    """Greedy MDL learner: add a context only when it pays for its own description."""

    def __init__(
        self,
        maximum_order: int = 8,
        alpha: float = 0.25,
        minimum_fit_count: int = 10,
        minimum_selection_count: int = 5,
        description_weight: float = 1.0,
    ) -> None:
        self.maximum_order = maximum_order
        self.alpha = alpha
        self.minimum_fit_count = minimum_fit_count
        self.minimum_selection_count = minimum_selection_count
        self.description_weight = description_weight
        self.rules: dict[bytes, SelectedRule] = {}

    @staticmethod
    def _varint_bits(value: int) -> int:
        return 8 * len(_encode_varint(value))

    def _description_bits(self, context: bytes, counts: Counter[int]) -> int:
        return (
            8
            + 8 * len(context)
            + 16
            + sum(8 + self._varint_bits(count) for count in counts.values())
            + self._varint_bits(sum(counts.values()))
        )

    def _nearest_selected_suffix(self, context: bytes) -> bytes:
        for cut in range(1, len(context) + 1):
            suffix = context[cut:]
            if suffix in self.rules:
                return suffix
        return b""

    def fit(self, fit_data: bytes, selection_data: bytes) -> None:
        fit_tables = _collect_counts(fit_data, self.maximum_order)
        selection_tables = _collect_counts(selection_data, self.maximum_order)
        root_counts = fit_tables[0][b""]
        root_distribution = Distribution(dict(root_counts), sum(root_counts.values()))
        self.rules = {
            b"": SelectedRule(
                context=b"",
                distribution=root_distribution,
                parent=b"",
                validation_gain_bits=0.0,
                description_bits=self._description_bits(b"", root_counts),
            )
        }

        for order in range(1, self.maximum_order + 1):
            for context, selection_counts in selection_tables[order].items():
                fit_counts = fit_tables[order].get(context)
                if fit_counts is None:
                    continue
                fit_total = sum(fit_counts.values())
                selection_total = sum(selection_counts.values())
                if fit_total < self.minimum_fit_count or selection_total < self.minimum_selection_count:
                    continue

                parent_context = self._nearest_selected_suffix(context)
                parent = self.rules[parent_context].distribution
                parent_nll = 0.0
                local_nll = 0.0
                for symbol, count in selection_counts.items():
                    parent_nll -= count * log2(parent.probability(symbol, self.alpha))
                    local_probability = (fit_counts.get(symbol, 0) + self.alpha) / (
                        fit_total + self.alpha * ALPHABET_SIZE
                    )
                    local_nll -= count * log2(local_probability)

                gain = parent_nll - local_nll
                description_bits = self._description_bits(context, fit_counts)
                if gain > self.description_weight * description_bits:
                    self.rules[context] = SelectedRule(
                        context=context,
                        distribution=Distribution(dict(fit_counts), fit_total),
                        parent=parent_context,
                        validation_gain_bits=gain,
                        description_bits=description_bits,
                    )

    def refit(self, all_training_data: bytes) -> None:
        tables = _collect_counts(all_training_data, self.maximum_order)
        updated: dict[bytes, SelectedRule] = {}
        for context, rule in self.rules.items():
            counts = tables[len(context)].get(context, Counter())
            updated[context] = SelectedRule(
                context=context,
                distribution=Distribution(dict(counts), sum(counts.values())),
                parent=rule.parent,
                validation_gain_bits=rule.validation_gain_bits,
                description_bits=self._description_bits(context, counts),
            )
        self.rules = updated

    def compile(self, profile_data: bytes, shortcut_budget: int = 512) -> "CompiledResidualLM":
        return CompiledResidualLM.from_rules(self.rules, self.alpha, profile_data, shortcut_budget)


@dataclass
class _BuildNode:
    edges: dict[int, int]
    fail: int = 0
    terminal_rule: int | None = None
    output_rule: int = 0


@dataclass(frozen=True)
class CompiledNode:
    fail: int
    output_rule: int
    transitions: dict[int, int]


@dataclass(frozen=True)
class UTF8State:
    remaining: int = 0
    low: int = 0x80
    high: int = 0xBF


def _utf8_step(state: UTF8State, byte: int) -> UTF8State | None:
    if state.remaining == 0:
        if byte <= 0x7F:
            return UTF8State()
        if 0xC2 <= byte <= 0xDF:
            return UTF8State(1)
        if byte == 0xE0:
            return UTF8State(2, 0xA0, 0xBF)
        if 0xE1 <= byte <= 0xEC or 0xEE <= byte <= 0xEF:
            return UTF8State(2)
        if byte == 0xED:
            return UTF8State(2, 0x80, 0x9F)
        if byte == 0xF0:
            return UTF8State(3, 0x90, 0xBF)
        if 0xF1 <= byte <= 0xF3:
            return UTF8State(3)
        if byte == 0xF4:
            return UTF8State(3, 0x80, 0x8F)
        return None
    if not state.low <= byte <= state.high:
        return None
    if state.remaining == 1:
        return UTF8State()
    return UTF8State(state.remaining - 1)


class CompiledResidualLM:
    def __init__(self, alpha: float, distributions: list[Distribution], nodes: list[CompiledNode]) -> None:
        self.alpha = alpha
        self.distributions = distributions
        self.nodes = nodes

    @classmethod
    def from_rules(
        cls,
        rules: dict[bytes, SelectedRule],
        alpha: float,
        profile_data: bytes,
        shortcut_budget: int,
    ) -> "CompiledResidualLM":
        contexts = sorted(rules, key=lambda value: (len(value), value))
        rule_ids = {context: index for index, context in enumerate(contexts)}
        distributions = [rules[context].distribution for context in contexts]
        build_nodes = [_BuildNode(edges={}, terminal_rule=rule_ids[b""], output_rule=rule_ids[b""])]

        for context in contexts:
            if not context:
                continue
            state = 0
            for byte in context:
                next_state = build_nodes[state].edges.get(byte)
                if next_state is None:
                    next_state = len(build_nodes)
                    build_nodes[state].edges[byte] = next_state
                    build_nodes.append(_BuildNode(edges={}))
                state = next_state
            build_nodes[state].terminal_rule = rule_ids[context]

        queue: deque[int] = deque(build_nodes[0].edges.values())
        while queue:
            state = queue.popleft()
            node = build_nodes[state]
            if node.terminal_rule is not None:
                node.output_rule = node.terminal_rule
            else:
                node.output_rule = build_nodes[node.fail].output_rule
            for byte, child in node.edges.items():
                queue.append(child)
                fallback = node.fail
                while fallback and byte not in build_nodes[fallback].edges:
                    fallback = build_nodes[fallback].fail
                build_nodes[child].fail = build_nodes[fallback].edges.get(byte, 0)

        pair_frequency: Counter[tuple[int, int]] = Counter()
        pair_result: dict[tuple[int, int], tuple[int, int]] = {}
        state = 0
        for byte in profile_data:
            original = state
            hops = 0
            while state and byte not in build_nodes[state].edges:
                hops += 1
                state = build_nodes[state].fail
            state = build_nodes[state].edges.get(byte, 0)
            pair = (original, byte)
            pair_frequency[pair] += 1
            pair_result[pair] = (state, hops)

        ranked = sorted(
            (
                (pair_frequency[pair] * pair_result[pair][1], pair, pair_result[pair][0])
                for pair in pair_frequency
                if pair_result[pair][1] > 0
            ),
            reverse=True,
        )
        shortcuts = {pair: target for _, pair, target in ranked[:shortcut_budget]}

        compiled_nodes: list[CompiledNode] = []
        for state, node in enumerate(build_nodes):
            transitions = dict(node.edges)
            for (source, byte), target in shortcuts.items():
                if source == state:
                    transitions[byte] = target
            compiled_nodes.append(
                CompiledNode(fail=node.fail, output_rule=node.output_rule, transitions=transitions)
            )
        return cls(alpha=alpha, distributions=distributions, nodes=compiled_nodes)

    @property
    def runtime_state_bits(self) -> int:
        return max(1, (len(self.nodes) - 1).bit_length())

    def _transition(self, state: int, byte: int) -> tuple[int, int]:
        checks = 0
        while True:
            checks += 1
            target = self.nodes[state].transitions.get(byte)
            if target is not None:
                return target, checks
            if state == 0:
                return 0, checks
            state = self.nodes[state].fail

    def evaluate(self, data: bytes) -> dict[str, float]:
        state = 0
        nll_bits = 0.0
        checks = 0
        for byte in data:
            distribution = self.distributions[self.nodes[state].output_rule]
            nll_bits -= log2(distribution.probability(byte, self.alpha))
            state, step_checks = self._transition(state, byte)
            checks += step_checks
        return {
            "bpb": nll_bits / len(data),
            "nll_bits": nll_bits,
            "average_transition_checks": checks / len(data),
        }

    def generate(
        self,
        prompt: str,
        byte_count: int,
        seed: int = 0,
        temperature: float = 0.7,
        enforce_utf8: bool = True,
    ) -> str:
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        rng = np.random.default_rng(seed)
        encoded = prompt.encode("utf-8")
        output = bytearray(encoded)
        state = 0
        utf8_state = UTF8State()
        for byte in encoded:
            if enforce_utf8:
                next_utf8 = _utf8_step(utf8_state, byte)
                if next_utf8 is None:
                    raise ValueError("prompt is not valid UTF-8")
                utf8_state = next_utf8
            state, _ = self._transition(state, byte)

        root = self.distributions[0]
        for _ in range(byte_count):
            distribution = self.distributions[self.nodes[state].output_rule]
            symbols = [
                symbol
                for symbol in distribution.counts
                if not enforce_utf8 or _utf8_step(utf8_state, symbol) is not None
            ]
            if not symbols:
                symbols = [
                    symbol
                    for symbol in root.counts
                    if not enforce_utf8 or _utf8_step(utf8_state, symbol) is not None
                ]
            weights = np.asarray(
                [distribution.counts.get(symbol, 0) + 0.01 * root.counts.get(symbol, 0) for symbol in symbols],
                dtype=np.float64,
            )
            weights = np.power(weights, 1.0 / temperature)
            weights /= weights.sum()
            byte = int(rng.choice(np.asarray(symbols, dtype=np.int64), p=weights))
            output.append(byte)
            if enforce_utf8:
                next_utf8 = _utf8_step(utf8_state, byte)
                if next_utf8 is None:
                    raise RuntimeError("UTF-8 constraint failed")
                utf8_state = next_utf8
            state, _ = self._transition(state, byte)

        while enforce_utf8 and utf8_state.remaining:
            candidates = [symbol for symbol in root.counts if _utf8_step(utf8_state, symbol) is not None]
            byte = max(candidates, key=lambda symbol: root.counts[symbol])
            output.append(byte)
            utf8_state = _utf8_step(utf8_state, byte) or UTF8State()
        return output.decode("utf-8")

    def to_bytes(self) -> bytes:
        out = bytearray(MAGIC)
        out.extend(struct.pack("<f", self.alpha))
        out.extend(_encode_varint(len(self.distributions)))
        out.extend(_encode_varint(len(self.nodes)))
        for distribution in self.distributions:
            pairs = sorted(distribution.counts.items())
            out.extend(_encode_varint(len(pairs)))
            for symbol, count in pairs:
                out.append(symbol)
                out.extend(_encode_varint(count))
        for node in self.nodes:
            out.extend(_encode_varint(node.fail))
            out.extend(_encode_varint(node.output_rule))
            pairs = sorted(node.transitions.items())
            out.extend(_encode_varint(len(pairs)))
            for symbol, target in pairs:
                out.append(symbol)
                out.extend(_encode_varint(target))
        return bytes(out)

    @classmethod
    def from_bytes(cls, data: bytes) -> "CompiledResidualLM":
        if not data.startswith(MAGIC):
            raise ValueError("invalid model magic")
        offset = len(MAGIC)
        if offset + 4 > len(data):
            raise ValueError("truncated model")
        alpha = struct.unpack_from("<f", data, offset)[0]
        offset += 4
        distribution_count, offset = _decode_varint(data, offset)
        node_count, offset = _decode_varint(data, offset)
        distributions: list[Distribution] = []
        for _ in range(distribution_count):
            pair_count, offset = _decode_varint(data, offset)
            counts: dict[int, int] = {}
            for _ in range(pair_count):
                if offset >= len(data):
                    raise ValueError("truncated distribution")
                symbol = data[offset]
                offset += 1
                count, offset = _decode_varint(data, offset)
                counts[symbol] = count
            distributions.append(Distribution(counts=counts, total=sum(counts.values())))
        nodes: list[CompiledNode] = []
        for _ in range(node_count):
            fail, offset = _decode_varint(data, offset)
            output_rule, offset = _decode_varint(data, offset)
            transition_count, offset = _decode_varint(data, offset)
            transitions: dict[int, int] = {}
            for _ in range(transition_count):
                if offset >= len(data):
                    raise ValueError("truncated transition")
                symbol = data[offset]
                offset += 1
                target, offset = _decode_varint(data, offset)
                transitions[symbol] = target
            nodes.append(CompiledNode(fail=fail, output_rule=output_rule, transitions=transitions))
        if offset != len(data):
            raise ValueError("trailing model bytes")
        return cls(alpha=alpha, distributions=distributions, nodes=nodes)
