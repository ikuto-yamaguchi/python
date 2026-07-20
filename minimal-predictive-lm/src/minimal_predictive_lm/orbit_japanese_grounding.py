from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from .orbit_japanese_grounding_core import Binding, Episode, GroundedOrbit
from .orbit_japanese_grounding_dialogue import Dialogue, DialogueTurn, DiscourseOrbit
from .orbit_japanese_grounding_data import (
    FOLLOWUPS, accuracy, dialogue_accuracy, make_dialogue, make_episode,
)

def run(output_dir: Path, seed: int = 20260720) -> dict[str, object]:
    rng = random.Random(seed)
    training = [make_episode(rng, train=True) for _ in range(360)]
    training += [make_episode(rng, train=True, noop=True) for _ in range(120)]
    base = GroundedOrbit()
    started = time.perf_counter()
    base.fit(training)
    base_fit_ms = (time.perf_counter() - started) * 1000
    base_suites = {
        "unseen_entities_values": [make_episode(rng, train=False) for _ in range(200)],
        "surface_recombination": [make_episode(rng, train=False, recombined=True) for _ in range(200)],
        "state_renderer": [make_episode(rng, train=False, heldout_state=True) for _ in range(200)],
        "negation_recombination": [make_episode(rng, train=False, noop=True, recombined=True) for _ in range(120)],
    }
    base_results = {name: accuracy(base, rows) for name, rows in base_suites.items()}

    dialogue_training: list[Dialogue] = []
    for operator in FOLLOWUPS:
        dialogue_training.extend(make_dialogue(rng, operator, train=True) for _ in range(100))
    discourse = DiscourseOrbit()
    started = time.perf_counter()
    discourse.fit(dialogue_training)
    discourse_fit_ms = (time.perf_counter() - started) * 1000
    dialogue_results = {
        operator.lower(): dialogue_accuracy(
            discourse, [make_dialogue(rng, operator, train=False) for _ in range(150)]
        )
        for operator in FOLLOWUPS
    }
    report: dict[str, object] = {
        "capability_id": "ORBIT-JAPANESE-GROUNDING-001",
        "principle": (
            "Meaning is a transported intervention orbit grounded by observed state change; "
            "dialogue context is an executable role-binding stack, not a full token history."
        ),
        "architecture": {
            "transformer": False,
            "neural_network": False,
            "gradient_training": False,
            "action_labels": False,
            "full_history_attention": False,
            "retained_dialogue_fields": 4,
        },
        "base": {
            "training_episodes": len(training),
            "patterns": len(base.patterns),
            "fit_ms": base_fit_ms,
            "failures": len(base.failures),
            "results": base_results,
            "cancellation_markers": base.cancellation_markers,
        },
        "dialogue": {
            "training_dialogues": len(dialogue_training),
            "patterns": len(discourse.patterns),
            "fit_ms": discourse_fit_ms,
            "failures": len(discourse.failures),
            "results": dialogue_results,
        },
        "checks": {
            "all_base_suites_100_percent": all(value == 1.0 for value in base_results.values()),
            "all_dialogue_suites_100_percent": all(value == 1.0 for value in dialogue_results.values()),
            "base_operator_library_constant": len(base.patterns) == 6,
            "dialogue_operator_library_constant": len(discourse.patterns) == 8,
            "no_training_failures": not base.failures and not discourse.failures,
            "completion_claim_rejected": True,
        },
        "highschool_level_passed": False,
        "claim_boundary": (
            "Executable non-neural Japanese grounding and two-turn ellipsis were validated only in a narrow "
            "numeric transfer world. Unrestricted syntax, commonsense, free-form generation, long dialogue, "
            "multiple simultaneous referents, and entrance-exam knowledge remain unvalidated."
        ),
        "next_falsification": (
            "Use three-to-ten turns with competing referents, pronouns whose antecedent is not the latest binding, "
            "corrections, topic shifts, nested goals, and nonlinear operators."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "orbit-japanese-grounding-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/orbit-japanese-grounding-001"))
    parser.add_argument("--seed", type=int, default=20260720)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.output_dir, arguments.seed), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
