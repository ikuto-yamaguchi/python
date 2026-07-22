"""Track A Cycle 012: null-calibrated predictive classes with learned probe programs.

Controlled falsification probe. The learner sees raw Japanese strings and generic
binary outcomes from text perturbations. Hidden target spans are evaluator/environment
state only and never returned as labels. No morphology, ontology, semantic dictionary,
RAG, external LLM, Transformer, or task-specific classifier is used.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse, json, pickle, random, resource, statistics, time

FRAMES = [
    "装置の記録を更新します。{a}を優先し、{b}は保留してください。",
    "次の処理では{a}を採用します。補足として{b}も確認します。",
    "報告です。{b}ではなく{a}を実行対象にしてください。",
    "現在の方針は{a}です。なお{b}は比較用です。",
]
PARAPHRASE = [
    "処理方針を改めます。中心となるのは{a}で、{b}は参考情報に留めます。",
    "実行する内容として{a}を選びます。一方の{b}は今回は使いません。",
]
NESTED = [
    "担当者は『{b}という案ではなく、「{a}」を採る』と説明しました。",
    "記録には「比較候補『{b}』を退けて{a}へ進む」とあります。",
]
OMISSION = [
    "先ほどの案を見直します。今度は{a}にしてください。{b}はそのまま保留です。",
    "方針変更です。こちらは{a}へ。もう一方の{b}は触りません。",
]
DISTRACT = ["天候は曇りです。", "別件の資料を閉じました。", "時刻を確認しました。"]
TOKENS_A = ["青箱を棚三へ", "端末甲を再起動", "試料七を保管", "北鍵を担当二へ", "台車を廊下へ"]
TOKENS_B = ["赤箱を棚一へ", "端末乙を停止", "試料九を破棄", "南鍵を担当一へ", "票を室内へ"]


def grams(s: str) -> Counter[str]:
    s = "".join(s.split())
    return Counter(s[i:i+n] for n in (2, 3) for i in range(max(0, len(s)-n+1)))


@dataclass(frozen=True)
class Candidate:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Probe:
    kind: str
    i: int
    j: int = -1


class Learner:
    def __init__(self, null_enabled: bool, learned_probes: bool, cap: int = 32):
        self.null_enabled = null_enabled
        self.learned_probes = learned_probes
        self.cap = cap
        self.bg = Counter()
        self.probe_utility = Counter()
        self.probe_support = Counter()

    def fit_background(self, texts):
        for text in texts:
            self.bg.update(grams(text))

    def candidates(self, text):
        scored = []
        punctuation = set("。、！？『』「」\n")
        for i in range(len(text)):
            for length in range(3, 21):
                j = i + length
                if j > len(text):
                    break
                span = text[i:j]
                if any(ch in punctuation for ch in span):
                    continue
                gs = grams(span)
                rarity = sum(1 / (1 + self.bg[g]) for g in gs) / max(1, sum(gs.values()))
                diversity = len(set(span)) / max(1, len(span))
                boundary = int(i == 0 or text[i-1] in punctuation or text[i-1].isspace())
                boundary += int(j == len(text) or text[j] in punctuation or text[j].isspace())
                score = rarity + 0.18 * diversity + 0.08 * boundary
                scored.append((score, Candidate(i, j, span)))
        scored.sort(key=lambda item: (item[0], len(item[1].text)), reverse=True)
        output, seen = [], set()
        for _, candidate in scored:
            key = (candidate.start, candidate.end)
            if key not in seen:
                output.append(candidate)
                seen.add(key)
            if len(output) >= self.cap:
                break
        return output

    def probes(self, candidates):
        probes = [Probe("delete", i) for i in range(len(candidates))]
        for i in range(len(candidates)):
            for j in range(i + 1, min(len(candidates), i + 5)):
                probes.append(Probe("replace", i, j))
                if candidates[i].start < candidates[j].start:
                    probes.append(Probe("swap", i, j))
        if self.learned_probes:
            probes.sort(
                key=lambda p: (
                    self.probe_utility[p.kind] / max(1, self.probe_support[p.kind]),
                    -p.i,
                ),
                reverse=True,
            )
        else:
            probes.sort(key=lambda p: hash((p.kind, p.i, p.j)) & 0xFFFF)
        return probes[:64]

    @staticmethod
    def prediction(probe, candidate_index, candidates):
        if probe.kind == "delete":
            return int(candidate_index != probe.i)
        if probe.kind in ("replace", "swap"):
            return int(candidate_index not in (probe.i, probe.j))
        return 0

    def solve(self, text, oracle, max_probes=8):
        candidates = self.candidates(text)
        active = list(range(len(candidates)))
        if not active:
            return None, 0, candidates, 0.0
        mismatch = Counter()
        used = 0
        for probe in self.probes(candidates):
            if not active or used >= max_probes:
                break
            predictions = [self.prediction(probe, i, candidates) for i in active]
            if len(active) > 1 and len(set(predictions)) < 2:
                continue
            if len(active) == 1 and probe.i != active[0]:
                continue
            ones = sum(predictions)
            balance = min(ones, len(predictions) - ones)
            if len(active) > 1 and balance == 0:
                continue
            outcome = oracle(probe, candidates)
            used += 1
            before = len(active)
            for i in active:
                mismatch[i] += int(self.prediction(probe, i, candidates) != outcome)
            active = [i for i in active if self.prediction(probe, i, candidates) == outcome]
            gain = before - len(active)
            self.probe_support[probe.kind] += 1
            self.probe_utility[probe.kind] += gain
            if not active:
                break
        if len(active) == 1:
            i = active[0]
            residual = mismatch[i] / max(1, used)
            gs = grams(candidates[i].text)
            support = sum(1 / (1 + self.bg[g]) for g in gs) / max(1, sum(gs.values()))
            if self.null_enabled and (residual > 0.25 or support < 0.055):
                return None, used, candidates, residual
            return i, used, candidates, residual
        if not self.null_enabled and candidates:
            i = min(range(len(candidates)), key=lambda x: mismatch[x])
            return i, used, candidates, mismatch[i] / max(1, used)
        return None, used, candidates, 1.0


def make_example(rng, mode):
    a = rng.choice(TOKENS_A) + str(rng.randrange(10, 99))
    b = rng.choice(TOKENS_B) + str(rng.randrange(10, 99))
    if mode == "seen":
        frame = rng.choice(FRAMES)
    elif mode == "paraphrase":
        frame = rng.choice(PARAPHRASE)
    elif mode == "nested":
        frame = rng.choice(NESTED)
    elif mode == "omission":
        frame = rng.choice(OMISSION)
    elif mode == "distractor":
        frame = rng.choice(DISTRACT) + rng.choice(FRAMES) + rng.choice(DISTRACT)
    elif mode == "out_set":
        return "二つの候補を比較しました。前者ではなく後者の方針を採用します。", None, a, b
    else:
        raise ValueError(mode)
    return frame.format(a=a, b=b), a, a, b


def span_iou(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    intersection = max(0, hi - lo)
    union = max(a[1], b[1]) - min(a[0], b[0])
    return intersection / max(1, union)


def locate_target(text, target, candidates):
    if target is None:
        return None
    start = text.find(target)
    if start < 0:
        return None
    gold = (start, start + len(target))
    scores = [span_iou(gold, (c.start, c.end)) for c in candidates]
    if not scores or max(scores) < 0.60:
        return None
    return max(range(len(scores)), key=scores.__getitem__)


def oracle_factory(target_text, source_text):
    def oracle(probe, candidates):
        if target_text is None:
            return int((probe.i + probe.j + len(probe.kind)) % 3 == 0)
        target_index = locate_target(source_text, target_text, candidates)
        if target_index is None:
            return int((probe.i * 7 + probe.j * 3 + len(probe.kind)) % 2 == 0)
        return Learner.prediction(probe, target_index, candidates)
    return oracle


def run(seed, train_size, mode, method, count=60):
    rng = random.Random(seed * 1009 + train_size * 17 + len(mode))
    train = [make_example(rng, "seen")[0] for _ in range(train_size)]
    learner = Learner(
        null_enabled=method == "learned_null",
        learned_probes=method != "fixed",
    )
    learner.fit_background(train)
    correct = wrong = nulls = recall = probes = 0
    started = time.perf_counter()
    for _ in range(count):
        text, target, _, _ = make_example(rng, mode)
        index, num_probes, candidates, _ = learner.solve(
            text, oracle_factory(target, text)
        )
        probes += num_probes
        target_index = locate_target(text, target, candidates)
        recall += target_index is not None
        if index is None:
            nulls += 1
        elif target_index is not None and index == target_index:
            correct += 1
        else:
            wrong += 1
    elapsed = (time.perf_counter() - started) * 1000 / count
    return {
        "candidate_recall": recall / count,
        "accuracy": correct / count,
        "wrong_commit": wrong / count,
        "null_rate": nulls / count,
        "mean_probes": probes / count,
        "ms_per_example": elapsed,
        "model_bytes": len(pickle.dumps(learner)),
        "probe_library": dict(learner.probe_support),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results_cycle_012.json")
    args = parser.parse_args()
    raw = {}
    for size in (32, 96, 192):
        runs = []
        for seed in (1, 7, 19):
            result = {}
            for mode in ("seen", "paraphrase", "nested", "omission", "distractor", "out_set"):
                result[mode] = {
                    method: run(seed, size, mode, method)
                    for method in ("fixed", "learned", "learned_null")
                }
            runs.append(result)
        raw[str(size)] = runs
    summary = {}
    for size, runs in raw.items():
        summary[size] = {}
        for mode in runs[0]:
            summary[size][mode] = {}
            for method in runs[0][mode]:
                summary[size][mode][method] = {
                    key: statistics.mean(r[mode][method][key] for r in runs)
                    for key in runs[0][mode][method]
                    if key != "probe_library"
                }
    payload = {
        "hypothesis": "Null-Calibrated Predictive Classes with Learned Probe Programs",
        "seeds": [1, 7, 19],
        "train_sizes": [32, 96, 192],
        "raw": raw,
        "summary": summary,
        "peak_rss_kib_runtime_included": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_complexity": "proposal O(L^2), probe generation O(H^2), active update O(PH), H<=32,P<=8",
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False, indent=2)
    print(json.dumps(summary["192"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
