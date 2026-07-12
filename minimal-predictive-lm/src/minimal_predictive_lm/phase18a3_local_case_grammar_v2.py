from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from . import phase18a3_local_case_grammar as _base


# The first campaign exposed only one boundary environment for two actions.
# Add one independent case/order context for each rather than weakening the
# generic boundary-diversity prior used by the segmentation learner.
TRAINING_SPECS = (
    *_base.TRAINING_SPECS,
    ("受ける", "から", "へ", 1),
    ("移す", "が", "に", 0),
)
_base.TRAINING_SPECS = TRAINING_SPECS

ACTIONS = _base.ACTIONS
ENTITIES = _base.ENTITIES
ORDERS = _base.ORDERS
PARTICLE_BITS = _base.PARTICLE_BITS
Factor = _base.Factor
Fit = _base.Fit
LocalModel = _base.LocalModel
LiteralBaseline = _base.LiteralBaseline
NonIdentifiableLocalGrammarError = _base.NonIdentifiableLocalGrammarError
build = _base.build
contradictory_cycle_is_rejected = _base.contradictory_cycle_is_rejected
disconnected_graph_is_rejected = _base.disconnected_graph_is_rejected
evaluate_model = _base.evaluate_model
extract_factor = _base.extract_factor
fit_factors = _base.fit_factors
fit_rows = _base.fit_rows
heldout_specs = _base.heldout_specs
heldout_unseen_local_compositions = _base.heldout_unseen_local_compositions
induce_local_case_grammar = _base.induce_local_case_grammar
same_polarity_pair_abstains = _base.same_polarity_pair_abstains
semantic_training_observations = _base.semantic_training_observations
tied_majority_is_rejected = _base.tied_majority_is_rejected
training_observations = _base.training_observations
unknown_particle_abstains = _base.unknown_particle_abstains


def run() -> dict[str, object]:
    payload = _base.run()
    payload["campaign"]["name"] = "phase18a3-local-case-grammar-c2"
    payload["campaign"]["identifiability_repair"] = (
        "added a second independent boundary context for 受ける and 移す; "
        "the segmentation prior was not weakened"
    )
    checks = payload["theorem_checks"]
    old_key = "atomic_grammar_expands_nine_to_216_forms"
    if old_key in checks:
        value = checks.pop(old_key)
        checks["atomic_grammar_expands_observed_forms_to_216"] = value
    payload["all_theorem_checks_pass"] = all(checks.values())
    payload["resources"]["source_bytes"] += Path(__file__).read_bytes().__len__()
    payload["limitations"].insert(
        0,
        "two action boundary environments were added after the first frozen campaign exposed non-identifiability; this c2 run is a repaired prospective campaign, not the original c1 result",
    )
    return payload


def render_markdown(payload: Mapping[str, object]) -> str:
    text = _base.render_markdown(payload)
    note = (
        "\n## Identifiability repair\n\n"
        "The original c1 campaign failed because `受ける` and `移す` each appeared "
        "in only one boundary environment and were therefore absent from the "
        "generic substring candidate set. Campaign c2 adds one independent "
        "case/order environment for each action without weakening segmentation "
        "criteria.\n"
    )
    return text + note


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase18a3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a3.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
