from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from . import sparc_hs18_remaining_gate as base_gate
from . import sparc_hs18_remaining_gate_v2 as disclosed_gate
from .semantic_causal_ranker_v2 import train_curriculum_semantic_ranker


DEVELOPMENT_TRAIN_STOP = 120
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
            rewritten_id = model_id.replace("v2", "curriculum-semantic-v5")
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
    model, training = train_curriculum_semantic_ranker(
        document,
        development_train_stop=DEVELOPMENT_TRAIN_STOP,
        development_stop=DEVELOPMENT_STOP,
    )
    model_path = output / "hs18_curriculum_causal_ranker.zlib"
    model.save(model_path)
    os.environ["MPM_SEMANTIC_CAUSAL_RANKER"] = str(model_path.resolve())
    _install_worker_v5()

    result = disclosed_gate.run_gate()
    result["curriculum_causal_ranker"] = asdict(training)
    protocol = result["protocol"]
    protocol["curriculum_development_train_rows"] = DEVELOPMENT_TRAIN_STOP
    protocol["curriculum_development_validation_rows"] = (
        DEVELOPMENT_STOP - DEVELOPMENT_TRAIN_STOP
    )
    protocol["curriculum_synthetic_train_rows"] = training.synthetic_train_rows
    protocol["curriculum_synthetic_holdout_rows"] = training.synthetic_holdout_rows
    protocol["curriculum_final_training_rows"] = training.final_training_rows
    protocol["curriculum_tail_targets_used"] = 0
    protocol["worker"] = "minimal_predictive_lm.sparc_hs18_worker_v5"
    result["checks"]["curriculum_tail_targets_excluded"] = (
        model.metadata["tail_targets_used"] == 0
    )
    result["checks"]["synthetic_holdout_at_least_80_percent"] = (
        training.synthetic_holdout_accuracy >= 0.80
    )
    result["checks"]["curriculum_ranker_serialized_below_1mb"] = (
        training.serialized_bytes < 1_000_000
    )
    result["passed"] = all(result["checks"].values())
    result["claim_boundary"] = (
        "The causal classifier learns from disclosed public development rows and "
        "procedurally generated event worlds with separate synthetic surface holdouts. "
        "No tail target is used. Prior aggregate leakage still forbids a strict unseen "
        "benchmark claim, and this remains far below high-school intelligence."
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
    (output / "hs18_curriculum_causal_training.json").write_text(
        json.dumps(result["curriculum_causal_ranker"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(base_gate.render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
