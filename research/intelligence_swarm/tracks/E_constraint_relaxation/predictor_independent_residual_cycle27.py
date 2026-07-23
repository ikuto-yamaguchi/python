from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse
import json
import math
import pickle
import random
import resource
import statistics
import time

OBJECTS = ["青い箱", "赤い箱", "小型端末", "大型端末", "試料甲", "試料乙"]
ALIASES = {
    "青い箱": "青色ケース", "赤い箱": "赤色ケース", "小型端末": "小さい端末",
    "大型端末": "大きい端末", "試料甲": "サンプル甲", "試料乙": "サンプル乙",
}
VALUES = ["棚A", "棚B", "棚C", "棚D", "待機", "処理中", "完了", "保留"]
DISTRACTORS = ["別件の説明です。", "前案は保留です。", "補助記録は変更しません。"]

@dataclass
class Example:
    before: str
    command: str
    after: str
    future: str
    obj: str
    value: str
    mode: str


def build(seed: int, n: int, mode: str) -> list[Example]:
    rng = random.Random(seed)
    rows: list[Example] = []
    for _ in range(n):
        obj = rng.choice(OBJECTS)
        surf = ALIASES[obj] if mode == "unknown" else obj
        old, new = rng.sample(VALUES, 2)
        before = f"{surf}の現在値は{old}です。補助記録は維持します。"
        command = f"{surf}の値を{new}へ変更してください。"
        if mode == "ambiguous":
            other = rng.choice([x for x in OBJECTS if x != obj])
            command = f"{surf}か{other}の値を{new}へ変更してください。"
        elif mode == "nested":
            command = f"依頼内容は「{command}」です。"
        elif mode == "omitted":
            command = f"それを{new}へ変更してください。"
        elif mode == "paragraph":
            command = " ".join(rng.choice(DISTRACTORS) for _ in range(4)) + "\n" + command
        elif mode == "plan":
            rejected = rng.choice([x for x in VALUES if x not in (old, new)])
            command = f"{surf}を{rejected}にする案は撤回します。最終的には{command}"
        elif mode == "counterfactual":
            command = f"もし変更しなければ{surf}は{old}のままです。実際には{command}"
        after = f"{surf}の現在値は{new}です。補助記録は維持します。"
        future = f"次の観測でも{surf}は{new}です。補助記録は維持されます。"
        rows.append(Example(before, command, after, future, surf, new, mode))
    return rows


def spans(text: str, lo: int, hi: int) -> list[str]:
    return sorted(
        {text[i:j] for i in range(len(text)) for j in range(i + lo, min(len(text), i + hi) + 1)},
        key=lambda x: (-len(x), x),
    )


def char_shape(text: str) -> str:
    return "".join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、：／=\n " else c for c in text)


class CharPredictor:
    """Small character conditional predictor, independent of candidate spans."""
    def __init__(self, order: int = 3):
        self.order = order
        self.counts: dict[str, Counter[str]] = defaultdict(Counter)
        self.unigram: Counter[str] = Counter()

    def fit(self, pairs: list[tuple[str, str]]) -> None:
        for context, target in pairs:
            history = context[-self.order:]
            for ch in target:
                self.counts[history][ch] += 1
                self.unigram[ch] += 1
                history = (history + ch)[-self.order:]

    def nll_profile(self, context: str, target: str) -> list[float]:
        history = context[-self.order:]
        profile: list[float] = []
        alphabet = max(2, len(self.unigram))
        for ch in target:
            row = self.counts.get(history)
            if row:
                total = sum(row.values()) + alphabet
                prob = (row.get(ch, 0) + 1) / total
            else:
                total = sum(self.unigram.values()) + alphabet
                prob = (self.unigram.get(ch, 0) + 1) / max(1, total)
            profile.append(-math.log(prob))
            history = (history + ch)[-self.order:]
        return profile


@dataclass(frozen=True)
class ResidualSignature:
    channel: str
    bucket: int
    width: int
    shape: str


@dataclass
class Prototype:
    obj_shape: str
    value_shape: str
    residual: ResidualSignature
    credit: float
    support: int


def candidate_spans(ex: Example) -> tuple[list[str], list[str]]:
    object_candidates = [x for x in spans(ex.command, 2, 10) if x in ex.before][:6]
    value_candidates = [x for x in spans(ex.command, 1, 8) if x in ex.after or x in ex.future][:6]
    return object_candidates, value_candidates


def residual_nodes(ex: Example, after_pred: CharPredictor, future_pred: CharPredictor) -> list[ResidualSignature]:
    pa = after_pred.nll_profile(ex.before, ex.after)
    pf = future_pred.nll_profile(ex.command, ex.future)
    nodes: list[ResidualSignature] = []
    for channel, profile, text in (("after_without_command", pa, ex.after), ("future_without_after", pf, ex.future)):
        if not profile:
            continue
        threshold = statistics.mean(profile) + 0.35 * (statistics.pstdev(profile) if len(profile) > 1 else 0.0)
        hot = [i for i, v in enumerate(profile) if v >= threshold]
        groups: list[list[int]] = []
        for idx in hot:
            if not groups or idx > groups[-1][-1] + 1:
                groups.append([idx])
            else:
                groups[-1].append(idx)
        for g in groups[:6]:
            start, end = g[0], g[-1] + 1
            segment = text[start:end]
            bucket = min(7, int(8 * start / max(1, len(text))))
            nodes.append(ResidualSignature(channel, bucket, min(8, len(segment)), char_shape(segment)[:8]))
    return nodes[:10]


def base_energy(ex: Example, obj: str, value: str) -> float:
    after_cost = 0.0 if obj in ex.after and value in ex.after else 1.0
    future_cost = 0.0 if obj in ex.future and value in ex.future else 1.0
    execution_cost = 0.0 if obj in ex.command and value in ex.command else 1.0
    damage = 0.0 if "補助記録は維持" in ex.after else 1.0
    length_penalty = 0.08 / max(1, len(obj)) + 0.08 / max(1, len(value))
    return after_cost + future_cost + execution_cost + damage + length_penalty


def train_prototypes(examples: list[Example], after_pred: CharPredictor, future_pred: CharPredictor) -> list[Prototype]:
    support: dict[tuple[str, str, ResidualSignature], list[float]] = defaultdict(list)
    for ex in examples:
        objs, vals = candidate_spans(ex)
        residuals = residual_nodes(ex, after_pred, future_pred)
        for obj in objs:
            for value in vals:
                e_pair = base_energy(ex, obj, value)
                e_obj_ablated = base_energy(ex, "", value)
                e_value_ablated = base_energy(ex, obj, "")
                structural_gain = (e_obj_ablated + e_value_ablated) - 2 * e_pair
                for res in residuals:
                    response = (1.0 + 0.1 * res.width) * (1.0 if res.bucket in (1, 2, 3, 4, 5, 6) else 0.7)
                    credit = structural_gain * response
                    if credit > 0.12:
                        support[(char_shape(obj), char_shape(value), res)].append(credit)
    out: list[Prototype] = []
    for (os, vs, res), credits in support.items():
        if len(credits) >= 4 and statistics.mean(credits) > 0.18:
            out.append(Prototype(os, vs, res, min(0.9, statistics.mean(credits)), len(credits)))
    return sorted(out, key=lambda p: (p.support, p.credit), reverse=True)[:128]


def prototype_credit(obj: str, value: str, residuals: list[ResidualSignature], prototypes: list[Prototype]) -> float:
    os, vs = char_shape(obj), char_shape(value)
    best = 0.0
    rset = set(residuals)
    for p in prototypes:
        if p.obj_shape == os and p.value_shape == vs and p.residual in rset:
            best = max(best, p.credit)
    return best


def relax(ex: Example, residuals: list[ResidualSignature], prototypes: list[Prototype], mode: str):
    objs, vals = candidate_spans(ex)
    active = [(o, v) for o in objs for v in vals][:36]
    if not active:
        return None, 0, 0, True, "candidate_collapse"
    previous = None
    sweeps = 0
    reason = "fixed_point"
    while sweeps < 6:
        sweeps += 1
        scored = []
        for o, v in active:
            credit = prototype_credit(o, v, residuals, prototypes) if mode != "base" else 0.0
            scored.append((base_energy(ex, o, v) - credit, (o, v)))
        scored.sort(key=lambda x: x[0])
        best = scored[0][0]
        active = [state for score, state in scored if score <= best + 0.06][:12]
        signature = tuple(active)
        if signature == previous:
            break
        previous = signature
    else:
        reason = "iteration_cap"
    final = sorted(
        (base_energy(ex, o, v) - (prototype_credit(o, v, residuals, prototypes) if mode != "base" else 0.0), (o, v))
        for o, v in active
    )
    if mode == "residual_null":
        if len(final) < 2 or final[1][0] - final[0][0] < 0.14:
            return None, sweeps, len(active), True, "null_safety"
    return final[0][1], sweeps, len(active), False, reason


def evaluate(test: list[Example], after_pred: CharPredictor, future_pred: CharPredictor, prototypes: list[Prototype], mode: str):
    correct = wrong = null = pair_recall = 0
    sweeps: list[int] = []
    actives: list[int] = []
    reasons = Counter()
    start = time.perf_counter()
    for ex in test:
        residuals = residual_nodes(ex, after_pred, future_pred)
        state, sw, ac, abstain, reason = relax(ex, residuals, prototypes, mode)
        sweeps.append(sw)
        actives.append(ac)
        reasons[reason] += 1
        objs, vals = candidate_spans(ex)
        pair_recall += int(ex.obj in objs and ex.value in vals)
        if abstain or state is None:
            null += 1
            continue
        ok = state == (ex.obj, ex.value)
        correct += int(ok)
        wrong += int(not ok)
    n = len(test)
    return {
        "accuracy": correct / n,
        "wrong_commit": wrong / n,
        "null_rate": null / n,
        "pair_recall": pair_recall / n,
        "mean_sweeps": statistics.mean(sweeps),
        "max_sweeps": max(sweeps),
        "mean_active": statistics.mean(actives),
        "convergence_rate": sum(1 for r in reasons if r != "iteration_cap") / max(1, len(reasons)),
        "inference_ms": (time.perf_counter() - start) * 1000 / n,
        "failure_reasons": dict(reasons),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="results_cycle_027.json")
    args = ap.parse_args()
    modes = ["seen", "unknown", "ambiguous", "nested", "omitted", "paragraph", "plan", "counterfactual"]
    raw = {}
    for seed in (1, 7, 19):
        train = build(seed, 48, "seen") + build(seed + 11, 48, "unknown")
        after_pred = CharPredictor(order=3)
        future_pred = CharPredictor(order=2)
        after_pred.fit([(x.before, x.after) for x in train])
        future_pred.fit([(x.command, x.future) for x in train])
        start = time.perf_counter()
        prototypes = train_prototypes(train, after_pred, future_pred)
        training_seconds = time.perf_counter() - start
        run = {
            "training_seconds": training_seconds,
            "model_bytes": len(pickle.dumps((after_pred, future_pred, prototypes))),
            "prototype_count": len(prototypes),
        }
        for mode in modes:
            test = build(seed + 999, 36, mode)
            run[mode] = {
                "base": evaluate(test, after_pred, future_pred, prototypes, "base"),
                "residual": evaluate(test, after_pred, future_pred, prototypes, "residual"),
                "residual_null": evaluate(test, after_pred, future_pred, prototypes, "residual_null"),
            }
        raw[str(seed)] = run
    summary = {}
    for mode in modes:
        summary[mode] = {}
        for method in ("base", "residual", "residual_null"):
            numeric_keys = [k for k, v in raw["1"][mode][method].items() if isinstance(v, (int, float))]
            summary[mode][method] = {
                k: statistics.mean(raw[str(seed)][mode][method][k] for seed in (1, 7, 19)) for k in numeric_keys
            }
    summary["model_bytes"] = statistics.mean(raw[str(seed)]["model_bytes"] for seed in (1, 7, 19))
    summary["prototype_count"] = statistics.mean(raw[str(seed)]["prototype_count"] for seed in (1, 7, 19))
    summary["training_seconds"] = statistics.mean(raw[str(seed)]["training_seconds"] for seed in (1, 7, 19))
    payload = {
        "hypothesis": "Predictor-Independent Residual Nodes from Cross-View Leave-One-Channel-Out Error",
        "seeds": [1, 7, 19],
        "raw": raw,
        "summary": summary,
        "peak_rss_kib_runtime_included": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_complexity": "predictor fit O(NL), residual O(L), prototype audit O(NOVR), relaxation O(SH), O,V<=6,R<=10,H<=36,S<=6",
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
