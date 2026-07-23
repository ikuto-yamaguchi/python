"""Track C Cycle 023: temporal-reversal causal event anchors.

Learner input:
- raw Japanese before/command/after/future strings
- temporal order only

Hidden object/field/value labels are evaluator-only.
No Transformer, attention, external LLM, RAG, morphological analyzer,
fixed ontology, handwritten slots, or problem-specific branching.
"""
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

OBJECTS = ["青い箱", "赤い箱", "小型端末", "大型端末", "北側の鍵", "南側の鍵", "試料甲", "試料乙"]
ALIASES = {
    "青い箱": "青色ケース", "赤い箱": "赤色ケース",
    "小型端末": "小さい端末", "大型端末": "大きい端末",
    "北側の鍵": "北のキー", "南側の鍵": "南のキー",
    "試料甲": "サンプル甲", "試料乙": "サンプル乙",
}
FIELDS = ["場所", "状態", "担当"]
VALUES = {
    "場所": ["棚A", "棚B", "棚C", "棚D"],
    "状態": ["待機", "処理中", "完了", "保留"],
    "担当": ["担当一", "担当二", "担当三", "担当四"],
}
STATE_FORMS = [
    "{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。",
    "{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。",
]
CMD = {
    "場所": ["{o}を{v}へ移してください。", "{o}の保管先を{v}へ変更します。"],
    "状態": ["{o}を{v}にしてください。", "{o}の進行状態を{v}へ切り替えます。"],
    "担当": ["{o}を{v}の担当にしてください。", "{o}の受け持ちを{v}へ変更します。"],
}
HELD = {
    "場所": ["対象{o}、次から{v}で保管。"],
    "状態": ["対象{o}は以後{v}扱い。"],
    "担当": ["{o}は{v}へ引き継ぎ。"],
}
OMIT = {
    "場所": ["それを{v}へ移してください。"],
    "状態": ["その対象を{v}にしてください。"],
    "担当": ["担当は{v}へ変えてください。"],
}
DIST = ["別件の資料を確認しました。", "前の案はいったん保留です。", "この文は更新と無関係です。"]

@dataclass
class Ex:
    before: str
    command: str
    after: str
    future: str
    obj: str
    field: str
    value: str
    mode: str
    focus: str

@dataclass
class Event:
    cl: str
    cr: str
    sl: str
    sr: str
    old_shape: str
    new_shape: str
    forward_success: int = 0
    forward_wrong: int = 0
    reverse_success: int = 0
    reverse_wrong: int = 0
    null: int = 0
    direction_score: float = 0.0
    support: int = 1

def grams(s: str) -> Counter:
    s = "".join(s.split())
    return Counter(s[i:i+n] for n in (1, 2, 3) for i in range(max(0, len(s)-n+1)))

def cosine(a: Counter, b: Counter) -> float:
    d = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return d / (na * nb + 1e-12)

def shape(s: str) -> str:
    return "".join(
        "A" if c.isascii() and c.isalnum()
        else "J" if c not in "。、／=：:\n "
        else c for c in s
    )

def diff(a: str, b: str):
    l = 0
    while l < min(len(a), len(b)) and a[l] == b[l]:
        l += 1
    r = 0
    while r < min(len(a)-l, len(b)-l) and a[-1-r] == b[-1-r]:
        r += 1
    return l, r, a[l:len(a)-r if r else len(a)], b[l:len(b)-r if r else len(b)]

def state(o, d, form):
    return STATE_FORMS[form].format(o=o, loc=d["場所"], status=d["状態"], owner=d["担当"])

def make_stream(seed, n, mode):
    rng = random.Random(seed)
    world = {}
    out = []
    focus = ""
    for _ in range(n):
        canonical = rng.choice(OBJECTS)
        o = ALIASES[canonical] if mode == "rename" else canonical
        world.setdefault(canonical, {f: rng.choice(VALUES[f]) for f in FIELDS})
        field = rng.choice(FIELDS)
        value = rng.choice([v for v in VALUES[field] if v != world[canonical][field]])
        form = 1 if mode == "alternate" else 0
        before = state(o, world[canonical], form)
        forms = OMIT[field] if mode == "omitted" else (
            HELD[field] if mode in ("held", "paragraph", "plan", "counterfactual") else CMD[field]
        )
        command = rng.choice(forms).format(o=o, v=value)
        if mode == "paragraph":
            command = " ".join(rng.choice(DIST) for _ in range(3)) + "\n" + command
        if mode == "plan":
            old = rng.choice([x for x in VALUES[field] if x not in (world[canonical][field], value)])
            command = f"{o}を{old}にする案でした。{rng.choice(DIST)} 最終的には" + command
        world[canonical][field] = value
        after = state(o, world[canonical], form)
        future = f"次の観測でも{o}の更新結果は{value}で、補助記録は維持されます。"
        if mode == "counterfactual":
            future = f"もし更新しなければ{o}は以前の値のままです。実行時は{value}です。"
        out.append(Ex(before, command, after, future, o, field, value, mode, focus))
        focus = o
    return out

class Model:
    def __init__(self, kind):
        self.kind = kind
        self.events = []
        self.edges = []
        self.train_seconds = 0.0

    def fit(self, examples):
        start = time.perf_counter()
        dedup = {}
        for ex in examples:
            l, r, old, new = diff(ex.before, ex.after)
            if not old or not new:
                continue
            p = ex.command.find(new)
            if p < 0:
                continue
            ev = Event(
                ex.command[max(0, p-8):p],
                ex.command[p+len(new):p+len(new)+8],
                ex.before[max(0, l-8):l],
                ex.before[len(ex.before)-r:len(ex.before)-r+8] if r else ex.before[l+len(old):l+len(old)+8],
                shape(old),
                shape(new),
            )
            key = (ev.cl, ev.cr, ev.sl, ev.sr, ev.old_shape, ev.new_shape)
            if key in dedup:
                dedup[key].support += 1
            else:
                dedup[key] = ev
        self.events = sorted(dedup.values(), key=lambda e: e.support, reverse=True)[:64]

        for ev in self.events:
            for ex in examples:
                fwd, okf = self._apply(ex.before, ex.command, ev, reverse=False)
                rev, okr = self._apply(ex.after, ex.command, ev, reverse=True)
                if not okf:
                    ev.null += 1
                elif fwd == ex.after:
                    ev.forward_success += 1
                else:
                    ev.forward_wrong += 1
                if okr and rev == ex.before:
                    ev.reverse_success += 1
                elif okr:
                    ev.reverse_wrong += 1
            fs = ev.forward_success
            fw = ev.forward_wrong
            rs = ev.reverse_success
            rw = ev.reverse_wrong
            ev.direction_score = (fs + 1) / (fs + fw + 2) - (rs + 1) / (rs + rw + 2)

        if self.kind == "graph":
            for i, a in enumerate(self.events):
                if a.forward_success < 2 or a.direction_score <= 0:
                    continue
                for j, b in enumerate(self.events):
                    if i == j or b.forward_success < 2:
                        continue
                    compatible = a.new_shape == b.old_shape or a.sr == b.sl
                    if compatible:
                        self.edges.append((i, j, a.direction_score + b.direction_score))
            self.edges = sorted(self.edges, key=lambda x: x[2], reverse=True)[:96]
        self.train_seconds = time.perf_counter() - start

    def _extract(self, command, ev):
        i = command.find(ev.cl) if ev.cl else 0
        if i < 0:
            return None
        st = i + len(ev.cl)
        en = command.find(ev.cr, st) if ev.cr else len(command)
        if en < st:
            return None
        value = command[st:en]
        return value if 0 < len(value) <= 14 else None

    def _apply(self, state_text, command, ev, reverse=False):
        value = self._extract(command, ev)
        if value is None:
            return state_text, False
        i = state_text.find(ev.sl) if ev.sl else 0
        if i < 0:
            return state_text, False
        st = i + len(ev.sl)
        en = state_text.find(ev.sr, st) if ev.sr else len(state_text)
        if en < st:
            return state_text, False
        if reverse:
            current = state_text[st:en]
            if shape(current) != ev.new_shape:
                return state_text, False
            return state_text, False
        return state_text[:st] + value + state_text[en:], True

    def predict(self, ex):
        candidates = []
        cg = grams(ex.command)
        sg = grams(ex.before)
        for i, ev in enumerate(self.events):
            pred, ok = self._apply(ex.before, ex.command, ev, reverse=False)
            if not ok:
                continue
            score = (
                0.45 * cosine(cg, grams(ev.cl + "|" + ev.cr))
                + 0.35 * cosine(sg, grams(ev.sl + "|" + ev.sr))
                + 0.20 * min(1.0, ev.support / 4)
            )
            if self.kind in ("asymmetry", "graph"):
                score += 0.30 * ev.direction_score
                score += 0.15 * ((ev.forward_success + 1) / (ev.forward_success + ev.forward_wrong + 2))
            if self.kind == "graph":
                outgoing = sum(1 for a, _, _ in self.edges if a == i)
                incoming = sum(1 for _, b, _ in self.edges if b == i)
                score += 0.03 * min(4, outgoing) - 0.015 * min(4, incoming)
            candidates.append((score, pred, i))
        if not candidates:
            return ex.before, 0, 1
        candidates.sort(reverse=True, key=lambda x: x[0])
        if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < 0.02:
            return ex.before, len(candidates), 1
        return candidates[0][1], len(candidates), 0

def evaluate(seed, n, mode):
    train = []
    for k, m in enumerate(("seen", "held", "rename", "alternate")):
        train += make_stream(seed + 31*k, n//4, m)
    test = make_stream(seed + 999, max(12, n//6), mode)
    result = {}
    for kind in ("surface", "asymmetry", "graph"):
        model = Model(kind)
        model.fit(train)
        start = time.perf_counter()
        correct = wrong = null = candidates = 0
        for ex in test:
            pred, c, z = model.predict(ex)
            candidates += c
            correct += int(pred == ex.after)
            wrong += int(pred != ex.after and not z)
            null += int(z)
        directional = [e for e in model.events if e.direction_score > 0]
        result[kind] = {
            "accuracy": correct / len(test),
            "wrong_commit": wrong / len(test),
            "null_rate": null / len(test),
            "mean_candidates": candidates / len(test),
            "events": len(model.events),
            "directed_events": len(directional),
            "causal_edges": len(model.edges),
            "mean_direction_score": statistics.mean([e.direction_score for e in directional]) if directional else 0.0,
            "forward_success": sum(e.forward_success for e in model.events),
            "forward_wrong": sum(e.forward_wrong for e in model.events),
            "reverse_success": sum(e.reverse_success for e in model.events),
            "model_bytes": len(pickle.dumps(model)),
            "training_seconds": model.train_seconds,
            "inference_ms": (time.perf_counter() - start) * 1000 / len(test),
        }
    return result

def sequential(seed, n):
    seq = make_stream(seed + 700, n, "seen")
    out = {}
    for kind in ("surface", "asymmetry", "graph"):
        model = Model(kind)
        model.fit(seq[:n//2])
        coverage = correct = 0
        for a, b in zip(seq[n//2:-1], seq[n//2+1:]):
            p1, c1, z1 = model.predict(a)
            b2 = Ex(p1, b.command, b.after, b.future, b.obj, b.field, b.value, b.mode, b.focus)
            p2, c2, z2 = model.predict(b2)
            if c1 and c2 and not z1 and not z2:
                coverage += 1
                correct += int(p2 == b.after)
        out[kind] = {
            "coverage": coverage / max(1, len(seq[n//2:-1])),
            "accuracy_conditional": correct / max(1, coverage),
        }
    return out

def summarize(raw):
    out = {}
    for n, runs in raw.items():
        out[n] = {}
        for mode in ("seen", "held", "rename", "alternate", "omitted", "paragraph", "plan", "counterfactual"):
            out[n][mode] = {}
            for kind in ("surface", "asymmetry", "graph"):
                out[n][mode][kind] = {
                    k: statistics.mean(r[mode][kind][k] for r in runs)
                    for k in runs[0][mode][kind]
                }
        out[n]["sequential"] = {
            kind: {
                k: statistics.mean(r["sequential"][kind][k] for r in runs)
                for k in runs[0]["sequential"][kind]
            }
            for kind in ("surface", "asymmetry", "graph")
        }
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results_cycle_023.json")
    args = parser.parse_args()
    raw = {}
    for n in (48, 144, 288):
        runs = []
        for seed in (1, 7, 19):
            r = {
                mode: evaluate(seed, n, mode)
                for mode in ("seen", "held", "rename", "alternate", "omitted", "paragraph", "plan", "counterfactual")
            }
            r["sequential"] = sequential(seed, max(24, n//3))
            runs.append(r)
        raw[str(n)] = runs
    payload = {
        "hypothesis": "Temporal-Reversal Event Anchors with Directed Transition Graphs",
        "seeds": [1, 7, 19],
        "sizes": [48, 144, 288],
        "raw": raw,
        "summary": summarize(raw),
        "peak_rss_kib_runtime_included": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_complexity": "event extraction O(NL), audit O(PN), graph O(P^2), inference O(PL), P<=64",
        "hidden_labels_used_by_learner": False,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload["summary"]["288"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
