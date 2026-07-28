#!/usr/bin/env python3
"""Focused regression for Cycle 087 canonical split identity."""
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[3]
CORE = ROOT / "research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py"
PATCH = Path(__file__).with_name("apply_r0d_cycle_087_core_canonical_split_identity.py")


def load_core(path: Path):
    spec = importlib.util.spec_from_file_location("evaluation_contract_cycle_087", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def row(i: int, seed: int, split: str):
    is_eval = split != "train"
    return {
        "instance_id": f"i-{seed}-{split}-{i}",
        "domain": "rtfm",
        "seed": seed,
        "split": split,
        "condition": (
            "entity_holdout+dynamics_holdout+language_holdout"
            if is_eval
            else "in_distribution"
        ),
        "utterance": f"utterance-{seed}-{split}-{i}",
        "state_before": [i],
        "gold_action": i % 2,
        "gold_state_after": [i + 1],
        "entity_id": f"entity-{split}-{i}",
        "dynamics_id": f"dynamics-{split}-{i}",
    }


def dataset(eval_split: str = "test"):
    rows = []
    for seed in (1, 7, 19):
        rows.append(row(0, seed, "train"))
        rows.append(row(1, seed, eval_split))
    return rows


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py"
        target.parent.mkdir(parents=True)
        target.write_text(CORE.read_text(encoding="utf-8"), encoding="utf-8")

        # The workflow applies the hardening to CORE before this regression runs.
        # Keep standalone execution useful, but never require a second mutation of
        # an already-hardened temporary copy.
        target_text = target.read_text(encoding="utf-8")
        already_hardened = (
            "def canonical_split(" in target_text
            and '"canonical_split_identity_required": True' in target_text
            and "split must use exact canonical spelling" in target_text
        )
        if not already_hardened:
            patch = root / "research/intelligence_swarm/governance/apply.py"
            patch.parent.mkdir(parents=True)
            patch.write_text(PATCH.read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run(["python3", str(patch)], check=True)

        core = load_core(target)

        assert core.canonical_split("ＴＥＳＴ") == "test"
        assert core.canonical_split("te\u200bst") == "test"
        assert core.canonical_split(" test ") == "test"
        assert core.split_spelling_is_canonical("test")
        assert not core.split_spelling_is_canonical("ＴＥＳＴ")
        assert not core.split_spelling_is_canonical("te\u200bst")
        assert not core.split_spelling_is_canonical(" test ")

        good = core.validate_dataset(dataset("test"))
        assert good["valid"], json.dumps(good, ensure_ascii=False, indent=2)
        assert good["canonical_split_identity_required"] is True

        for alias in ("ＴＥＳＴ", "te\u200bst", " test "):
            audit = core.validate_dataset(dataset(alias))
            assert not audit["valid"]
            assert any("exact canonical spelling" in error for error in audit["errors"])

        canonical = dataset("test")[1]
        alias = dict(canonical, split="ＴＥＳＴ")
        assert core.instance_fingerprint(canonical) == core.instance_fingerprint(alias)

    print("cycle 087 canonical split regression: PASS")


if __name__ == "__main__":
    main()
