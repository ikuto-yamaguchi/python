#!/usr/bin/env python3
"""Fail-closed validator for the Gaddy--Klein to SILG component mapping.

This audit does not train or score a model. It verifies that every component
claimed by the R0.2 method-transfer manifest has a concrete local symbol and
that the pinned method properties still match the implementation source.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_PUBLIC_COMMIT = "98c0dc68926ee9535f15019922d2ca871b0ac0b5"
EXPECTED_SEEDS = [1, 7, 19]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def defined_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def source_has_all(path: Path, fragments: list[str]) -> list[str]:
    source = path.read_text(encoding="utf-8")
    return [fragment for fragment in fragments if fragment not in source]


def audit(manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked_files: dict[str, dict[str, Any]] = {}

    if manifest.get("classification_on_failure") != "initial_reproduction_failure":
        errors.append("classification_on_failure must be initial_reproduction_failure")
    if manifest.get("claim_scope") != "faithful_method_transfer_not_numerical_reproduction":
        errors.append("claim_scope must forbid numerical-reproduction claims")

    public = manifest.get("public_reference", {})
    if public.get("commit") != EXPECTED_PUBLIC_COMMIT:
        errors.append(f"unexpected public reference commit: {public.get('commit')!r}")

    properties = manifest.get("fixed_method_properties", {})
    if properties.get("pretrained_language_model") is not False:
        errors.append("pretrained_language_model must be false")
    if properties.get("canonical_seeds") != EXPECTED_SEEDS:
        errors.append(f"canonical seeds must be {EXPECTED_SEEDS}")
    if properties.get("message_variables") != 20 or properties.get("message_symbols") != 30:
        errors.append("public default message space must remain 20 variables x 30 symbols")
    if properties.get("freeze_decoder_default") is not True:
        errors.append("freeze_decoder_default must be true")
    if properties.get("formal_rtfm_s1_holdouts") != {
        "entity": False,
        "dynamics": True,
        "language_form": False,
    }:
        errors.append("RTFM S1 formal holdout declaration changed")

    components = manifest.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty list")
        components = []

    ids = [str(component.get("id")) for component in components]
    if len(ids) != len(set(ids)):
        errors.append("component ids must be unique")

    default_file = manifest.get("local_implementation", {}).get("path")
    for component in components:
        component_id = str(component.get("id"))
        relative = component.get("local_symbol_file", default_file)
        symbols = component.get("local_symbols")
        evidence = component.get("required_evidence")
        author_files = component.get("author_files")

        if not relative or not isinstance(relative, str):
            errors.append(f"{component_id}: local symbol file missing")
            continue
        if not isinstance(symbols, list) or not symbols:
            errors.append(f"{component_id}: local_symbols must be non-empty")
            continue
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{component_id}: required_evidence must be non-empty")
        if not isinstance(author_files, list):
            errors.append(f"{component_id}: author_files must be a list")

        path = repo_root / relative
        if not path.is_file():
            errors.append(f"{component_id}: local file not found: {relative}")
            continue
        found = defined_symbols(path)
        missing_symbols = sorted(set(str(symbol) for symbol in symbols) - found)
        if missing_symbols:
            errors.append(f"{component_id}: missing local symbols {missing_symbols} in {relative}")
        checked_files[relative] = {
            "sha256": sha256(path),
            "defined_symbols": sorted(found),
        }

    baseline_rel = manifest.get("local_implementation", {}).get("path")
    baseline = repo_root / str(baseline_rel)
    if baseline.is_file():
        fragments = [
            "message_variables: int = 20",
            "message_symbols: int = 30",
            "freeze_decoder: bool = True",
            "nn.LSTM",
            "gumbel_softmax",
            "environment_logits.detach()",
            "parameter.requires_grad = False",
            "train_environment(transition, decoder",
            "train_language(transition, language, decoder",
        ]
        missing = source_has_all(baseline, fragments)
        if missing:
            errors.append(f"baseline implementation lost required method evidence: {missing}")

    comparison_rel = manifest.get("local_implementation", {}).get("comparison_harness")
    comparison = repo_root / str(comparison_rel)
    if comparison.is_file():
        fragments = [
            "class EndToEndModel",
            "class StateOnlyModel",
            "env_inference_bytes = parameter_bytes(env_language, env_decoder)",
            "e2e_inference_bytes = parameter_bytes(end_to_end)",
            "if env_inference_bytes != e2e_inference_bytes",
            "raise RuntimeError",
        ]
        missing = source_has_all(comparison, fragments)
        if missing:
            errors.append(f"comparison harness lost required controls: {missing}")

    online_rel = manifest.get("local_implementation", {}).get("online_evaluator")
    online = repo_root / str(online_rel)
    if online.is_file():
        fragments = [
            "def evaluate_method",
            "episode_seed = seed * 1_000_003 + episode",
            "initial_instance_fingerprint",
            "win = float(obs[\"reward\"][0][0].item() > 0.5)",
            "cpu_inference_ms_per_step",
            "peak_rss_kib",
            "def paired_gaps",
        ]
        missing = source_has_all(online, fragments)
        if missing:
            errors.append(f"online evaluator lost required resource/task evidence: {missing}")

    prohibited = set(manifest.get("prohibited_claims", []))
    required_prohibitions = {
        "numerical reproduction of ACL 2019 on RTFM",
        "held-out entity transfer on RTFM S1",
        "held-out language-form transfer on RTFM S1",
        "new architecture",
        "new intelligence principle",
        "capability progress before immutable three-seed results",
    }
    missing_prohibitions = sorted(required_prohibitions - prohibited)
    if missing_prohibitions:
        errors.append(f"missing prohibited claims: {missing_prohibitions}")

    return {
        "status": "passed" if not errors else "blocked",
        "classification": (
            "r02_gaddy_klein_component_mapping_passed"
            if not errors
            else "initial_reproduction_failure"
        ),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "public_reference_commit": public.get("commit"),
        "component_count": len(components),
        "checked_files": checked_files,
        "errors": errors,
        "new_architecture": False,
        "capability_progress_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = audit(args.manifest, args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 2)


if __name__ == "__main__":
    main()
