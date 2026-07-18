from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from . import semantic_causal_ranker as semantic
from . import sparc_hs18_remaining_gate as base_gate
from . import sparc_hs18_remaining_gate_v2 as disclosed_gate
from .sparc_hs18_learned_gate_v2 import normalized_causal_choice_rows


TRAIN_STOP = 120
DEVELOPMENT_STOP = 142


def _install_worker_v5() -> None:
    original = base_gate.base.run_command_adapter

    def run_command_adapter(manifest, policy, *, model_id, command, timeout_seconds):
        rewritten = command
        rewritten_id = model_id
        if any("sparc_hs18_worker_v2" in str(part) for part in command):
            rewritten = tuple(
                "minimal_predictive_lm.sparc_hs18_worker_v5"
                if str(part) == "minimal_predictive_lm.sparc_hs18_worker_v2"
                else part
                for part in command
            )
            rewritten_id = model_id.replace("v2", "semantic-learned-v5")
        return original(
            manifest,
            policy,
            model_id=rewritten_id,
            command=rewritten,
            timeout_seconds=timeout_seconds,
        )

    base_gate.base.run_command_adapter = run_command_adapter


def run_gate() -> dict[str, object]:
    output = Path("results")
    output.mkdir(exist_ok=True)
    payload = base_gate.base.download_verified_git_blob(
        f"{base_gate.base.BBH_BASE_URL}/causal_judgement.json",
        base_gate.CAUSAL_BLOB_SHA1,
    )
    document = json.loads(payload.decode("utf-8"))
    semantic.causal_choice_rows = normalized_causal_choice_rows
    model, training = semantic.train_semantic_causal_ranker(
        document,
        train_stop=TRAIN_STOP,
        development_stop=DEVELOPMENT_STOP,
    )
    model_path = output / "hs18_semantic_causal_ranker.zlib"
    model.save(model_path)
    os.environ["MPM_SEMANTIC_CAUSAL_RANKER"] = str(model_path.resolve())
    _install_worker_v5()

    result = disclosed_gate.run_gate()
    result["semantic_causal_ranker"] = asdict(training)
    protocol = result["protocol"]
    protocol["semantic_selection_train_rows"] = TRAIN_STOP
    protocol["semantic_selection_validation_rows"] = DEVELOPMENT_STOP - TRAIN_STOP
    protocol["semantic_final_training_rows"] = DEVELOPMENT_STOP
    protocol["semantic_tail_targets_used"] = 0
    protocol["worker"] = "minimal_predictive_lm.sparc_hs18_worker_v5"
    result["checks"]["semantic_ranker_development_only"] = (
        model.metadata["tail_targets_used"] == 0
        and DEVELOPMENT_STOP <= protocol["highest_individual_target_index_inspected"] + 1
    )
    result["checks"]["semantic_ranker_serialized_below_1mb"] = training.serialized_bytes < 1_000_000
    result["passed"] = all(result["checks"].values())
    result["claim_boundary"] = (
        "A compact learned classifier combines event, norm, intent, temporal, omission, "
        "and counterfactual features. It is trained and selected only on disclosed rows "
        "0-141. Tail labels are excluded, but prior aggregate leakage forbids a strict "
        "unseen claim. High-school intelligence and phone speed remain unproven."
    )
    return result


def main() -> None:
    result = run_gate()
    output = Path("results")
    (output / "sparc_hs18_remaining_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "sparc_hs18_remaining_gate.md").write_text(
        base_gate.render_markdown(result), encoding="utf-8"
    )
    (output / "hs18_semantic_causal_training.json").write_text(
        json.dumps(result["semantic_causal_ranker"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(base_gate.render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
