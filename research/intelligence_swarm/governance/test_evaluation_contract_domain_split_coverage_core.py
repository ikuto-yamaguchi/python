#!/usr/bin/env python3
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "benchmarks" / "grounded_causal" / "evaluation_contract.py"
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def row(domain: str, seed: int, split: str, suffix: str) -> dict:
    return {
        "instance_id": f"{domain}-{seed}-{split}-{suffix}",
        "domain": domain,
        "seed": seed,
        "split": split,
        "condition": "in_distribution",
        "utterance": f"utterance-{domain}-{seed}-{split}-{suffix}",
        "state_before": {"x": seed},
        "gold_action": 0,
        "gold_state_after": {"x": seed + 1},
    }


def complete_bundle() -> list[dict]:
    rows = []
    for domain in ("alpha", "beta"):
        for seed in sorted(module.CANONICAL_SEEDS):
            rows.append(row(domain, seed, "train", "a"))
            rows.append(row(domain, seed, "test", "b"))
    return rows


def test_complete_domain_local_coverage_passes() -> None:
    audit = module.validate_dataset(complete_bundle())
    assert audit["valid"], audit["errors"]
    assert audit["domain_local_train_eval_coverage_required"] is True


def test_train_only_and_eval_only_domains_fail_closed() -> None:
    rows = []
    for seed in sorted(module.CANONICAL_SEEDS):
        rows.append(row("train_only", seed, "train", "a"))
        rows.append(row("eval_only", seed, "test", "b"))
    audit = module.validate_dataset(rows)
    assert not audit["valid"]
    joined = "\n".join(audit["errors"])
    for seed in sorted(module.CANONICAL_SEEDS):
        assert f"domain 'train_only' seed {seed}: evaluation split is missing" in joined
        assert f"domain 'eval_only' seed {seed}: train split is missing" in joined


if __name__ == "__main__":
    test_complete_domain_local_coverage_passes()
    test_train_only_and_eval_only_domains_fail_closed()
    print("ok")
