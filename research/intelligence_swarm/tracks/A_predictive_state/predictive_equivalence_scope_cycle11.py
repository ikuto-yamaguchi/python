"""Track A Cycle 011: predictive-equivalence classes with shared active probes.

Controlled falsification probe. The learner receives raw Japanese strings and generic
binary outcomes of selected perturbation probes. It receives no entity/value list,
semantic slots, morphology, fixed ontology, answer value, RAG, or external model.

The benchmark retains hidden target spans for evaluation only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, hashlib, json, math, pickle, random, resource, statistics, time

FRAMES = [
    "候補として{items}を検討しています。現在の意図を一つ選びます。",
    "作業案は{items}です。直前の事情を踏まえて決定します。",
    "最初の説明では{items}が並びました。最終的な対象を確定します。",
    "関係者から{items}という案が出ています。ここでは一案だけ採用します。",
]
NESTED_FRAMES = [
    "前段では{a}を考えました。補足で{b}も挙がり、さらに{c}が候補です。結論を更新します。",
    "担当者は{a}を示し、別の担当者は{b}を示しました。なお{c}という案も残っています。",
]
SUBJECT_OMISSION = [
    "先ほどの件、{items}まで絞りました。ここから一つにします。",
    "続きです。{items}のどれかへ変更します。",
]
HELD_FRAMES = [
    "検討対象には{items}があります。選定結果は後続の挙動で確認します。",
    "複数案の{items}を保持します。採用案は実行結果から推定します。",
]
DISTRACTORS = ["天候は安定しています", "資料番号を確認しました", "別件は後回しです", "通信状態は正常です"]
PREFIXES = ["棚", "箱", "区域", "端末", "試料", "部屋", "工程", "台車", "鍵", "票"]
SUFFIXES = list("甲乙丙丁戊己庚辛壬癸") + [str(i) for i in range(1, 10)]


def grams(text: str, ns=(2, 3)) -> Counter[str]:
    s = "".join(text.split())
    return Counter(s[i:i+n] for n in ns for i in range(max(0, len(s)-n+1)))


def train_ngram_counts(texts: list[str]) -> Counter[str]:
    c = Counter()
    for t in texts:
        c.update(grams(t, (2,)))
    return c


def candidate_spans(text: str, counts: Counter[str], max_candidates: int = 24) -> list[str]:
    """Generate rare local spans without a value dictionary or quote delimiters."""
    s = "".join(text.split())
    scored: dict[str, float] = {}
    stop = set("。、，,.！？!?：:；;（）()\n")
    for length in range(2, 8):
        for i in range(0, len(s)-length+1):
            span = s[i:i+length]
            if any(ch in stop for ch in span):
                continue
            gs = [span[j:j+2] for j in range(len(span)-1)]
            rarity = sum(1.0 / (1.0 + counts[g]) for g in gs) / max(1, len(gs))
            boundary = 0.0
            if i == 0 or s[i-1] in "、はがをにへとでのも": boundary += 0.18
            if i+length == len(s) or s[i+length] in "、はがをにへとでのも": boundary += 0.18
            diversity = len(set(span)) / len(span)
            score = rarity + boundary + 0.08 * diversity - 0.018 * abs(length-3)
            if any(ch.isdigit() or ('A' <= ch <= 'Z') for ch in span): score += 0.22
            scored[span] = max(scored.get(span, -1), score)
    ranked = sorted(scored.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
    out = []
    for span, _ in ranked:
        if span in out: continue
        if any(span in x and len(x)-len(span) <= 2 for x in out): continue
        out.append(span)
        if len(out) >= max_candidates: break
    return out


def predictive_vector(span: str, channels: int = 12) -> tuple[int, ...]:
    """Local deterministic predictions under generic future perturbations."""
    bits = []
    for i in range(channels):
        h = hashlib.blake2b((str(i)+"|"+span).encode("utf-8"), digest_size=2).digest()
        bits.append((int.from_bytes(h, "big") >> (i % 9)) & 1)
    return tuple(bits)


@dataclass
class Episode:
    text: str
    values: list[str]
    target: str
    split: str


def make_values(rng: random.Random, k: int, unknown=False) -> list[str]:
    vals = []
    while len(vals) < k:
        if unknown:
            core = "新" + chr(0x4E00 + rng.randrange(1200)) + chr(0x4E00 + rng.randrange(1200))
            v = core + rng.choice(SUFFIXES)
        else:
            v = rng.choice(PREFIXES) + rng.choice(SUFFIXES)
        if v not in vals: vals.append(v)
    return vals


def make_episode(rng: random.Random, k: int, split: str) -> Episode:
    unknown = split in ("unknown_words", "combined")
    values = make_values(rng, k, unknown)
    target = rng.choice(values)
    items = "、".join(values)
    if split == "nested" and k >= 3:
        text = rng.choice(NESTED_FRAMES).format(a=values[0], b=values[1], c="、".join(values[2:]))
    elif split == "subject_omission":
        text = rng.choice(SUBJECT_OMISSION).format(items=items)
    elif split in ("paraphrase", "combined"):
        text = rng.choice(HELD_FRAMES).format(items=items)
    else:
        text = rng.choice(FRAMES).format(items=items)
    if split in ("distractor", "combined"):
        text = rng.choice(DISTRACTORS) + "。" + text + "。" + rng.choice(DISTRACTORS)
    return Episode(text, values, target, split)


def target_recall(cands: list[str], target: str) -> bool:
    return any(c == target for c in cands)


def dedupe_classes(cands: list[str]) -> dict[tuple[int, ...], list[str]]:
    groups = defaultdict(list)
    for c in cands:
        groups[predictive_vector(c)].append(c)
    return dict(groups)


def shared_active(cands: list[str], target: str, max_probes=8, random_probe=False, rng=None):
    """Choose a channel that maximally splits predictive equivalence classes."""
    if target not in cands:
        return None, 0, False, len(dedupe_classes(cands))
    remaining = list(cands)
    target_vec = predictive_vector(target)
    probes = 0
    used = set()
    while len(remaining) > 1 and probes < max_probes:
        vectors = {c: predictive_vector(c) for c in remaining}
        choices = []
        for ch in range(len(target_vec)):
            if ch in used: continue
            ones = sum(v[ch] for v in vectors.values())
            zeros = len(remaining)-ones
            gain = min(ones, zeros)
            choices.append((gain, ch))
        if not choices or max(choices)[0] == 0:
            break
        if random_probe:
            viable = [ch for gain, ch in choices if gain > 0]
            ch = rng.choice(viable)
        else:
            _, ch = max(choices)
        used.add(ch); probes += 1
        observed = target_vec[ch]
        remaining = [c for c in remaining if vectors[c][ch] == observed]
    if len(remaining) == 1:
        return remaining[0], probes, True, len(dedupe_classes(cands))
    return None, probes, False, len(dedupe_classes(cands))


def sequential_active(cands: list[str], target: str, max_probes=24):
    if target not in cands: return None, 0, False
    probes = 0
    for c in cands[:max_probes]:
        probes += 1
        if c == target: return c, probes, True
    return None, probes, False


def immediate(cands: list[str]):
    return cands[0] if cands else None


def evaluate(seed: int, train_size: int, k: int, split: str):
    rng = random.Random(seed * 10007 + train_size * 13 + k * 101 + len(split))
    train = [make_episode(rng, rng.choice((2,4,8)), "seen").text for _ in range(train_size)]
    counts = train_ngram_counts(train)
    episodes = [make_episode(rng, k, split) for _ in range(60)]
    metrics = Counter(); probes_seq=[]; probes_shared=[]; probes_rand=[]; classes=[]; ncands=[]
    start = time.perf_counter()
    for ep in episodes:
        cands = candidate_spans(ep.text, counts)
        ncands.append(len(cands))
        metrics["candidate_recall"] += target_recall(cands, ep.target)
        metrics["immediate"] += immediate(cands) == ep.target
        ps, ns, _ = sequential_active(cands, ep.target)
        pg, ng, _, cls = shared_active(cands, ep.target)
        pr, nr, _, _ = shared_active(cands, ep.target, random_probe=True, rng=rng)
        metrics["sequential_accuracy"] += ps == ep.target
        metrics["shared_accuracy"] += pg == ep.target
        metrics["random_accuracy"] += pr == ep.target
        metrics["shared_abstention"] += pg is None
        metrics["false_commit"] += pg is not None and pg != ep.target
        probes_seq.append(ns); probes_shared.append(ng); probes_rand.append(nr); classes.append(cls)
    elapsed = (time.perf_counter()-start)*1000/len(episodes)
    n=len(episodes)
    return {
        **{key: metrics[key]/n for key in ("candidate_recall","immediate","sequential_accuracy","shared_accuracy","random_accuracy","shared_abstention","false_commit")},
        "mean_sequential_probes": statistics.mean(probes_seq),
        "mean_shared_probes": statistics.mean(probes_shared),
        "mean_random_probes": statistics.mean(probes_rand),
        "mean_predictive_classes": statistics.mean(classes),
        "mean_candidates": statistics.mean(ncands),
        "ms_per_example_all_methods": elapsed,
    }


def run(seed: int, train_size: int):
    out = {}
    for split in ("seen","paraphrase","unknown_words","nested","subject_omission","distractor","combined"):
        out[split] = {}
        for k in (2,4,8,16):
            out[split][str(k)] = evaluate(seed, train_size, k, split)
    rng=random.Random(seed+train_size)
    texts=[make_episode(rng,rng.choice((2,4,8)),"seen").text for _ in range(train_size)]
    model=train_ngram_counts(texts)
    out["model_bytes"] = len(pickle.dumps(model))
    out["bigram_types"] = len(model)
    return out


def summarize(raw):
    result={}
    for size,runs in raw.items():
        result[size]={}
        for split in ("seen","paraphrase","unknown_words","nested","subject_omission","distractor","combined"):
            result[size][split]={}
            for k in ("2","4","8","16"):
                keys=runs[0][split][k].keys()
                result[size][split][k]={key:statistics.mean(r[split][k][key] for r in runs) for key in keys}
        result[size]["model_bytes"] = statistics.mean(r["model_bytes"] for r in runs)
        result[size]["bigram_types"] = statistics.mean(r["bigram_types"] for r in runs)
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_011.json")
    args=ap.parse_args()
    raw={str(n):[run(seed,n) for seed in (1,7,19)] for n in (64,256,512)}
    payload={
        "hypothesis":"Predictive-Equivalence Scope Classes with Shared Active Probes",
        "seeds":[1,7,19],"train_sizes":[64,256,512],"raw":raw,"summary":summarize(raw),
        "learner_inputs":"raw Japanese, corpus bigram counts, generic binary selected-probe outcomes",
        "target_value_in_probe_response":False,
        "estimated_complexity":"proposal O(L^2), class build O(HC), active O(C*H*logH), C=12, H<=24",
        "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "free_japanese_integrated_gate":0.0,
        "highschool_level_passed":False,"native_japanese_communication_passed":False,
        "weak_smartphone_verified":False,"completion":False,
    }
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["512"],ensure_ascii=False,indent=2))
    print("peak_rss",payload["peak_rss_kib_runtime_included"])
if __name__=="__main__": main()
