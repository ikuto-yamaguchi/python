from __future__ import annotations
import random, time, json, pickle, resource, statistics
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class Example:
    text: str
    spans: list[tuple[int, int]]

FAMILIES = [
    ("{a}を{b}へ移して", ["a", "b"]),
    ("{a}の温度を{b}に設定して", ["a", "b"]),
    ("もし{a}なら{b}を止めて", ["a", "b"]),
    ("{a}が終わったら{b}を開始して", ["a", "b"]),
]
KNOWN_A = ["青い箱", "赤い容器", "試料A", "装置甲", "左側の部品", "小型ポンプ"]
KNOWN_B = ["棚", "保管庫", "25度", "停止状態", "搬送機", "検査工程"]
NONCE_A = ["ミラコフ", "ネグサ粒子", "未知体X7", "ふわる対象", "ケトラ装置"]
NONCE_B = ["ゾル棚", "42度域", "未知工程Q", "奥側区画", "休止モード"]


def instantiate(fmt: str, a: str, b: str) -> Example:
    text = fmt.format(a=a, b=b)
    spans = []
    pos = 0
    for value in (a, b):
        i = text.index(value, pos)
        spans.append((i, i + len(value)))
        pos = i + len(value)
    return Example(text, spans)


def make_data(seed: int, n_train: int = 160, n_test: int = 80):
    rng = random.Random(seed)
    train = [instantiate(rng.choice(FAMILIES)[0], rng.choice(KNOWN_A), rng.choice(KNOWN_B)) for _ in range(n_train)]
    test = [instantiate(rng.choice(FAMILIES)[0], rng.choice(NONCE_A), rng.choice(NONCE_B)) for _ in range(n_test)]
    paraphrase_formats = [
        "{a}を{b}まで運んで",
        "{a}の温度設定を{b}へ変更して",
        "{a}の場合は{b}を停止して",
        "{a}完了後、{b}を起動して",
    ]
    paraphrase = [instantiate(rng.choice(paraphrase_formats), rng.choice(NONCE_A), rng.choice(NONCE_B)) for _ in range(n_test)]
    return train, test, paraphrase


class MDLAnchorLattice:
    def __init__(self, min_len: int = 2, max_len: int = 8, min_count: int = 4, diversity: int = 3):
        self.min_len = min_len
        self.max_len = max_len
        self.min_count = min_count
        self.diversity = diversity
        self.anchors: dict[str, tuple[float, int, int]] = {}

    def fit(self, texts: list[str]):
        occurrences = defaultdict(list)
        for text in texts:
            for length in range(self.min_len, min(self.max_len, len(text)) + 1):
                for i in range(len(text) - length + 1):
                    span = text[i:i + length]
                    left = text[i - 1] if i else "^"
                    right = text[i + length] if i + length < len(text) else "$"
                    occurrences[span].append((left, right))
        scored = {}
        for span, contexts in occurrences.items():
            if len(contexts) < self.min_count:
                continue
            left_diversity = len({left for left, _ in contexts})
            right_diversity = len({right for _, right in contexts})
            gain = (len(contexts) - 1) * len(span) - len(span) - 2
            if gain > 0 and (left_diversity >= self.diversity or right_diversity >= self.diversity):
                scored[span] = (gain, left_diversity + right_diversity, len(contexts))
        self.anchors = dict(sorted(scored.items(), key=lambda item: (-item[1][0], -len(item[0])))[:300])
        return self

    def segment(self, text: str):
        matches = []
        for span, (gain, _, _) in self.anchors.items():
            start = 0
            while True:
                i = text.find(span, start)
                if i < 0:
                    break
                matches.append((i, i + len(span), gain + 0.1 * len(span), span))
                start = i + 1
        by_end = defaultdict(list)
        for match in matches:
            by_end[match[1]].append(match)
        dp = [(0.0, []) for _ in range(len(text) + 1)]
        for end in range(1, len(text) + 1):
            dp[end] = dp[end - 1]
            for begin, _, weight, span in by_end[end]:
                candidate = (dp[begin][0] + weight, dp[begin][1] + [(begin, end, span)])
                if candidate[0] > dp[end][0]:
                    dp[end] = candidate
        anchors = sorted(dp[len(text)][1])
        residuals = []
        cursor = 0
        for begin, end, _ in anchors:
            if begin > cursor and self._candidate(text[cursor:begin]):
                residuals.append((cursor, begin))
            cursor = max(cursor, end)
        if cursor < len(text) and self._candidate(text[cursor:]):
            residuals.append((cursor, len(text)))
        merged = []
        for span in residuals:
            if merged and span[0] - merged[-1][1] <= 1:
                merged[-1] = (merged[-1][0], span[1])
            else:
                merged.append(span)
        return merged, anchors

    @staticmethod
    def _candidate(fragment: str) -> bool:
        stripped = fragment.strip("、。！？, ")
        particles = set("をへにがはのとでならもし後")
        return len(stripped) >= 2 and not all(char in particles for char in stripped)


class PairAntiUnify:
    def fit(self, texts: list[str]):
        self.texts = texts
        return self

    def predict(self, text: str):
        best = None
        for known in self.texts:
            prefix = 0
            while prefix < min(len(known), len(text)) and known[prefix] == text[prefix]:
                prefix += 1
            suffix = 0
            while suffix < min(len(known) - prefix, len(text) - prefix) and known[-1 - suffix] == text[-1 - suffix]:
                suffix += 1
            score = prefix + suffix
            if best is None or score > best[0]:
                best = (score, prefix, len(text) - suffix)
        if not best or best[2] <= best[1]:
            return []
        return [(best[1], best[2])]


def span_f1(predicted, gold):
    predicted_chars = {i for begin, end in predicted for i in range(begin, end)}
    gold_chars = {i for begin, end in gold for i in range(begin, end)}
    true_positive = len(predicted_chars & gold_chars)
    precision = true_positive / len(predicted_chars) if predicted_chars else 0.0
    recall = true_positive / len(gold_chars) if gold_chars else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def evaluate(seed: int, min_count: int = 4, diversity: int = 3):
    train, nonce, paraphrase = make_data(seed)
    start = time.perf_counter()
    model = MDLAnchorLattice(min_count=min_count, diversity=diversity).fit([example.text for example in train])
    train_seconds = time.perf_counter() - start
    baseline = PairAntiUnify().fit([example.text for example in train])

    def score(data):
        f1s, exacts, latencies, anchor_counts = [], [], [], []
        for example in data:
            query_start = time.perf_counter_ns()
            predicted, anchors = model.segment(example.text)
            latencies.append((time.perf_counter_ns() - query_start) / 1e6)
            f1s.append(span_f1(predicted, example.spans))
            exacts.append(int(sorted(predicted) == sorted(example.spans)))
            anchor_counts.append(len(anchors))
        return {
            "f1": statistics.mean(f1s),
            "exact": statistics.mean(exacts),
            "latency_ms": statistics.mean(latencies),
            "anchors": statistics.mean(anchor_counts),
        }

    def score_baseline(data):
        values = [span_f1(baseline.predict(example.text), example.spans) for example in data]
        return statistics.mean(values)

    return {
        "seed": seed,
        "model_bytes": len(pickle.dumps(model)),
        "train_seconds": train_seconds,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "anchor_count": len(model.anchors),
        "nonce": score(nonce),
        "paraphrase": score(paraphrase),
        "baseline_nonce_f1": score_baseline(nonce),
        "baseline_paraphrase_f1": score_baseline(paraphrase),
    }


if __name__ == "__main__":
    results = [evaluate(seed) for seed in (1, 7, 19)]
    print(json.dumps(results, ensure_ascii=False, indent=2))
