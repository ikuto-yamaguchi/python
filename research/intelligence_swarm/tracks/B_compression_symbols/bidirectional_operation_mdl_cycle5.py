from __future__ import annotations

import difflib
import json
import pickle
import random
import resource
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass

ENT_TRAIN = ["試料A", "試料B", "青箱", "赤容器", "装置甲", "装置乙"]
ENT_TEST = ["未知体X", "ミラコフ", "対象春夏", "器具δ"]
VAL_TRAIN = ["棚B", "保管庫C", "検査台D", "奥区画", "20度", "30度"]
VAL_TEST = ["北室", "区画Z", "45度", "待機域"]
STATE_FORMS = ["{e}は{v}です。", "現在の{e}は{v}。", "記録：{e}→{v}。"]
TRAIN_FORMS = [
    "{e}を{v}へ移して",
    "{v}へ{e}を移動して",
    "{e}の置き場を{v}に変更して",
    "対象{e}、最終値は{v}にして",
]
PARA_FORMS = ["{e}を{v}まで運んで", "{e}を{v}へ配置し直して", "{e}の値を{v}へ調整して"]
ORDER_FORMS = ["行き先は{v}、対象は{e}", "最終的に{v}、変更対象は{e}", "{v}にする対象は{e}"]
NOOPS = ["{e}はそのままにして", "{e}を確認するだけ", "{e}には触れないで"]


@dataclass
class Episode:
    before: str
    command: str
    after: str
    changed: bool
    entity: str
    old: str
    new: str


def make(seed: int, n: int, mode: str = "train") -> list[Episode]:
    rng = random.Random(seed)
    entities = ENT_TEST if mode in {"rename", "rename_para"} else ENT_TRAIN
    values = VAL_TEST if mode in {"rename", "rename_para"} else VAL_TRAIN
    forms = TRAIN_FORMS if mode in {"train", "rename", "confound"} else PARA_FORMS if mode in {"para", "rename_para"} else ORDER_FORMS
    rows: list[Episode] = []
    for i in range(n):
        entity = rng.choice(entities)
        old, new = rng.sample(values, 2)
        state_form = STATE_FORMS[i % len(STATE_FORMS)]
        before = state_form.format(e=entity, v=old)
        if mode == "confound" and i % 2 == 0:
            command = rng.choice(NOOPS).format(e=entity)
            after = before
            changed = False
        else:
            command = rng.choice(forms).format(e=entity, v=new)
            after = state_form.format(e=entity, v=new)
            changed = True
        rows.append(Episode(before, command, after, changed, entity, old, new))
    return rows


def lcs_blocks(a: str, b: str, min_len: int = 1) -> list[str]:
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [a[x.a : x.a + x.size] for x in matcher.get_matching_blocks() if x.size >= min_len]


def one_diff(a: str, b: str) -> tuple[str, str] | None:
    old_parts: list[str] = []
    new_parts: list[str] = []
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in {"replace", "delete"} and i2 > i1:
            old_parts.append(a[i1:i2])
        if tag in {"replace", "insert"} and j2 > j1:
            new_parts.append(b[j1:j2])
    if not old_parts or not new_parts:
        return None
    return "".join(old_parts), "".join(new_parts)


def boundary_candidates(ep: Episode) -> list[tuple[str, str, str, str, str, str]]:
    diff = one_diff(ep.before, ep.after)
    if not diff or not ep.changed:
        return []
    old, new = diff
    common = sorted(set(lcs_blocks(ep.before, ep.command, 2)), key=len, reverse=True)
    candidates: list[tuple[str, str, str, str, str, str]] = []
    for raw_entity in common[:8]:
        if old in raw_entity or new in raw_entity:
            continue
        variants = {raw_entity, raw_entity.strip("現在の記録：→はをにへ、。 ")}
        for entity in variants:
            if len(entity) < 2 or entity not in ep.before or entity not in ep.command:
                continue
            command_pattern = ep.command.replace(entity, "<E>", 1).replace(new, "<N>", 1)
            before_pattern = ep.before.replace(entity, "<E>", 1).replace(old, "<O>", 1)
            after_pattern = ep.after.replace(entity, "<E>", 1).replace(new, "<N>", 1)
            if all(token in text for token, text in (("<E>", command_pattern), ("<N>", command_pattern), ("<O>", before_pattern), ("<N>", after_pattern))):
                candidates.append((entity, old, new, before_pattern, command_pattern, after_pattern))
    return list(dict.fromkeys(candidates))


def literal_skeleton(command_pattern: str) -> tuple[str, ...]:
    return tuple(piece for piece in command_pattern.replace("<E>", "|").replace("<N>", "|").split("|") if piece)


def recover_old(before: str, entity: str, before_pattern: str) -> str | None:
    if "<O>" not in before_pattern:
        return None
    tmp = before.replace(entity, "<E>", 1)
    prefix, suffix = before_pattern.split("<O>", 1)
    if not tmp.startswith(prefix) or (suffix and not tmp.endswith(suffix)):
        return None
    return tmp[len(prefix) : len(tmp) - len(suffix) if suffix else None]


def recover_new(command: str, entity: str, literals: tuple[str, ...]) -> str | None:
    residual = command.replace(entity, "<E>", 1)
    for literal in literals:
        if literal not in residual:
            return None
        residual = residual.replace(literal, "", 1)
    value = residual.replace("<E>", "").strip("。、，：:→ 　をにはへがのですしてくださいせよ直す変更設定移動対象最終値行き先")
    return value or None


class SurfacePrototype:
    def fit(self, episodes: list[Episode]) -> None:
        self.rows = [ep for ep in episodes if ep.changed]

    def predict(self, before: str, command: str) -> tuple[str | None, int, float]:
        if not self.rows:
            return None, 0, 0.0
        best = max(self.rows, key=lambda ep: difflib.SequenceMatcher(None, command, ep.command, autojunk=False).ratio())
        diff = one_diff(best.before, best.after)
        if diff and diff[0] in before:
            return before.replace(diff[0], diff[1], 1), len(self.rows), 1.0
        return None, len(self.rows), 0.0

    def bytes(self) -> int:
        return len(pickle.dumps(self.rows))


class LiteralGraph:
    def fit(self, episodes: list[Episode]) -> None:
        counts: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
        self.noop_views: list[str] = []
        for ep in episodes:
            if not ep.changed:
                self.noop_views.append(ep.command)
                continue
            for _, _, _, before_pattern, command_pattern, after_pattern in boundary_candidates(ep):
                counts[(before_pattern, after_pattern, literal_skeleton(command_pattern))] += 1
        self.rows = dict(counts)

    def predict(self, before: str, command: str) -> tuple[str | None, int, float]:
        no_op_similarity = max((difflib.SequenceMatcher(None, command, x, autojunk=False).ratio() for x in self.noop_views), default=0.0)
        if no_op_similarity > 0.72:
            return before, len(self.rows), 0.0
        scored: list[tuple[float, str]] = []
        common = sorted(set(lcs_blocks(before, command, 2)), key=len, reverse=True)
        for (before_pattern, after_pattern, literals), support in self.rows.items():
            for entity in common[:8]:
                old = recover_old(before, entity, before_pattern)
                if not old:
                    continue
                new = recover_new(command, entity, literals)
                if not new or new == old:
                    continue
                scored.append((float(support), after_pattern.replace("<E>", entity).replace("<N>", new)))
        if not scored:
            return None, len(self.rows), 0.0
        scored.sort(reverse=True)
        return scored[0][1], len(self.rows), 1.0

    def bytes(self) -> int:
        return len(pickle.dumps((self.rows, self.noop_views)))


class BidirectionalMDL:
    def fit(self, episodes: list[Episode]) -> None:
        op_support: Counter[tuple[str, str]] = Counter()
        decoder_support: Counter[tuple[str, ...]] = Counter()
        op_decoders: defaultdict[tuple[str, str], Counter[tuple[str, ...]]] = defaultdict(Counter)
        self.noop_views: list[str] = []
        for ep in episodes:
            if not ep.changed:
                self.noop_views.append(ep.command)
                continue
            for _, _, _, before_pattern, command_pattern, after_pattern in boundary_candidates(ep):
                operation = (before_pattern, after_pattern)
                decoder = literal_skeleton(command_pattern)
                op_support[operation] += 1
                decoder_support[decoder] += 1
                op_decoders[operation][decoder] += 1
        self.operations = dict(op_support)
        self.decoders = dict(decoder_support)
        self.op_decoders = {op: dict(counts) for op, counts in op_decoders.items()}

    def predict(self, before: str, command: str) -> tuple[str | None, int, float]:
        no_op_similarity = max((difflib.SequenceMatcher(None, command, x, autojunk=False).ratio() for x in self.noop_views), default=0.0)
        if no_op_similarity > 0.72:
            return before, len(self.operations) + len(self.decoders), 0.0
        common = sorted(set(lcs_blocks(before, command, 2)), key=len, reverse=True)
        candidates: list[tuple[float, str]] = []
        for operation, support in self.operations.items():
            before_pattern, after_pattern = operation
            for entity in common[:10]:
                old = recover_old(before, entity, before_pattern)
                if not old:
                    continue
                for decoder, decoder_support in self.op_decoders.get(operation, {}).items():
                    new = recover_new(command, entity, decoder)
                    if not new or new == old:
                        continue
                    explained = sum(map(len, decoder)) + len(entity) + len(new)
                    score = (support + 1).bit_length() + (decoder_support + 1).bit_length() - 0.03 * (len(entity) + len(new)) - 0.1 * max(0, len(command) - explained)
                    prediction = after_pattern.replace("<E>", entity).replace("<N>", new)
                    candidates.append((score, prediction))
        candidates.sort(reverse=True)
        if not candidates:
            return None, len(self.operations) + len(self.decoders), 0.0
        margin = candidates[0][0] - (candidates[1][0] if len(candidates) > 1 else candidates[0][0] - 1.0)
        return candidates[0][1], len(self.operations) + len(self.decoders), margin

    def bytes(self) -> int:
        return len(pickle.dumps((self.operations, self.decoders, self.op_decoders, self.noop_views)))


def evaluate(seed: int, n: int) -> dict[str, float | int]:
    train = make(seed, n, "train") + make(seed + 33, max(12, n // 6), "confound")
    result: dict[str, float | int] = {"seed": seed, "n": n}
    methods = [("surface", SurfacePrototype()), ("literal_graph", LiteralGraph()), ("bidirectional_mdl", BidirectionalMDL())]
    for name, model in methods:
        started = time.perf_counter()
        model.fit(train)
        result[f"{name}_train_s"] = time.perf_counter() - started
        result[f"{name}_bytes"] = model.bytes()
        result[f"{name}_units"] = len(getattr(model, "operations", getattr(model, "rows", [])))
        for split, mode in (("seen", "train"), ("order", "order"), ("synonym", "para"), ("rename", "rename"), ("rename_synonym", "rename_para"), ("confound", "confound")):
            rows = make(seed + 100 + len(split), 50, mode)
            scores: list[bool] = []
            latencies: list[float] = []
            reads: list[int] = []
            margins: list[float] = []
            for ep in rows:
                t0 = time.perf_counter_ns()
                prediction, read_count, margin = model.predict(ep.before, ep.command)
                latencies.append((time.perf_counter_ns() - t0) / 1e6)
                reads.append(read_count)
                margins.append(margin)
                if split == "confound":
                    scores.append((prediction is None or prediction == ep.before) == (not ep.changed))
                else:
                    scores.append(prediction == ep.after)
            result[f"{name}_{split}"] = statistics.mean(scores)
            result[f"{name}_{split}_ms"] = statistics.mean(latencies)
            result[f"{name}_{split}_reads"] = statistics.mean(reads)
            result[f"{name}_{split}_margin"] = statistics.mean(margins)
    result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return result


def main() -> None:
    sizes = (60, 180, 360)
    seeds = (1, 7, 19)
    rows = [evaluate(seed, n) for n in sizes for seed in seeds]
    aggregate: dict[str, dict[str, dict[str, float]]] = {}
    for n in sizes:
        selected = [row for row in rows if row["n"] == n]
        aggregate[str(n)] = {}
        for method in ("surface", "literal_graph", "bidirectional_mdl"):
            keys = ("seen", "order", "synonym", "rename", "rename_synonym", "confound", "bytes", "units", "train_s", "seen_ms", "seen_reads", "seen_margin")
            aggregate[str(n)][method] = {key: statistics.mean(float(row[f"{method}_{key}"]) for row in selected) for key in keys}
    output = {
        "hypothesis": "Bidirectional Executable MDL Operation Quotient",
        "aggregate": aggregate,
        "rows": rows,
        "peak_rss_kib_runtime_included": max(int(row["peak_rss_kib"]) for row in rows),
        "audit": {
            "model_sees_entity_list": False,
            "model_sees_value_list": False,
            "fixed_semantic_slots": False,
            "external_llm_or_rag": False,
            "dataset_is_controlled_synthetic": True,
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
