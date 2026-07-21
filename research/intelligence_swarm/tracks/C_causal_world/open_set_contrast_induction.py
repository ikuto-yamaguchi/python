from __future__ import annotations
import json, random, time, resource, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter

NAMES = ["アオ", "ユキ", "ソラ", "ミナ", "レン", "ナギ", "トワ", "カイ"]
PLACES = ["北棚", "南箱", "窓辺", "入口", "奥室", "机下", "庭先", "書庫"]
VERBS = ["移す", "運ぶ", "置く"]
PARA_VERBS = ["持っていく", "場所を変える", "移動させる"]

STATE_TEMPLATES = [
    "{e}は{v}にある。",
    "{e}の場所は{v}だ。",
    "現在、{e}は{v}に置かれている。",
]
COMMAND_TEMPLATES = [
    "{e}を{v}へ{verb}。",
    "{e}の行き先を{v}にして。",
    "{v}へ{e}を{verb}よう。",
]
HELD_COMMANDS = [
    "今いる所から{v}まで、{e}を持っていって。",
    "{e}については、次の所在地を{v}へ変更して。",
]


def lcp(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return a[:i]


def lcsuf(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[-1 - i] == b[-1 - i]:
        i += 1
    return a[len(a) - i:] if i else ""


def middle_diff(a, b):
    p = lcp(a, b)
    s = lcsuf(a[len(p):], b[len(p):])
    ae = len(a) - len(s) if s else len(a)
    be = len(b) - len(s) if s else len(b)
    return p, a[len(p):ae], b[len(p):be], s


def common_substrings(strings, min_len=1):
    if not strings:
        return []
    base = min(strings, key=len)
    out = []
    for i in range(len(base)):
        for j in range(i + min_len, len(base) + 1):
            x = base[i:j]
            if all(x in s for s in strings):
                out.append(x)
    return sorted(set(out), key=lambda x: (-len(x), x))


def extract_invariants(before, after, command):
    # The learner receives no entity/value ontology. It induces surface spans
    # shared across before/after/command views.
    shared_all = common_substrings([before, after, command], 1)
    identity = max(shared_all, key=len, default="")
    p, old, new, s = middle_diff(before, after)
    cmd_parts = []
    for n in range(1, min(12, len(command)) + 1):
        for i in range(len(command) - n + 1):
            x = command[i:i + n]
            if x in after and x not in before:
                cmd_parts.append(x)
    new_hint = max(cmd_parts, key=len, default=new)
    return {
        "identity": identity,
        "old": old,
        "new": new,
        "new_hint": new_hint,
        "prefix": p,
        "suffix": s,
    }


@dataclass
class Bundle:
    before: str
    command: str
    after: str
    noop_after: str
    reverse_command: str
    reverse_after: str
    other_before: str
    other_command: str
    other_after: str


class ContrastInducer:
    def __init__(self, require_all=True):
        self.require_all = require_all
        self.rules = []
        self.rejected = 0

    def fit_one(self, b: Bundle):
        inv = extract_invariants(b.before, b.after, b.command)
        changed = b.before != b.after
        noop_stable = b.before == b.noop_after
        reverse_restores = b.reverse_after == b.before
        other_noninterference = (
            b.other_before.split("。")[-1:] == b.other_after.split("。")[-1:]
            or b.other_before != b.other_after
        )
        ok = changed and noop_stable
        if self.require_all:
            ok = ok and reverse_restores and other_noninterference
        if not ok or not inv["identity"] or not inv["new_hint"]:
            self.rejected += 1
            return
        cmd_skel = b.command.replace(inv["identity"], "<ID>").replace(inv["new_hint"], "<NEW>")
        before_skel = b.before.replace(inv["identity"], "<ID>").replace(inv["old"], "<OLD>")
        after_skel = b.after.replace(inv["identity"], "<ID>").replace(inv["new_hint"], "<NEW>")
        self.rules.append((cmd_skel, before_skel, after_skel))

    def fit(self, bundles):
        for b in bundles:
            self.fit_one(b)
        self.rules = list(Counter(self.rules).keys())

    def predict(self, before, command):
        candidates = []
        for cmd_skel, before_skel, after_skel in self.rules:
            cp = cmd_skel.split("<ID>")
            if len(cp) != 2:
                continue
            pre, rest = cp
            if not command.startswith(pre):
                continue
            tail = rest.split("<NEW>")
            if len(tail) != 2:
                continue
            mid, suf = tail
            if mid not in command or (suf and not command.endswith(suf)):
                continue
            id_part = command[len(pre):command.index(mid, len(pre))]
            new_start = command.index(mid, len(pre)) + len(mid)
            new_end = len(command) - len(suf) if suf else len(command)
            new_part = command[new_start:new_end]
            bs = before_skel.replace("<ID>", id_part).split("<OLD>")
            if len(bs) != 2 or not before.startswith(bs[0]) or not before.endswith(bs[1]):
                continue
            candidates.append(after_skel.replace("<ID>", id_part).replace("<NEW>", new_part))
        return candidates

    def serialize_bytes(self):
        return len(json.dumps(self.rules, ensure_ascii=False).encode())


def make_bundle(rng, held=False, confound=False):
    e, other = rng.sample(NAMES, 2)
    old, new, other_old, other_new = rng.sample(PLACES, 4)
    state_template = rng.choice(STATE_TEMPLATES)
    command_template = rng.choice(HELD_COMMANDS if held else COMMAND_TEMPLATES)
    verb = rng.choice(PARA_VERBS if held else VERBS)
    before = state_template.format(e=e, v=old)
    command = command_template.format(e=e, v=new, verb=verb)
    after = before if confound else state_template.format(e=e, v=new)
    noop = before
    reverse_command = command_template.format(e=e, v=old, verb=verb)
    reverse_after = before
    other_before = state_template.format(e=other, v=other_old)
    other_command = command_template.format(e=other, v=other_new, verb=verb)
    other_after = state_template.format(e=other, v=other_new)
    return Bundle(
        before,
        command,
        after,
        noop,
        reverse_command,
        reverse_after,
        other_before,
        other_command,
        other_after,
    )


def evaluate(model, rng, n, held=False, rename=False, confound=False):
    correct = 0
    abstain = 0
    for _ in range(n):
        b = make_bundle(rng, held=held, confound=confound)
        if rename:
            for src, dst in zip(NAMES, ["ヌル", "キオ", "ラマ", "セト", "ビア", "ホク", "メラ", "ジン"]):
                b = Bundle(*[x.replace(src, dst) for x in asdict(b).values()])
            for src, dst in zip(PLACES, ["第一域", "第二域", "第三域", "第四域", "第五域", "第六域", "第七域", "第八域"]):
                b = Bundle(*[x.replace(src, dst) for x in asdict(b).values()])
        preds = model.predict(b.before, b.command)
        if confound:
            abstain += int(len(preds) == 0 or b.after not in preds)
        else:
            correct += int(b.after in preds)
    return (abstain if confound else correct) / n


def run(seed, train_n):
    rng = random.Random(seed)
    train = [make_bundle(rng) for _ in range(train_n)]
    confounds = [make_bundle(rng, confound=True) for _ in range(max(4, train_n // 8))]
    models = {
        "action_only": ContrastInducer(False),
        "full_contrast": ContrastInducer(True),
    }
    rows = {}
    for name, model in models.items():
        started = time.perf_counter()
        model.fit(train + confounds)
        train_seconds = time.perf_counter() - started
        query_rng = random.Random(seed + 999)
        started = time.perf_counter()
        seen = evaluate(model, query_rng, 120)
        inference_ms = (time.perf_counter() - started) * 1000 / 120
        rows[name] = {
            "seen": seen,
            "rename": evaluate(model, random.Random(seed + 1001), 120, rename=True),
            "held_syntax": evaluate(model, random.Random(seed + 1002), 120, held=True),
            "confound_rejection": evaluate(model, random.Random(seed + 1003), 120, confound=True),
            "model_bytes": model.serialize_bytes(),
            "train_seconds": train_seconds,
            "inference_ms": inference_ms,
            "rules": len(model.rules),
            "rejected": model.rejected,
            "candidate_reads": len(model.rules),
        }
    return rows


def main():
    all_rows = []
    for train_n in (32, 128, 512):
        for seed in (1, 7, 19):
            rows = run(seed, train_n)
            for method, values in rows.items():
                all_rows.append({"train_n": train_n, "seed": seed, "method": method, **values})
    aggregate = {}
    fields = [
        "seen",
        "rename",
        "held_syntax",
        "confound_rejection",
        "model_bytes",
        "train_seconds",
        "inference_ms",
        "rules",
        "rejected",
        "candidate_reads",
    ]
    for train_n in (32, 128, 512):
        aggregate[str(train_n)] = {}
        for method in ("action_only", "full_contrast"):
            selected = [x for x in all_rows if x["train_n"] == train_n and x["method"] == method]
            aggregate[str(train_n)][method] = {
                key: sum(row[key] for row in selected) / len(selected) for key in fields
            }
    report = {
        "hypothesis": "Open-set contrast bundles can induce causal event skeletons without predefined value/entity sets.",
        "aggregate": aggregate,
        "runs": all_rows,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    output = Path(__file__).with_name("results_cycle_004.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))


def self_test():
    rng = random.Random(3)
    bundles = [make_bundle(rng) for _ in range(96)]
    invariants = extract_invariants(bundles[0].before, bundles[0].after, bundles[0].command)
    assert invariants["identity"] and invariants["new_hint"]
    model = ContrastInducer(True)
    model.fit(bundles)
    assert model.rules
    assert evaluate(model, random.Random(77), 60) > 0.25
    b = bundles[0]
    bad = Bundle(
        b.before,
        b.command,
        b.before,
        b.before,
        b.reverse_command,
        b.reverse_after,
        b.other_before,
        b.other_command,
        b.other_after,
    )
    rejected = ContrastInducer(True)
    rejected.fit([bad])
    assert not rejected.rules
    print("self-test: ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
