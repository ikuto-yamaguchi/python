from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

from .benchmark_harness import ABSTAIN_TOKEN, RunPolicy, answer_is_correct, run_command_adapter
from .phase13a_experiment import build_phase13a_manifest


def _max_parenthesis_depth(text: str) -> int:
    depth = 0
    maximum = 0
    for character in text:
        if character == "(":
            depth += 1
            maximum = max(maximum, depth)
        elif character == ")":
            depth -= 1
    return maximum


def _surface_features(prompt: str) -> dict[str, object]:
    return {
        "multiply_negative": bool(re.search(r"\*\s*-\s*\d", prompt)),
        "plus_negative": bool(re.search(r"\+\s*-\s*\d", prompt)),
        "subtract_negative": bool(re.search(r"-\s*-\s*\d", prompt)),
        "leading_negative": bool(re.search(r"(?:^|\()\s*-\s*\d", prompt)),
        "operator_counts": {
            "+": prompt.count("+"),
            "-": prompt.count("-"),
            "*": prompt.count("*"),
            "/": prompt.count("/"),
        },
        "max_parenthesis_depth": _max_parenthesis_depth(prompt),
    }


def run() -> dict[str, object]:
    manifest, _ = build_phase13a_manifest()
    policy = RunPolicy(
        max_output_chars=256,
        stop_sequences=("\n\n",),
        tools_allowed=(),
        temperature=0.0,
        seed=0,
    )
    report = run_command_adapter(
        manifest,
        policy,
        model_id="mpm-phase13b-generic-algebra-diagnostic",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase13b_worker"),
        timeout_seconds=300.0,
    )
    predictions = {row.example_id: row.text for row in report.predictions}
    failures: list[dict[str, object]] = []
    feature_outcomes: Counter[tuple[str, bool, str]] = Counter()
    for example in manifest.examples:
        if example.axis != "multistep_arithmetic":
            continue
        prediction = predictions.get(example.example_id, "").strip()
        if answer_is_correct(example, prediction):
            outcome = "correct"
        elif not prediction or prediction == ABSTAIN_TOKEN:
            outcome = "abstained"
        else:
            outcome = "wrong"
        features = _surface_features(example.prompt)
        for key in ("multiply_negative", "plus_negative", "subtract_negative", "leading_negative"):
            feature_outcomes[(key, bool(features[key]), outcome)] += 1
        if outcome != "correct":
            failures.append(
                {
                    "id": example.example_id,
                    "prompt": example.prompt,
                    "target": example.target,
                    "prediction": prediction,
                    "outcome": outcome,
                    "surface_features": features,
                }
            )
    return {
        "failures": failures,
        "failure_count": len(failures),
        "feature_outcomes": [
            {"feature": key, "present": present, "outcome": outcome, "count": count}
            for (key, present, outcome), count in sorted(feature_outcomes.items())
        ],
    }


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase13b_diagnostic.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
