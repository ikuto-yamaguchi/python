from __future__ import annotations

from collections import Counter
import json

from ._phase18a2_continuous_japanese_core import (
    action_candidate_lexemes,
    complete_semantic_rows,
    exact_cover_action_lexicons,
    induce_entity_grounding,
)
from .phase18a3_local_case_grammar_v2 import fit_rows, training_observations


def main() -> None:
    rows = training_observations()
    entities, grounding = induce_entity_grounding(rows)
    semantic = complete_semantic_rows(rows, entities)
    candidates = action_candidate_lexemes(semantic, entities)
    covers = exact_cover_action_lexicons(semantic, entities, candidates)
    failures: Counter[str] = Counter()
    valid: list[dict[str, object]] = []
    samples: list[dict[str, object]] = []
    for actions in covers:
        try:
            fit = fit_rows(semantic, entities, actions)
        except Exception as error:  # diagnostic boundary only
            key = f"{type(error).__name__}: {error}"
            failures[key] += 1
            if len(samples) < 20:
                samples.append({"actions": list(actions), "failure": key})
            continue
        valid.append(
            {
                "actions": list(actions),
                "errors": fit.errors,
                "particles": [list(row) for row in fit.particle_index],
                "orders": [list(row) for row in fit.orders],
            }
        )
    print(json.dumps({
        "rows": len(rows),
        "entity_grounding": [list(row) for row in entities],
        "grounding_cost": grounding.best_cost,
        "grounding_margin": grounding.margin,
        "semantic_rows": len(semantic),
        "candidate_actions": list(candidates),
        "exact_covers": len(covers),
        "valid_models": valid,
        "failure_counts": dict(failures),
        "failure_samples": samples,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
