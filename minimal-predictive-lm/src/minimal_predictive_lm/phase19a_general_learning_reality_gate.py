from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SUPPORTED_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml"}
DOMAIN_BY_SUFFIX = {".py": "code", ".md": "prose", ".json": "structured", ".yml": "structured", ".yaml": "structured"}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", "results", "artifacts"}

@dataclass(frozen=True)
class CorpusFile:
    path: str
    domain: str
    data: bytes
    rank: int

@dataclass(frozen=True)
class Merge:
    left: int
    right: int
    token: int
    count: int

@dataclass(frozen=True)
class NgramModel:
    order: int
    vocabulary_size: int
    alpha: float
    contexts: Mapping[tuple[int, ...], Counter[int]]
    totals: Mapping[tuple[int, ...], int]

    def bits(self, sequence: Sequence[int]) -> float:
        if not sequence:
            return 0.0
        history = [self.vocabulary_size, self.vocabulary_size + 1]
        bits = 0.0
        for token in sequence:
            context = tuple(history[-(self.order - 1):]) if self.order > 1 else ()
            counts = self.contexts.get(context)
            total = self.totals.get(context, 0)
            count = 0 if counts is None else counts.get(token, 0)
            probability = (count + self.alpha) / (total + self.alpha * self.vocabulary_size)
            bits -= math.log2(probability)
            history.append(token)
        return bits

def stable_rank(path: str) -> int:
    return int.from_bytes(hashlib.sha256(path.encode("utf-8")).digest()[:8], "big")

def collect_corpus(root: Path, *, per_file_limit: int = 16_384, total_limit: int = 786_432) -> tuple[tuple[CorpusFile, ...], tuple[CorpusFile, ...]]:
    rows: list[CorpusFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        data = path.read_bytes()[:per_file_limit]
        if not data:
            continue
        path_text = relative.as_posix()
        rows.append(CorpusFile(path_text, DOMAIN_BY_SUFFIX[path.suffix.lower()], data, stable_rank(path_text)))
    rows.sort(key=lambda row: row.rank)
    kept: list[CorpusFile] = []
    used = 0
    for row in rows:
        if used >= total_limit:
            break
        data = row.data[: total_limit - used]
        if data:
            kept.append(CorpusFile(row.path, row.domain, data, row.rank))
            used += len(data)
    train_rows: list[CorpusFile] = []
    heldout_rows: list[CorpusFile] = []
    for domain in sorted({row.domain for row in kept}):
        domain_rows = sorted((row for row in kept if row.domain == domain), key=lambda row: row.rank)
        for index, row in enumerate(domain_rows):
            (heldout_rows if index % 5 == 0 else train_rows).append(row)
    train = tuple(sorted(train_rows, key=lambda row: row.rank))
    heldout = tuple(sorted(heldout_rows, key=lambda row: row.rank))
    if not train or not heldout:
        raise ValueError("deterministic split produced an empty partition")
    return train, heldout

def nested_training_slice(files: Sequence[CorpusFile], fraction: float) -> tuple[CorpusFile, ...]:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    count = max(1, math.ceil(len(files) * fraction))
    return tuple(sorted(files, key=lambda row: row.rank)[:count])

def apply_one_merge(sequence: Sequence[int], merge: Merge) -> list[int]:
    output: list[int] = []
    index = 0
    while index < len(sequence):
        if index + 1 < len(sequence) and sequence[index] == merge.left and sequence[index + 1] == merge.right:
            output.append(merge.token)
            index += 2
        else:
            output.append(sequence[index])
            index += 1
    return output

def encode(data: bytes, merges: Sequence[Merge]) -> tuple[int, ...]:
    sequence = list(data)
    for merge in merges:
        sequence = apply_one_merge(sequence, merge)
    return tuple(sequence)

def learn_merges(files: Sequence[CorpusFile], *, max_merges: int = 64, minimum_count: int = 8) -> tuple[Merge, ...]:
    sequences = [list(row.data) for row in files]
    merges: list[Merge] = []
    for step in range(max_merges):
        pairs: Counter[tuple[int, int]] = Counter()
        for sequence in sequences:
            pairs.update(zip(sequence, sequence[1:]))
        if not pairs:
            break
        best_pair, best_count = min(pairs.items(), key=lambda item: (-item[1], item[0]))
        if best_count < minimum_count:
            break
        merge = Merge(best_pair[0], best_pair[1], 256 + step, best_count)
        merges.append(merge)
        sequences = [apply_one_merge(sequence, merge) for sequence in sequences]
    return tuple(merges)

def train_ngram(sequences: Iterable[Sequence[int]], *, order: int, vocabulary_size: int, alpha: float = 0.1) -> NgramModel:
    contexts: dict[tuple[int, ...], Counter[int]] = defaultdict(Counter)
    totals: Counter[tuple[int, ...]] = Counter()
    for sequence in sequences:
        history = [vocabulary_size, vocabulary_size + 1]
        for token in sequence:
            context = tuple(history[-(order - 1):]) if order > 1 else ()
            contexts[context][token] += 1
            totals[context] += 1
            history.append(token)
    return NgramModel(order, vocabulary_size, alpha, dict(contexts), dict(totals))

def merge_payload_bits(merges: Sequence[Merge]) -> int:
    if not merges:
        return 0
    width = max(8, math.ceil(math.log2(256 + len(merges) + 2)))
    return len(merges) * width * 2

def evaluate_model(model: NgramModel, heldout: Sequence[CorpusFile], merges: Sequence[Merge]) -> Mapping[str, object]:
    by_domain_bits: Counter[str] = Counter()
    by_domain_bytes: Counter[str] = Counter()
    total_bits = 0.0
    total_bytes = 0
    for row in heldout:
        bits = model.bits(encode(row.data, merges))
        total_bits += bits
        total_bytes += len(row.data)
        by_domain_bits[row.domain] += bits
        by_domain_bytes[row.domain] += len(row.data)
    dictionary_bits = merge_payload_bits(merges)
    return {
        "heldout_bytes": total_bytes,
        "likelihood_bits_per_byte": total_bits / total_bytes,
        "dictionary_amortized_bits_per_byte": (total_bits + dictionary_bits) / total_bytes,
        "dictionary_bits": dictionary_bits,
        "domain_bits_per_byte": {domain: by_domain_bits[domain] / by_domain_bytes[domain] for domain in sorted(by_domain_bytes)},
        "domain_bytes": dict(sorted(by_domain_bytes.items())),
    }

def run_gate(root: Path) -> Mapping[str, object]:
    train, heldout = collect_corpus(root)
    scaling: list[Mapping[str, object]] = []
    for fraction in (0.25, 0.5, 1.0):
        subset = nested_training_slice(train, fraction)
        merges = learn_merges(subset)
        model = train_ngram([encode(row.data, merges) for row in subset], order=3, vocabulary_size=256 + len(merges))
        scaling.append({
            "fraction": fraction,
            "training_files": len(subset),
            "training_bytes": sum(len(row.data) for row in subset),
            "merges": len(merges),
            **evaluate_model(model, heldout, merges),
        })
    full_train = nested_training_slice(train, 1.0)
    raw_model = train_ngram([tuple(row.data) for row in full_train], order=3, vocabulary_size=256)
    raw_metrics = evaluate_model(raw_model, heldout, ())
    full_metrics = scaling[-1]
    bpb = [float(row["dictionary_amortized_bits_per_byte"]) for row in scaling]
    domains = set(full_metrics["domain_bits_per_byte"])
    checks = {
        "heldout_is_file_disjoint": not ({row.path for row in train} & {row.path for row in heldout}),
        "mixed_domains_present": {"code", "prose", "structured"}.issubset(domains),
        "enough_heldout_bytes": int(full_metrics["heldout_bytes"]) >= 16_384,
        "scaling_is_monotonic": bpb[2] <= bpb[1] + 0.02 and bpb[1] <= bpb[0] + 0.02,
        "dictionary_beats_raw_byte_trigram": float(full_metrics["dictionary_amortized_bits_per_byte"]) < float(raw_metrics["dictionary_amortized_bits_per_byte"]),
        "no_task_labels_in_training_records": all(set(vars(row)) == {"path", "domain", "data", "rank"} for row in train),
    }
    return {
        "campaign": "phase19a_general_learning_reality_gate",
        "claim": "self-supervised mixed-repository byte prediction only",
        "train_files": len(train),
        "heldout_files": len(heldout),
        "train_bytes": sum(len(row.data) for row in train),
        "heldout_bytes": sum(len(row.data) for row in heldout),
        "scaling": scaling,
        "raw_byte_trigram": raw_metrics,
        "checks": checks,
        "passed": all(checks.values()),
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }

def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        "# Phase 19a: general-learning reality gate", "", f"Passed: **{result['passed']}**", "",
        "This is a self-supervised mixed-repository next-token/compression gate, not a claim of language understanding.", "",
        "| train fraction | train bytes | merges | heldout bpb |", "|---:|---:|---:|---:|",
    ]
    for row in result["scaling"]:
        lines.append(f"| {row['fraction']:.2f} | {row['training_bytes']} | {row['merges']} | {row['dictionary_amortized_bits_per_byte']:.4f} |")
    raw = result["raw_byte_trigram"]
    lines.extend(["", f"Raw-byte trigram baseline: **{raw['dictionary_amortized_bits_per_byte']:.4f} bits/byte**", "", "## Checks", ""])
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(["", "## Claim boundary", "", "- No free-form dialogue or Japanese high-school reasoning is demonstrated.", "- The corpus is the repository itself, not an internet-scale corpus.", "- A failure means the current representation-learning route does not yet show even this small scaling property."])
    return "\n".join(lines) + "\n"

def main() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_gate(root)
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "phase19a.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (results_dir / "phase19a.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
