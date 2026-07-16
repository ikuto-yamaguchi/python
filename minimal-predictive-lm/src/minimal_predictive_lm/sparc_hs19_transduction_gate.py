from __future__ import annotations

import json
from pathlib import Path
import random
import resource
import string
import sys
import time

from .sparc_dialogue_transducer import DialoguePair, SparseDialogueTransducer


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def _token(rng: random.Random, prefix: str) -> str:
    return prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))


def _pairs(count: int, *, seed: int, shifted: bool = False) -> tuple[DialoguePair, ...]:
    rng = random.Random(seed)
    rows: list[DialoguePair] = []
    for index in range(count):
        family = index % 4
        if family == 0:
            subject = _token(rng, "主題")
            answer = _token(rng, "回答")
            evidence = _token(rng, "根拠")
            caveat = _token(rng, "留保")
            source = _token(rng, "資料")
            user = (
                f"説明対象:{subject}; 資料:{source}; 注意:{caveat}; 理由:{evidence}; 結論:{answer}"
                if shifted
                else f"{subject}を説明。答え={answer}、根拠={evidence}、留保={caveat}、資料={source}。"
            )
            assistant = (
                f"{subject}については、{answer}。理由は{evidence}です。"
                f"ただし、{caveat}。出典は{source}です。"
            )
        elif family == 1:
            subject = _token(rng, "訂正主題")
            old_value = _token(rng, "旧値")
            new_value = _token(rng, "新値")
            evidence = _token(rng, "訂正根拠")
            user = (
                f"修正対象:{subject}; 根拠:{evidence}; 正:{new_value}; 誤:{old_value}"
                if shifted
                else f"{subject}を訂正。旧={old_value}、新={new_value}、根拠={evidence}。"
            )
            assistant = (
                f"{subject}は、{old_value}ではなく{new_value}です。"
                f"根拠は{evidence}です。"
            )
        elif family == 2:
            subject = _token(rng, "回答主題")
            answer = _token(rng, "結論")
            evidence = _token(rng, "証拠")
            source = _token(rng, "出典")
            user = (
                f"問い:{subject}; 出典:{source}; 証拠:{evidence}; 回答:{answer}"
                if shifted
                else f"{subject}に回答。結論={answer}、証拠={evidence}、出典={source}。"
            )
            assistant = (
                f"{subject}への答えは{answer}です。"
                f"根拠は{evidence}で、出典は{source}です。"
            )
        else:
            subject = _token(rng, "比較主題")
            answer = _token(rng, "比較結論")
            evidence = _token(rng, "比較根拠")
            caveat = _token(rng, "比較留保")
            user = (
                f"比較案件:{subject}; 注意:{caveat}; 証拠:{evidence}; 判断:{answer}"
                if shifted
                else f"{subject}を比較。結論={answer}、根拠={evidence}、留保={caveat}。"
            )
            assistant = (
                f"{subject}を比べると、{answer}。"
                f"根拠は{evidence}です。ただし、{caveat}。"
            )
        rows.append(DialoguePair(user, assistant))
    return tuple(rows)


def run_gate() -> tuple[dict[str, object], SparseDialogueTransducer]:
    started = time.perf_counter()
    training = _pairs(10_000, seed=1910)
    model = SparseDialogueTransducer(max_schemas=64, max_candidates=8)
    learned_schemas = model.fit(training)

    heldout = _pairs(512, seed=1911)
    correct = 0
    answered = 0
    max_candidates = 0
    max_feature_reads = 0
    failures: list[dict[str, object]] = []
    for row in heldout:
        prediction = model.transduce(row.user)
        answered += prediction.text is not None
        max_candidates = max(max_candidates, prediction.candidates)
        max_feature_reads = max(max_feature_reads, prediction.feature_reads)
        if prediction.text == row.assistant:
            correct += 1
        elif len(failures) < 16:
            failures.append(
                {
                    "user": row.user,
                    "expected": row.assistant,
                    "actual": prediction.text,
                    "mechanism": prediction.mechanism,
                }
            )

    shifted = _pairs(64, seed=1912, shifted=True)
    shifted_correct = 0
    shifted_answered = 0
    shifted_wrong = 0
    shifted_examples: list[dict[str, object]] = []
    for row in shifted:
        prediction = model.transduce(row.user)
        shifted_answered += prediction.text is not None
        shifted_correct += prediction.text == row.assistant
        shifted_wrong += prediction.text is not None and prediction.text != row.assistant
        if len(shifted_examples) < 8:
            shifted_examples.append(
                {
                    "user": row.user,
                    "expected": row.assistant,
                    "actual": prediction.text,
                    "mechanism": prediction.mechanism,
                }
            )

    restored = SparseDialogueTransducer.from_bytes(model.to_bytes())
    restoration_row = _pairs(1, seed=1913)[0]
    restoration_ok = restored.transduce(restoration_row.user).text == restoration_row.assistant
    report = model.report()
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    checks = {
        "ten_thousand_raw_dialogue_pairs": len(training) == 10_000,
        "induced_at_most_eight_schemas": learned_schemas <= 8,
        "heldout_exact_512_of_512": correct == len(heldout) == 512,
        "heldout_coverage_512_of_512": answered == 512,
        "max_candidates_at_most_eight": max_candidates <= 8,
        "max_feature_reads_at_most_128": max_feature_reads <= 128,
        "unseen_surface_wrong_answers_zero": shifted_wrong == 0,
        "unseen_surface_abstains_64_of_64": shifted_answered == 0,
        "save_restore_preserves_programs": restoration_ok,
        "serialized_model_at_most_16k": int(report["serialized_bytes"]) <= 16 * 1024,
        "explicit_semantic_slots_not_used": report["explicit_semantic_slots_used"] is False,
        "complete_response_selection_not_used": report["complete_response_selection_used"] is False,
    }
    result: dict[str, object] = {
        "capability_id": "SPARC-HS19-UNSUPERVISED-COPY-TRANSDUCTION",
        "training_pairs": len(training),
        "learned_schemas": learned_schemas,
        "heldout_values": {
            "examples": len(heldout),
            "correct": correct,
            "answered": answered,
            "max_candidates": max_candidates,
            "max_feature_reads": max_feature_reads,
            "failures": failures,
        },
        "surface_shift": {
            "examples": len(shifted),
            "correct": shifted_correct,
            "answered": shifted_answered,
            "wrong": shifted_wrong,
            "examples_preview": shifted_examples,
        },
        "resources": {
            "serialized_bytes": report["serialized_bytes"],
            "posting_edges": report["posting_edges"],
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "wall_seconds": elapsed,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS19 can induce copy-and-reorder variables from raw paired turns without "
            "explicit semantic slot labels, and generalises to unseen values inside learned "
            "surfaces. It deliberately abstains on wholly unseen phrasings. The remaining "
            "bottleneck is language-level schema transfer, not value copying or surface rendering."
        ),
    }
    return result, model


def render_markdown(result: dict[str, object]) -> str:
    heldout = result["heldout_values"]
    shift = result["surface_shift"]
    resources = result["resources"]
    return "\n".join(
        [
            "# SPARC-HS19: unsupervised dialogue copy transduction",
            "",
            f"Passed: **{result['passed']}**",
            f"- Raw training pairs: **{result['training_pairs']}**",
            f"- Induced schemas: **{result['learned_schemas']}**",
            f"- Unseen-value exact: **{heldout['correct']}/{heldout['examples']}**",
            f"- Max candidates / reads: **{heldout['max_candidates']} / {heldout['max_feature_reads']}**",
            f"- Unseen-surface coverage: **{shift['answered']}/{shift['examples']}**",
            f"- Unseen-surface wrong answers: **{shift['wrong']}**",
            f"- Model bytes: **{resources['serialized_bytes']}**",
            f"- Wall seconds: **{resources['wall_seconds']:.2f}**",
            "",
            "## Claim boundary",
            "",
            str(result["claim_boundary"]),
            "",
        ]
    )


def main() -> None:
    result, model = run_gate()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "sparc_hs19_transduction.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "sparc_hs19_transduction.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )
    (output_dir / "SPARC-HS19-transducer.model.zlib").write_bytes(model.to_bytes())
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
