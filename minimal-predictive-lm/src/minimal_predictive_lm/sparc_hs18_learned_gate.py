from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from .generic_causal_judgement_v3 import GenericCausalJudgementV3
from .learned_causal_ranker import train_causal_ranker
from . import sparc_hs18_remaining_gate as base_gate
from . import sparc_hs18_remaining_gate_v2 as disclosed_gate


RANKER_TRAIN_STOP = 120
RANKER_DEVELOPMENT_STOP = 142


def _install_worker_v4() -> None:
    original = base_gate.base.run_command_adapter

    def run_command_adapter(manifest, policy, *, model_id, command, timeout_seconds):
        rewritten = command
        rewritten_id = model_id
        if any("sparc_hs18_worker_v2" in str(part) for part in command):
            rewritten = tuple(
                "minimal_predictive_lm.sparc_hs18_worker_v4"
                if str(part) == "minimal_predictive_lm.sparc_hs18_worker_v2"
                else part
                for part in command
            )
            rewritten_id = model_id.replace("v2", "learned-symbolic-v4")
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
    ranker, training = train_causal_ranker(
        document,
        GenericCausalJudgementV3,
        train_stop=RANKER_TRAIN_STOP,
        development_stop=RANKER_DEVELOPMENT_STOP,
    )
    ranker_path = output / "hs18_learned_causal_ranker.zlib"
    ranker.save(ranker_path)
    os.environ["MPM_CAUSAL_RANKER"] = str(ranker_path.resolve())
    _install_worker_v4()

    result = disclosed_gate.run_gate()
    result["learned_causal_ranker"] = asdict(training)
    protocol = result["protocol"]
    protocol["causal_ranker_selection_train_rows"] = RANKER_TRAIN_STOP
    protocol["causal_ranker_selection_validation_rows"] = (
        RANKER_DEVELOPMENT_STOP - RANKER_TRAIN_STOP
    )
    protocol["causal_ranker_final_training_rows"] = RANKER_DEVELOPMENT_STOP
    protocol["causal_ranker_tail_targets_used"] = 0
    protocol["worker"] = "minimal_predictive_lm.sparc_hs18_worker_v4"
    result["checks"]["causal_ranker_uses_development_only"] = (
        ranker.metadata["final_tail_targets_used"] == 0
        and RANKER_DEVELOPMENT_STOP <= protocol["highest_individual_target_index_inspected"] + 1
    )
    result["checks"]["causal_ranker_serialized_below_4mb"] = training.serialized_bytes < 4_000_000
    result["passed"] = all(result["checks"].values())
    result["claim_boundary"] = (
        "The causal ranker is trained on disclosed public development rows 0-141 and "
        "combined with a compact causal program under a policy selected only on rows "
        "120-141. Tail target labels are not used, but prior aggregate leakage means the "
        "tail is not a strict unseen benchmark. This is not high-school intelligence."
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
    (output / "hs18_learned_causal_training.json").write_text(
        json.dumps(result["learned_causal_ranker"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(base_gate.render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
