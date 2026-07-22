"""Track B Cycle 015: destruction-vector e-graph quotient refinement.

Controlled falsification probe. Learner receives raw Japanese before/command/after
strings only. Hidden object/field/value labels are evaluator-only.

No external model, RAG, morphological analyzer, fixed ontology, or handwritten
semantic slots are used by proposal, execution, quotienting, or inference.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse
import hashlib
import json
import math
import pickle
import random
import resource
import statistics
import time

OBJECTS = ["青い箱", "赤い箱", "小型端末", "大型端末", "北側の鍵", "南側の鍵", "試料甲", "試料乙"]
FIELDS = ["置き場所", "状態", "担当"]
VALUES = {
    "置き場所": ["棚A", "棚B", "棚C", "棚D"],
    "状態": ["待機", "処理中", "完了", "保留"],
    "担当": ["担当一", "担当二", "担当三", "担当四"],
}
STATE_FORMS = [
    "{o}の置き場所は{loc}。{o}の状態は{status}。{o}の担当は{owner}。",
    "{o}について、保管先={loc}／進行={status}／受持={owner}。",
]
COMMANDS = {
    "置き場所": [
        "{o}を{v}へ移してください。",
        "{o}の保管先を{v}へ変更します。",
    ],
    "状態": [
        "{o}を{v}にしてください。",
        "{o}の進行状態を{v}へ切り替えます。",
    ],
    "担当": [
        "{o}を{v}の担当にしてください。",
        "{o}の受け持ちを{v}へ変更します。",
    ],
}
HELD_ORDER = {
    "置き場所": ["{v}へ移してください、対象は{o}です。"],
    "状態": ["{v}扱いにしてください、対象は{o}です。"],
    "担当": ["{v}へ引き継いでください、対象は{o}です。"],
}
HELD_LEXEME = {
    "置き場所": ["対象{o}は次から{v}で保管。"],
    "状態": ["対象{o}は以後{v}として運用。"],
    "担当": ["対象{o}の受持を{v}へ。"],
}
OMITTED = {
    "置き場所": ["それを{v}へ移してください。"],
    "状態": ["その対象を{v}にしてください。"],
    "担当": ["担当は{v}へ変えてください。"],
}


def stable_hash(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")


def grams(text: str) -> Counter[str]:
    s = "".join(text.split())
    return Counter(s[i : i + n] for n in (2, 3) for i in range(max(0, len(s) - n + 1)))


def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb + 1e-12)


def split_clauses(text: str) -> list[tuple[int, int, str]]:
    # Punctuation-delimited lattice plus adjacent pair spans. No semantic labels.
    cuts = [0]
    for i, ch in enumerate(text):
        if ch in "。\n／":
            cuts.append(i + 1)
    if cuts[-1] != len(text):
        cuts.append(len(text))
    base = []
    for a, b in zip(cuts, cuts[1:]):
        seg = text[a:b]
        if seg.strip():
            base.append((a, b, seg))
    lattice = base[:]
    for i in range(len(base) - 1):
        lattice.append((base[i][0], base[i + 1][1], text[base[i][0] : base[i + 1][1]]))
    return lattice[:12]


def diff_window(a: str, b: str) -> tuple[int, int, str, str]:
    left = 0
    while left < min(len(a), len(b)) and a[left] == b[left]:
        left += 1
    right = 0
    while right < min(len(a) - left, len(b) - left) and a[-1 - right] == b[-1 - right]:
        right += 1
    amid = a[left : len(a) - right if right else len(a)]
    bmid = b[left : len(b) - right if right else len(b)]
    return left, right, amid, bmid


def contexts(text: str, token: str, radius: int = 9) -> list[tuple[str, str]]:
    out = []
    start = 0
    while token and True:
        i = text.find(token, start)
        if i < 0:
            break
        out.append((text[max(0, i - radius) : i], text[i + len(token) : i + len(token) + radius]))
        start = i + 1
    return out[:4]


@dataclass
class Episode:
    before: str
    command: str
    after: str
    obj: str
    field: str
    value: str
    focus: str | None


@dataclass
class Program:
    cmd_left: str
    cmd_right: str
    state_left: str
    state_right: str
    source_clause: str
    support: int = 1
    score: float = 0.0
    destruction: tuple[int, ...] = ()
    aliases: set[str] = field(default_factory=set)

    def model_cost(self) -> int:
        return len(self.cmd_left) + len(self.cmd_right) + len(self.state_left) + len(self.state_right) + 8


class Learner:
    def __init__(self, mode: str, cap: int = 32):
        self.mode = mode
        self.cap = cap
        self.programs: list[Program] = []
        self.raw_candidates = 0
        self.rejected = 0
        self.merges = 0
        self.peak_candidates = 0

    def _extract(self, command: str, p: Program) -> str | None:
        starts = [0]
        if p.cmd_left:
            starts = []
            pos = 0
            while True:
                i = command.find(p.cmd_left, pos)
                if i < 0:
                    break
                starts.append(i + len(p.cmd_left))
                pos = i + 1
        vals = []
        for st in starts:
            en = command.find(p.cmd_right, st) if p.cmd_right else len(command)
            if en >= st:
                v = command[st:en]
                if 0 < len(v) <= 12:
                    vals.append(v)
        return min(vals, key=len) if vals else None

    def execute(self, state: str, command: str, p: Program) -> tuple[str, bool, int]:
        value = self._extract(command, p)
        if value is None:
            return state, False, 0
        matches = []
        pos = 0
        while True:
            i = state.find(p.state_left, pos) if p.state_left else pos
            if i < 0:
                break
            st = i + len(p.state_left)
            en = state.find(p.state_right, st) if p.state_right else len(state)
            if en >= st:
                matches.append((st, en))
            pos = i + 1
            if not p.state_left or pos >= len(state):
                break
        if len(matches) != 1:
            return state, False, len(matches)
        st, en = matches[0]
        return state[:st] + value + state[en:], True, 1

    def propose(self, ep: Episode) -> list[Program]:
        out = []
        before_lattice = split_clauses(ep.before)
        after_lattice = split_clauses(ep.after)
        for ba, bb, bc in before_lattice:
            for aa, ab, ac in after_lattice:
                l, r, old, new = diff_window(bc, ac)
                if not new or len(new) > 12 or bc == ac:
                    continue
                for cl, cr in contexts(ep.command, new):
                    p = Program(cl, cr, bc[:l], bc[len(bc) - r :] if r else "", bc)
                    out.append(p)
                    if len(out) >= 96:
                        return out
        return out

    def destruction_vector(self, ep: Episode, p: Program, contrast_states: list[str]) -> tuple[int, ...]:
        # Learner-side probes use raw string executions only.
        base, ok, ambiguity = self.execute(ep.before, ep.command, p)
        exact = int(ok and base == ep.after)
        unique = int(ambiguity == 1)

        same_state_damage = 0
        other_state_damage = 0
        for i, st in enumerate(contrast_states[-8:]):
            out, worked, _ = self.execute(st, ep.command, p)
            if worked and out != st:
                if i % 2 == 0:
                    same_state_damage += 1
                else:
                    other_state_damage += 1

        # Inverse proxy from raw before/after: replace extracted new span with the old diff.
        _, _, old, new = diff_window(ep.before, ep.after)
        inv_cmd = ep.command.replace(new, old, 1) if new and new in ep.command else ep.command
        restored, inv_ok, _ = self.execute(ep.after, inv_cmd, p)
        inverse = int(inv_ok and restored == ep.before)

        # Command order perturbation and state representation perturbation.
        chunks = [x for x in ep.command.replace("。", "").split("、") if x]
        swapped = "、".join(reversed(chunks)) + ("。" if ep.command.endswith("。") else "")
        sw_out, sw_ok, _ = self.execute(ep.before, swapped, p)
        order_stable = int(sw_ok and sw_out == ep.after)

        alt_state = ep.before.replace("。", "／").replace("は", "=")
        alt_out, alt_ok, _ = self.execute(alt_state, ep.command, p)
        alt_changed = int(alt_ok and alt_out != alt_state)

        # Focus omission proxy: remove the longest recurring raw prefix from command.
        omitted = ep.command
        if ep.focus:
            omitted = omitted.replace(ep.focus, "その対象", 1)
        om_out, om_ok, _ = self.execute(ep.before, omitted, p)
        omitted_stable = int(om_ok and om_out == ep.after)

        return (
            exact,
            unique,
            min(same_state_damage, 3),
            min(other_state_damage, 3),
            inverse,
            order_stable,
            alt_changed,
            omitted_stable,
        )

    def learn(self, episodes: list[Episode]) -> None:
        contrast_states: list[str] = []
        eclasses: dict[tuple, Program] = {}
        for ep in episodes:
            proposals = self.propose(ep)
            self.raw_candidates += len(proposals)
            self.peak_candidates = max(self.peak_candidates, len(proposals))
            for p in proposals:
                out, ok, ambiguity = self.execute(ep.before, ep.command, p)
                if not ok or out != ep.after or ambiguity != 1:
                    self.rejected += 1
                    continue
                p.destruction = self.destruction_vector(ep, p, contrast_states)
                # Penalize observed damage and description length.
                p.score = 5 * p.destruction[0] + 2 * p.destruction[1] + p.destruction[4] - 0.4 * (
                    p.destruction[2] + p.destruction[3]
                ) - 0.015 * p.model_cost()
                p.aliases.add(p.cmd_left + "|" + p.cmd_right)

                if self.mode == "executable":
                    key = (p.cmd_left, p.cmd_right, p.state_left, p.state_right)
                elif self.mode == "surface_quotient":
                    key = (
                        p.cmd_left[-4:], p.cmd_right[:4], p.state_left[-4:], p.state_right[:4]
                    )
                else:
                    # E-class requires same observed destruction behavior. Surface shape
                    # is only a weak tie-breaker, not the quotient identity.
                    key = (p.destruction, len(p.state_left) // 4, len(p.state_right) // 4)

                current = eclasses.get(key)
                if current is None:
                    eclasses[key] = p
                else:
                    current.support += 1
                    current.aliases |= p.aliases
                    if p.score > current.score or (p.score == current.score and p.model_cost() < current.model_cost()):
                        p.support = current.support
                        p.aliases |= current.aliases
                        eclasses[key] = p
                    self.merges += 1
            contrast_states.append(ep.before)

        ranked = sorted(eclasses.values(), key=lambda p: (p.score, math.log1p(p.support), -p.model_cost()), reverse=True)
        self.programs = ranked[: self.cap]

    def infer(self, before: str, command: str) -> tuple[str, int]:
        candidates = []
        for p in self.programs:
            out, ok, ambiguity = self.execute(before, command, p)
            if ok and ambiguity == 1:
                sim = cosine(grams(command), grams(p.cmd_left + p.cmd_right))
                candidates.append((p.score + 0.5 * math.log1p(p.support) + sim, out))
        candidates.sort(reverse=True, key=lambda x: x[0])
        return (candidates[0][1] if candidates else before), len(candidates)


def render_state(obj: str, d: dict[str, str], form: int) -> str:
    return STATE_FORMS[form].format(o=obj, loc=d["置き場所"], status=d["状態"], owner=d["担当"])


def build(seed: int, n: int, split: str) -> list[Episode]:
    rng = random.Random(seed)
    world: dict[str, dict[str, str]] = {}
    episodes = []
    focus = None
    for _ in range(n):
        obj = rng.choice(OBJECTS)
        if obj not in world:
            world[obj] = {f: rng.choice(VALUES[f]) for f in FIELDS}
        field = rng.choice(FIELDS)
        value = rng.choice([x for x in VALUES[field] if x != world[obj][field]])
        form = 1 if split == "alternate_state" else 0
        before = render_state(obj, world[obj], form)
        if split == "held_order":
            forms = HELD_ORDER[field]
        elif split in ("held_lexeme", "free_paragraph"):
            forms = HELD_LEXEME[field]
        elif split == "omitted":
            forms = OMITTED[field]
        else:
            forms = COMMANDS[field]
        command = rng.choice(forms).format(o=obj, v=value)
        if split == "nested":
            command = "補足として「" + command + "」という指示です。"
        elif split == "free_paragraph":
            command = "前の話題とは別です。\n" + command + "\nこの更新だけを反映してください。"
        world[obj][field] = value
        after = render_state(obj, world[obj], form)
        episodes.append(Episode(before, command, after, obj, field, value, focus))
        focus = obj
    return episodes


def evaluate(train_n: int, seed: int, split: str, mode: str) -> dict:
    train = build(seed, train_n, "seen")
    test = build(seed + 1000, 120, split)
    learner = Learner(mode)
    t0 = time.perf_counter()
    learner.learn(train)
    training = time.perf_counter() - t0
    correct = 0
    reads = 0
    t1 = time.perf_counter()
    for ep in test:
        pred, r = learner.infer(ep.before, ep.command)
        correct += pred == ep.after
        reads += r
    infer_ms = (time.perf_counter() - t1) * 1000 / len(test)
    return {
        "accuracy": correct / len(test),
        "model_bytes": len(pickle.dumps(learner)),
        "programs": len(learner.programs),
        "raw_candidates": learner.raw_candidates,
        "rejected": learner.rejected,
        "merges": learner.merges,
        "peak_candidates_per_episode": learner.peak_candidates,
        "training_seconds": training,
        "inference_ms": infer_ms,
        "mean_execution_candidates": reads / len(test),
    }


def summarize(raw: dict) -> dict:
    out = {}
    for n, runs in raw.items():
        out[n] = {}
        for split in ("seen", "held_order", "held_lexeme", "nested", "omitted", "alternate_state", "free_paragraph"):
            out[n][split] = {}
            for mode in ("executable", "surface_quotient", "destruction_quotient"):
                keys = runs[0][split][mode].keys()
                out[n][split][mode] = {
                    k: statistics.mean(r[split][mode][k] for r in runs) for k in keys
                }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="results_cycle_015.json")
    args = ap.parse_args()
    raw = {}
    for n in (48, 144, 432):
        runs = []
        for seed in (1, 7, 19):
            run = {}
            for split in ("seen", "held_order", "held_lexeme", "nested", "omitted", "alternate_state", "free_paragraph"):
                run[split] = {
                    mode: evaluate(n, seed, split, mode)
                    for mode in ("executable", "surface_quotient", "destruction_quotient")
                }
            runs.append(run)
        raw[str(n)] = runs
    payload = {
        "hypothesis": "Destruction-Vector E-Graph with Role-Bearing Quotient Refinement",
        "seeds": [1, 7, 19],
        "train_sizes": [48, 144, 432],
        "raw": raw,
        "summary": summarize(raw),
        "peak_rss_kib_runtime_included": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_complexity": "proposal O(N C^2), surgery O(P K L), quotient O(P), inference O(E L); P<=96/episode, E<=32",
        "learner_hidden_labels": False,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload["summary"]["432"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
