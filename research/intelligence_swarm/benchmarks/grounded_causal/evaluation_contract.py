#!/usr/bin/env python3
"""Fail-closed reproducibility, leakage and paired-statistics contract for R0.

Accepts canonical rows and the concrete SILG/RTFM typed trajectory schema.
Uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
import unicodedata
from decimal import Decimal, InvalidOperation
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

CANONICAL_REQUIRED = {"instance_id", "domain", "seed", "split", "condition", "utterance", "state_before", "gold_action", "gold_state_after"}
PRED_REQUIRED = {"instance_id", "method", "instance_fingerprint", "pred_action", "pred_state_after"}
REQUIRED_CONTROL_METHODS = {"random", "language_blind", "state_only", "target_label_shuffle", "outcome_shuffle"}
REQUIRED_METHODS = {"correct"} | REQUIRED_CONTROL_METHODS
SHUFFLE_METHODS = {"target_label_shuffle", "outcome_shuffle"}
SHUFFLE_REQUIRED = {"control_source_instance_id", "control_source_fingerprint"}
HELD_OUT_CONDITIONS = {"entity_holdout", "dynamics_holdout", "language_holdout"}
FORBIDDEN_MODEL_INPUT_FIELDS = {
    "gold_action", "gold_state_after", "gold_inverse", "answer", "label",
    "completed_trajectory", "post_treatment_state", "state_after", "action",
    "reward", "done", "terminal_observation", "episode_return", "episode_success",
}
FORBIDDEN_PREDICTION_FIELDS = {
    "gold_action", "gold_state_after", "gold_inverse", "answer", "label",
    "reward", "done", "terminal_observation", "episode_return", "episode_success",
    "completed_trajectory", "rollout", "future_state", "next_state_gold",
    "oracle_action", "target_action", "post_treatment_state", "state_after",
}
ALLOWED_PREDICTION_FIELDS = PRED_REQUIRED | {
    "pred_inverse", "control_source_instance_id", "control_source_fingerprint",
}
RESOURCE_FIELDS = {"model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item", "raw_log_sha256", "model_sha256", "data_sha256", "code_commit"}
ARTIFACT_FIELDS = (("raw_log_path", "raw_log_sha256"), ("model_path", "model_sha256"), ("data_path", "data_sha256"))
CANONICAL_SEEDS = {1, 7, 19}
TRAIN_SPLITS = {"train"}
EVAL_SPLITS = {"test", "eval", "validation", "valid"}
ALLOWED_SPLITS = TRAIN_SPLITS | EVAL_SPLITS


def normalize_schema_key(value: Any) -> str:
    """Collapse Unicode-width, snake/camel/kebab and spacing variants."""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return re.sub(r"[^a-z0-9]", "", text)


FORBIDDEN_MODEL_INPUT_ALIASES = {normalize_schema_key(k): k for k in FORBIDDEN_MODEL_INPUT_FIELDS}
FORBIDDEN_PREDICTION_ALIASES = {normalize_schema_key(k): k for k in FORBIDDEN_PREDICTION_FIELDS}
ALLOWED_PREDICTION_ALIASES = {normalize_schema_key(k): k for k in ALLOWED_PREDICTION_FIELDS}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{n}: each row must be an object")
            rows.append(obj)
    return rows


def read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return obj


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _is_hex(value: Any, n: int) -> bool:
    text = str(value)
    return len(text) == n and all(ch in "0123456789abcdefABCDEF" for ch in text)


def _finite_nonnegative(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) >= 0


def _finite_positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0


def _resolve_contained_artifact(base_dir: Path, relative: Any) -> tuple[Path | None, str | None]:
    """Resolve an artifact only when it is a non-symlinked file inside base_dir."""
    raw = str(relative)
    rel = Path(raw)
    if not raw or rel.is_absolute():
        return None, "artifact path must be a non-empty relative path"
    if any(part == ".." for part in rel.parts):
        return None, "artifact path must not contain parent traversal"
    root = base_dir.resolve()
    cursor = base_dir
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None, "artifact path must not traverse symlinks"
    try:
        resolved = (base_dir / rel).resolve(strict=True)
    except OSError as exc:
        return None, f"artifact path cannot be resolved: {exc}"
    if resolved != root and root not in resolved.parents:
        return None, "artifact resolves outside the bundle root"
    if not resolved.is_file():
        return None, "artifact is not a regular file"
    if resolved.stat().st_size <= 0:
        return None, "artifact must be non-empty"
    return resolved, None


def _finite_json(value: Any) -> bool:
    if value is None or isinstance(value, (bool, str, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite_json(item) for key, item in value.items())
    return False


def _action_is_valid(action: Any, mask: Any) -> bool:
    if mask is None:
        return True
    if not isinstance(action, int) or isinstance(action, bool):
        return False
    if isinstance(mask, list):
        return 0 <= action < len(mask) and bool(mask[action])
    if isinstance(mask, dict):
        return bool(mask.get(str(action), mask.get(action, False)))
    return False


def canonical_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "tokens:" + ",".join(str(int(x)) for x in value)
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(ch for ch in text if not ch.isspace() and unicodedata.category(ch) not in {"Cf", "Cc"})


def _truthy(row: dict[str, Any], key: str) -> bool:
    return row.get(key) is True or row.get(key) == 1 or str(row.get(key, False)).lower() == "true"


def _condition_parts(row: dict[str, Any]) -> set[str]:
    raw = unicodedata.normalize("NFKC", str(row.get("condition", ""))).casefold()
    return {part for part in re.split(r"[+,|\s]+", raw) if part}


def _declares_holdout(row: dict[str, Any], name: str) -> bool:
    key = f"{name}_holdout"
    return _truthy(row, key) or key in _condition_parts(row)


def adapt_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if "utterance" not in out and isinstance(out.get("text_tokens"), list):
        out["utterance"] = [int(x) for x in out["text_tokens"]]
        out["utterance_source"] = "text_tokens"
    if "gold_action" not in out and "action" in out:
        out["gold_action"] = out["action"]
    if "gold_state_after" not in out and "state_after" in out:
        out["gold_state_after"] = out["state_after"]
    if "valid_action_mask" not in out and "valid" in out:
        out["valid_action_mask"] = out["valid"]
    if "condition" not in out:
        flags = [name for name in HELD_OUT_CONDITIONS if _truthy(out, name)]
        out["condition"] = "+".join(sorted(flags)) if flags else "in_distribution"
    if "model_input_fields" not in out:
        out["model_input_fields"] = [k for k in ("utterance", "state_before", "history", "valid_action_mask") if k in out]
    if "model_input" not in out:
        out["model_input"] = {k: out[k] for k in out["model_input_fields"] if k in out}
    return out


def adapt_dataset(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [adapt_row(r) for r in rows]


def _find_forbidden_nested(value: Any, prefix: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for raw_key, nested in value.items():
            key = str(raw_key)
            path = f"{prefix}.{key}" if prefix else key
            canonical = FORBIDDEN_MODEL_INPUT_ALIASES.get(normalize_schema_key(key))
            if canonical is not None:
                found.append({"path": path, "key": key, "canonical": canonical})
            found.extend(_find_forbidden_nested(nested, path))
    elif isinstance(value, list):
        for i, nested in enumerate(value[:32]):
            found.extend(_find_forbidden_nested(nested, f"{prefix}[{i}]"))
    return found


def _canonical_identity_number(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        raw = str(value)
    elif isinstance(value, str):
        raw = canonical_text(value)
        if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?", raw):
            return None
    else:
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    number = number.normalize()
    if number == 0:
        number = Decimal(0)
    return format(number, "f")


def canonical_holdout_identity(value: Any) -> Any:
    """Canonicalize semantic split identities before hashing.

    This intentionally collapses Unicode width/case, whitespace and control/format
    differences, numeric-vs-string scalar aliases, and recursively normalizes
    mappings and sequences. Mapping keys are represented as sorted pairs so that
    normalization collisions remain visible and deterministic.
    """
    if value is None:
        return {"type": "null", "value": None}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    number = _canonical_identity_number(value)
    if number is not None:
        return {"type": "number", "value": number}
    if isinstance(value, str):
        return {"type": "text", "value": canonical_text(value)}
    if isinstance(value, dict):
        pairs = [
            [canonical_holdout_identity(key), canonical_holdout_identity(item)]
            for key, item in value.items()
        ]
        pairs.sort(key=lambda pair: json.dumps(pair[0], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return {"type": "mapping", "value": pairs}
    if isinstance(value, (list, tuple)):
        return {"type": "sequence", "value": [canonical_holdout_identity(item) for item in value]}
    if isinstance(value, (set, frozenset)):
        items = [canonical_holdout_identity(item) for item in value]
        items.sort(key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return {"type": "set", "value": items}
    return {"type": "text", "value": canonical_text(value)}


def _trajectory_split_identity(value: Any) -> str:
    """Normalize episode/observation identities before split-leakage comparison."""
    return stable_hash(canonical_holdout_identity(value))


def _split_sig(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        if row.get(key) is not None:
            return stable_hash(canonical_holdout_identity(row[key]))
    return None


def canonical_domain(value: Any) -> str:
    """Canonical domain label used by every dataset/statistics/resource cell."""
    return canonical_text(value)


def canonical_condition(value: Any) -> str:
    """Canonical order-independent condition token set."""
    raw = unicodedata.normalize("NFKC", str(value)).casefold()
    parts = {
        canonical_text(part)
        for part in re.split(r"[+,|\s]+", raw)
        if canonical_text(part)
    }
    return "+".join(sorted(parts))


def canonical_instance_id(value: Any) -> str:
    """Canonical identity used only to detect aliases; raw IDs remain binding keys."""
    return canonical_text(value)


def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(row["seed"]),
        canonical_domain(row["domain"]),
        str(row["split"]).lower(),
        canonical_condition(row["condition"]),
    )


def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    payload = {k: row.get(k) for k in keys}
    payload["domain"] = canonical_domain(row.get("domain", ""))
    payload["condition"] = canonical_condition(row.get("condition", ""))
    payload["split"] = str(row.get("split", "")).lower()
    return stable_hash(payload)


def validate_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    adapted = adapt_dataset(rows)
    errors, warnings = [], []
    seen, canonical_instance_ids, domains, seeds, conditions = set(), defaultdict(set), set(), set(), set()
    splits = Counter()
    texts = defaultdict(lambda: defaultdict(list))
    entities, dynamics = defaultdict(set), defaultdict(set)
    episode_splits, episode_seed_splits, observation_splits = defaultdict(set), defaultdict(set), defaultdict(set)
    fingerprints = {}
    leakage = silg_rows = 0
    alias_findings = []
    explicit_holdout_findings = []
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
    per_domain_seed_splits = defaultdict(set)
    raw_domains_by_canonical, raw_conditions_by_canonical = defaultdict(set), defaultdict(set)
    for index, row in enumerate(adapted, 1):
        missing = CANONICAL_REQUIRED - row.keys()
        if missing:
            errors.append(f"row {index}: missing fields {sorted(missing)}")
            continue
        iid = str(row["instance_id"])
        canonical_iid = canonical_instance_id(iid)
        if not canonical_iid:
            errors.append(f"row {index}: instance_id must be non-empty after canonicalization")
        if iid in seen:
            errors.append(f"row {index}: duplicate instance_id={iid}")
        seen.add(iid)
        canonical_instance_ids[canonical_iid].add(iid)
        fingerprints[iid] = instance_fingerprint(row)
        raw_domain, raw_condition = str(row["domain"]), str(row["condition"])
        domain, condition, split = canonical_domain(raw_domain), canonical_condition(raw_condition), str(row["split"]).lower()
        raw_domains_by_canonical[domain].add(raw_domain)
        raw_conditions_by_canonical[condition].add(raw_condition)
        if not domain:
            errors.append(f"row {index}: domain must be non-empty after canonicalization")
        if not split:
            errors.append(f"row {index}: split must be non-empty")
        elif split not in ALLOWED_SPLITS:
            errors.append(f"row {index}: unregistered split={split!r}; allowed={sorted(ALLOWED_SPLITS)}")
        if not condition:
            errors.append(f"row {index}: condition must be non-empty")
        domains.add(domain); conditions.add(condition); splits[split] += 1
        try:
            seed = int(row["seed"])
            seeds.add(seed); topology[(domain, split, condition)].add(seed); per_seed_splits[seed].add(split); per_domain_seed_splits[(domain, seed)].add(split)
        except (TypeError, ValueError):
            errors.append(f"row {index}: seed must be integer-like")
        if "text_tokens" in row:
            silg_rows += 1
            if row.get("utterance_source") != "text_tokens" and "utterance" not in rows[index - 1]:
                errors.append(f"row {index}: SILG text_tokens were not adapted as utterance")
        text = canonical_text(row["utterance"])
        texts[split][text].append(iid)
        if not text or text == "tokens:":
            warnings.append(f"row {index}: empty utterance")
        fields = row.get("model_input_fields", [])
        if not isinstance(fields, list):
            errors.append(f"row {index}: model_input_fields must be a list")
        else:
            bad = []
            for field_index, field in enumerate(fields):
                canonical = FORBIDDEN_MODEL_INPUT_ALIASES.get(normalize_schema_key(field))
                if canonical is not None:
                    bad.append(str(field))
                    alias_findings.append({"row": index, "source": "model_input_fields", "path": f"model_input_fields[{field_index}]", "key": str(field), "canonical_forbidden_key": canonical})
            if bad:
                leakage += 1
                errors.append(f"row {index}: alias-normalized forbidden model input fields {sorted(bad)}")
        nested = _find_forbidden_nested(row.get("model_input", {}), "model_input")
        if nested:
            leakage += 1
            alias_findings.extend({"row": index, "source": "model_input", "canonical_forbidden_key": item["canonical"], **item} for item in nested)
            errors.append(f"row {index}: alias-normalized forbidden keys inside model_input {sorted(item['path'] for item in nested)}")
        es, ds = _split_sig(row, "entity_id", "entity_signature"), _split_sig(row, "dynamics_id", "dynamics_signature")
        if es: entities[split].add(es)
        if ds: dynamics[split].add(ds)
        for holdout_name, signature in (("entity", es), ("dynamics", ds)):
            if not _declares_holdout(row, holdout_name):
                continue
            finding = {"row": index, "instance_id": iid, "split": split, "condition": condition, "holdout": holdout_name, "signature_present": signature is not None, "signature": signature}
            explicit_holdout_findings.append(finding)
            if split not in EVAL_SPLITS:
                errors.append(f"row {index}: explicit {holdout_name}_holdout must be on a registered evaluation split, found {split!r}")
            if signature is None:
                errors.append(f"row {index}: explicit {holdout_name}_holdout requires {holdout_name}_id or {holdout_name}_signature")
        if row.get("episode_id") is not None: episode_splits[_trajectory_split_identity(row["episode_id"])].add(split)
        if row.get("episode_seed") is not None: episode_seed_splits[_trajectory_split_identity(row["episode_seed"])].add(split)
        if row.get("observation_fingerprint") is not None: observation_splits[_trajectory_split_identity(row["observation_fingerprint"])].add(split)
    instance_id_collisions = {key: sorted(values) for key, values in canonical_instance_ids.items() if key and len(values) > 1}
    if instance_id_collisions:
        errors.append(f"instance_id aliases collide after canonicalization: {instance_id_collisions}")
    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if len(values) > 1}
    condition_collisions = {key: sorted(values) for key, values in raw_conditions_by_canonical.items() if len(values) > 1}
    if domain_collisions:
        errors.append(f"domain labels collide after canonicalization: {domain_collisions}")
    if condition_collisions:
        errors.append(f"condition labels collide after canonicalization: {condition_collisions}")
    overlap = {}; train_text = set(texts.get("train", {}))
    for split, values in texts.items():
        if split == "train": continue
        shared = sorted(train_text & set(values))
        overlap[split] = {"count": len(shared), "examples": [{"normalized": value, "train_instance_ids": texts["train"][value][:5], "eval_instance_ids": values[value][:5]} for value in shared[:5]]}
        if split in EVAL_SPLITS and shared: errors.append(f"Unicode-normalized utterance leakage train->{split}: {len(shared)} utterances")
    holdout = {}
    mappings = {"entity": entities, "dynamics": dynamics}
    for name, mapping in mappings.items():
        train_values = mapping.get("train", set())
        for split, values in mapping.items():
            if split == "train": continue
            shared = train_values & values
            holdout[f"{name}:train->{split}"] = {"train_unique": len(train_values), "eval_unique": len(values), "overlap": len(shared)}
            if any(str(r.get("split", "")).lower() == split and _declares_holdout(r, name) for r in adapted) and shared:
                errors.append(f"{name} holdout violation train->{split}: {len(shared)} shared signatures")
    for finding in explicit_holdout_findings:
        signature = finding.get("signature")
        if signature is not None and signature in mappings[finding["holdout"]].get("train", set()):
            errors.append(f"row {finding['row']}: explicit {finding['holdout']}_holdout reuses a train signature for instance={finding['instance_id']}")
            finding["overlaps_train"] = True
        else:
            finding["overlaps_train"] = False
    split_leakage = {}
    for name, mapping in (("episode_id", episode_splits), ("episode_seed", episode_seed_splits), ("observation_fingerprint", observation_splits)):
        shared = sorted(k for k, v in mapping.items() if "train" in v and v & EVAL_SPLITS)
        split_leakage[name] = shared[:10]
        if shared: errors.append(f"train/eval {name} leakage: {len(shared)} shared values")
    if seeds != CANONICAL_SEEDS: errors.append(f"dataset seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
    for cell, cell_seeds in sorted(topology.items()):
        if cell_seeds != CANONICAL_SEEDS: errors.append(f"dataset cell {cell} must contain seeds {sorted(CANONICAL_SEEDS)}, found {sorted(cell_seeds)}")
    for seed in sorted(CANONICAL_SEEDS):
        if "train" not in per_seed_splits.get(seed, set()): errors.append(f"seed {seed}: train split is missing")
        if not (EVAL_SPLITS & per_seed_splits.get(seed, set())): errors.append(f"seed {seed}: evaluation split is missing")
    for domain in sorted(domains):
        for seed in sorted(CANONICAL_SEEDS):
            domain_seed_splits = per_domain_seed_splits.get((domain, seed), set())
            if "train" not in domain_seed_splits:
                errors.append(f"domain {domain!r} seed {seed}: train split is missing")
            if not (EVAL_SPLITS & domain_seed_splits):
                errors.append(f"domain {domain!r} seed {seed}: evaluation split is missing")
    if not domains: errors.append("need >=1 domain")
    missing_holdouts = HELD_OUT_CONDITIONS - {name for c in conditions for name in HELD_OUT_CONDITIONS if name in c}
    if missing_holdouts: warnings.append(f"missing held-out conditions: {sorted(missing_holdouts)}")
    return {"valid": not errors, "errors": errors, "warnings": sorted(set(warnings)), "instances": len(adapted), "domains": sorted(domains), "seeds": sorted(seeds), "conditions": sorted(conditions), "split_counts": dict(sorted(splits.items())), "utterance_overlap": overlap, "utterance_normalization": "NFKC + casefold + remove whitespace/control-format characters", "holdout_integrity": holdout, "explicit_holdout_findings": explicit_holdout_findings, "explicit_condition_holdout_required": True, "split_identity_leakage": split_leakage, "leakage_rows": leakage, "schema_alias_findings": alias_findings, "schema_alias_normalization": "NFKC + casefold + remove non-ASCII-alphanumeric", "silg_rows_adapted": silg_rows, "dataset_sha256": stable_hash(adapted), "instance_fingerprints_sha256": stable_hash(fingerprints), "seed_domain_split_condition_topology": {str(k): sorted(v) for k, v in sorted(topology.items())}, "canonical_seed_topology_required": True, "domain_local_train_eval_coverage_required": True, "domain_seed_split_coverage": {str(k): sorted(v) for k, v in sorted(per_domain_seed_splits.items())}, "adapted_schema": True, "silg_text_tokens_supported": True, "episode_split_isolation_required": True, "normalized_trajectory_identity_required": True, "trajectory_identity_normalization": "recursive NFKC + casefold + remove whitespace/control-format + numeric scalar alias collapse", "unicode_utterance_overlap_required": True, "holdout_identity_normalization": "recursive NFKC + casefold + remove whitespace/control-format + numeric scalar alias collapse", "normalized_holdout_identity_required": True, "alias_normalized_leakage_required": True, "allowed_train_splits": sorted(TRAIN_SPLITS), "allowed_evaluation_splits": sorted(EVAL_SPLITS), "split_scope_fail_closed": True, "normalized_cell_identity_required": True, "cell_identity_normalization": "domain=NFKC+casefold+remove whitespace/control-format; condition=canonical sorted token set", "domain_label_collisions": domain_collisions, "condition_label_collisions": condition_collisions, "canonical_instance_identity_required": True, "exact_prediction_instance_id_required": True, "instance_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters", "instance_id_collisions": instance_id_collisions}


def _mean_ci(values: list[float]) -> tuple[float, float, float]:
    if not values: return math.nan, math.nan, math.nan
    mean = statistics.mean(values)
    if len(values) == 1: return mean, mean, mean
    se = statistics.stdev(values) / math.sqrt(len(values)); z = 1.959963984540054
    return mean, mean - z * se, mean + z * se


def _paired_p(diffs: list[float], trials: int = 20000, seed: int = 20260724) -> float:
    values = [v for v in diffs if v != 0]
    if not values: return 1.0
    observed, n = abs(statistics.mean(values)), len(values)
    if n <= 18:
        samples = [abs(statistics.mean(v if (mask >> i) & 1 else -v for i, v in enumerate(values))) for mask in range(1 << n)]
        return sum(v >= observed - 1e-15 for v in samples) / len(samples)
    rng = random.Random(seed); extreme = 0
    for _ in range(trials): extreme += abs(statistics.mean(v if rng.random() < .5 else -v for v in values)) >= observed - 1e-15
    return (extreme + 1) / (trials + 1)


def _mcnemar_exact(a: int, b: int) -> float:
    n = a + b
    if n == 0: return 1.0
    k = min(a, b)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def _cluster_bootstrap_ci(groups: dict[tuple[int, str, str, str], list[float]], trials: int = 5000, seed: int = 20260724) -> tuple[float, float]:
    keys = sorted(groups)
    if not keys: return math.nan, math.nan
    rng = random.Random(seed); estimates = []
    for _ in range(trials):
        sampled = []
        for key in [keys[rng.randrange(len(keys))] for _ in keys]:
            vals = groups[key]; sampled.extend(vals[rng.randrange(len(vals))] for _ in vals)
        estimates.append(statistics.mean(sampled))
    estimates.sort()
    return estimates[max(0, int(.025 * len(estimates)) - 1)], estimates[min(len(estimates) - 1, int(.975 * len(estimates)))]


def _validate_shuffle_assignments(preds: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], eval_ids: set[str]) -> tuple[list[str], dict[str, Any]]:
    errors, audit = [], {}
    for method in sorted(SHUFFLE_METHODS):
        rows = [r for r in preds if str(r.get("method")) == method and str(r.get("instance_id")) in eval_ids]
        by_cell, donors = defaultdict(list), defaultdict(list)
        for i, pred in enumerate(rows, 1):
            missing = SHUFFLE_REQUIRED - pred.keys()
            if missing: errors.append(f"{method} row {i}: missing shuffle provenance {sorted(missing)}"); continue
            iid, donor_id = str(pred["instance_id"]), str(pred["control_source_instance_id"])
            target, donor = by_id[iid], by_id.get(donor_id)
            if donor is None or donor_id not in eval_ids: errors.append(f"{method} row {i}: unknown/non-eval donor {donor_id}"); continue
            if donor_id == iid: errors.append(f"{method} row {i}: self-shuffle is not allowed for {iid}")
            if str(pred["control_source_fingerprint"]) != instance_fingerprint(donor): errors.append(f"{method} row {i}: donor fingerprint mismatch for {iid}<-{donor_id}")
            if method == "target_label_shuffle" and pred.get("pred_action") != donor.get("gold_action"):
                errors.append(f"{method} row {i}: pred_action is not bound to donor gold_action for {iid}<-{donor_id}")
            if method == "outcome_shuffle" and pred.get("pred_state_after") != donor.get("gold_state_after"):
                errors.append(f"{method} row {i}: pred_state_after is not bound to donor gold_state_after for {iid}<-{donor_id}")
            tc, dc = _cell_key(target), _cell_key(donor)
            if tc != dc: errors.append(f"{method} row {i}: donor crosses seed/domain/split/condition cell")
            by_cell[tc].append(iid); donors[tc].append(donor_id)
        cells = {}
        for cell in sorted(by_cell):
            targets, ds = by_cell[cell], donors[cell]
            bijective = len(targets) == len(set(ds)) and set(targets) == set(ds)
            deranged = all(a != b for a, b in zip(targets, ds))
            if not bijective: errors.append(f"{method} cell {cell}: donor assignment is not a bijection")
            if not deranged: errors.append(f"{method} cell {cell}: donor assignment is not a derangement")
            cells[str(cell)] = {"n": len(targets), "unique_donors": len(set(ds)), "bijective": bijective, "deranged": deranged}
        audit[method] = {
            "rows": len(rows),
            "cells": cells,
            "provenance_required": True,
            "donor_value_binding_required": True,
            "bound_field": "pred_action<-donor.gold_action" if method == "target_label_shuffle" else "pred_state_after<-donor.gold_state_after",
        }
    return errors, audit


def score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:
    dataset_audit = validate_dataset(data)
    adapted = adapt_dataset(data)
    by_id = {str(r["instance_id"]): r for r in adapted}
    canonical_to_raw_ids = defaultdict(set)
    for raw_id in by_id:
        canonical_to_raw_ids[canonical_instance_id(raw_id)].add(raw_id)
    dataset_splits = {str(r.get("split", "")).lower() for r in adapted}
    invalid_dataset_splits = sorted(dataset_splits - ALLOWED_SPLITS)
    eval_ids = {i for i, r in by_id.items() if str(r["split"]).lower() in EVAL_SPLITS}
    errors, seen = list(dataset_audit.get("errors", [])), set(); method_ids, grouped, snapshots, outcomes = defaultdict(set), defaultdict(list), defaultdict(set), defaultdict(dict)
    gold_inverse_ids = {iid for iid in eval_ids if "gold_inverse" in by_id[iid]}
    pred_inverse_ids = defaultdict(set)
    if invalid_dataset_splits:
        errors.append(f"dataset contains unregistered splits: {invalid_dataset_splits}; allowed={sorted(ALLOWED_SPLITS)}")
    payload_findings, alias_findings = [], []
    for index, pred in enumerate(preds, 1):
        missing = PRED_REQUIRED - pred.keys()
        if missing: errors.append(f"prediction row {index}: missing {sorted(missing)}"); continue
        iid, method = str(pred["instance_id"]), str(pred["method"]); key = (iid, method)
        leaked, unexpected_fields, normalized_seen = [], [], {}
        for raw_key in pred:
            normalized = normalize_schema_key(raw_key)
            if normalized in normalized_seen and normalized_seen[normalized] != str(raw_key): errors.append(f"prediction row {index}: alias-colliding keys {normalized_seen[normalized]!r} and {str(raw_key)!r}")
            normalized_seen[normalized] = str(raw_key)
            canonical = FORBIDDEN_PREDICTION_ALIASES.get(normalized)
            if canonical is not None:
                leaked.append(str(raw_key)); alias_findings.append({"row": index, "instance_id": iid, "key": str(raw_key), "canonical_forbidden_key": canonical})
            elif normalized not in ALLOWED_PREDICTION_ALIASES or str(raw_key) != ALLOWED_PREDICTION_ALIASES[normalized]: unexpected_fields.append(str(raw_key))
        leaked, unexpected_fields = sorted(set(leaked)), sorted(set(unexpected_fields))
        if leaked: payload_findings.append({"row": index, "instance_id": iid, "kind": "alias_normalized_forbidden_gold_or_outcome_fields", "fields": leaked}); errors.append(f"prediction row {index}: alias-normalized forbidden gold/outcome fields {leaked}")
        if unexpected_fields: payload_findings.append({"row": index, "instance_id": iid, "kind": "unregistered_prediction_fields", "fields": unexpected_fields}); errors.append(f"prediction row {index}: unregistered fields {unexpected_fields}")
        if not _finite_json(pred.get("pred_state_after")): errors.append(f"prediction row {index}: pred_state_after contains non-finite or unsupported values")
        if "pred_inverse" in pred and not _finite_json(pred.get("pred_inverse")): errors.append(f"prediction row {index}: pred_inverse contains non-finite or unsupported values")
        if key in seen: errors.append(f"prediction row {index}: duplicate instance/method={key}"); continue
        seen.add(key); gold = by_id.get(iid)
        if gold is None:
            aliases = sorted(canonical_to_raw_ids.get(canonical_instance_id(iid), set()))
            if aliases:
                errors.append(f"prediction row {index}: instance_id must exactly match dataset ID; alias {iid!r} canonicalizes to {aliases}")
            else:
                errors.append(f"prediction row {index}: unknown instance_id={iid}")
            continue
        gold_split = str(gold["split"]).lower()
        if gold_split not in EVAL_SPLITS:
            errors.append(f"prediction row {index}: prediction supplied for non-evaluation split={gold_split!r} instance={iid}")
            continue
        if not _action_is_valid(pred.get("pred_action"), gold.get("valid_action_mask", gold.get("valid"))): errors.append(f"prediction row {index}: pred_action is outside the instance valid-action schema")
        fp = str(pred["instance_fingerprint"])
        if fp != instance_fingerprint(gold): errors.append(f"prediction row {index}: instance snapshot mismatch for {iid}/{method}")
        snapshots[iid].add(fp); method_ids[method].add(iid)
        item = {"prospective": float(pred["pred_state_after"] == gold["gold_state_after"]), "action": float(pred["pred_action"] == gold["gold_action"])}
        if "pred_inverse" in pred:
            pred_inverse_ids[method].add(iid)
        if "gold_inverse" in gold and "pred_inverse" in pred:
            item["inverse"] = float(pred["pred_inverse"] == gold["gold_inverse"])
        cell = _cell_key(gold)
        grouped[(method, *cell)].append(item); outcomes[method][iid] = item
    for iid, fps in snapshots.items():
        if len(fps) != 1: errors.append(f"instance {iid}: methods used different input snapshots")
    required, coverage = REQUIRED_METHODS, {}
    unexpected = set(method_ids) - required
    if unexpected: errors.append(f"unexpected prediction methods: {sorted(unexpected)}")
    for method in sorted(required | set(method_ids)):
        ids = method_ids.get(method, set()); missing, extra = eval_ids - ids, ids - eval_ids
        coverage[method] = {"expected": len(eval_ids), "predicted": len(ids & eval_ids), "coverage": len(ids & eval_ids) / max(1, len(eval_ids)), "missing": len(missing), "extra": len(extra), "missing_examples": sorted(missing)[:5]}
        if missing: errors.append(f"method {method}: incomplete prediction coverage")
        if extra: errors.append(f"method {method}: predictions outside evaluation set")
    absent = required - set(method_ids)
    if absent: errors.append(f"missing required methods: {sorted(absent)}")
    inverse_metric_complete = False
    if gold_inverse_ids and gold_inverse_ids != eval_ids:
        errors.append(f"gold_inverse must cover all evaluation instances or none; found {len(gold_inverse_ids)}/{len(eval_ids)}")
    elif not gold_inverse_ids:
        leaking_methods = sorted(method for method, ids in pred_inverse_ids.items() if ids)
        if leaking_methods:
            errors.append(f"pred_inverse supplied without any evaluation gold_inverse by methods {leaking_methods}")
    else:
        inverse_metric_complete = True
        for method in sorted(required):
            ids = pred_inverse_ids.get(method, set())
            missing_inverse, extra_inverse = eval_ids - ids, ids - eval_ids
            if missing_inverse:
                inverse_metric_complete = False
                errors.append(f"method {method}: incomplete pred_inverse coverage ({len(missing_inverse)} missing)")
            if extra_inverse:
                inverse_metric_complete = False
                errors.append(f"method {method}: pred_inverse outside evaluation set ({len(extra_inverse)} extra)")
    shuffle_errors, shuffle_audit = _validate_shuffle_assignments(preds, by_id, eval_ids); errors.extend(shuffle_errors)
    reportable_metrics = {"prospective", "action"} | ({"inverse"} if inverse_metric_complete else set())
    cells = []
    for (method, seed, domain, split, condition), items in sorted(grouped.items()):
        cell = {"method": method, "seed": seed, "domain": domain, "split": split, "condition": condition, "n": len(items)}
        for metric in sorted({k for item in items for k in item} & reportable_metrics):
            cell[metric] = statistics.mean(item[metric] for item in items)
        cells.append(cell)
    metrics = sorted(reportable_metrics); summary, methods = defaultdict(dict), set(method_ids)
    for method in methods:
        method_cells = [c for c in cells if c["method"] == method]
        for metric in metrics:
            vals = [float(c[metric]) for c in method_cells if metric in c]
            if vals:
                mean, low, high = _mean_ci(vals); summary[method].update({metric: mean, f"{metric}_cell_ci95_low": low, f"{metric}_cell_ci95_high": high})
    correct_cells = {(c["seed"], c["domain"], c["split"], c["condition"]): c for c in cells if c["method"] == "correct"}; gaps = {}
    for control in sorted(methods - {"correct"}):
        control_cells = {(c["seed"], c["domain"], c["split"], c["condition"]): c for c in cells if c["method"] == control}; gaps[control] = {}; shared = sorted(eval_ids & method_ids.get("correct", set()) & method_ids.get(control, set()))
        for metric in metrics:
            diffs = [float(correct_cells[k][metric]) - float(control_cells[k][metric]) for k in sorted(correct_cells.keys() & control_cells.keys()) if metric in correct_cells[k] and metric in control_cells[k]]
            if not diffs: continue
            groups = defaultdict(list); a = b = ties = 0
            for iid in shared:
                left, right = outcomes["correct"][iid].get(metric), outcomes[control][iid].get(metric)
                if left is None or right is None: continue
                groups[_cell_key(by_id[iid])].append(float(left - right))
                if left > right: a += 1
                elif right > left: b += 1
                else: ties += 1
            values = [v for vs in groups.values() for v in vs]; boot_low, boot_high = _cluster_bootstrap_ci(groups) if values else (math.nan, math.nan); mean, low, high = _mean_ci(diffs)
            gaps[control][metric] = {"paired_cells": len(diffs), "mean_gap": mean, "min_cell_gap": min(diffs), "max_cell_gap": max(diffs), "positive_cell_fraction": sum(v > 0 for v in diffs) / len(diffs), "ci95_low": low, "ci95_high": high, "paired_randomization_p_two_sided": _paired_p(diffs), "paired_instances": len(values), "instance_mean_gap": statistics.mean(values) if values else math.nan, "instance_cluster_bootstrap_ci95_low": boot_low, "instance_cluster_bootstrap_ci95_high": boot_high, "correct_only_instances": a, "control_only_instances": b, "tied_instances": ties, "mcnemar_exact_p_two_sided": _mcnemar_exact(a, b), "passes_mean_gap_0_10": mean >= .10, "passes_every_cell_positive": min(diffs) > 0, "passes_ci_excludes_zero": low > 0, "passes_instance_cluster_ci_excludes_zero": boot_low > 0 if not math.isnan(boot_low) else False}
    if errors:
        cells = []
        summary = defaultdict(dict)
        gaps = {}
    return {"valid": not errors, "errors": errors, "classification": "qualified" if not errors else "initial_reproduction_failure", "dataset_contract_binding": True, "dataset_contract_valid": bool(dataset_audit.get("valid", False)), "dataset_contract_errors": list(dataset_audit.get("errors", [])), "invalid_dataset_statistics_forbidden": True, "invalid_score_statistics_forbidden": True, "statistics_emitted": not errors, "prediction_rows": len(preds), "expected_eval_instances": len(eval_ids), "coverage": coverage, "same_instance_snapshot": not any("snapshot" in e for e in errors), "fingerprints_required": True, "prediction_payload_findings": payload_findings, "prediction_schema_alias_findings": alias_findings, "strict_prediction_schema": True, "forbidden_prediction_fields": sorted(FORBIDDEN_PREDICTION_FIELDS), "alias_normalized_prediction_leakage_required": True, "finite_prediction_values_checked": True, "valid_action_schema_checked": True, "optional_metric_coverage_required": True, "inverse_metric_complete": inverse_metric_complete, "gold_inverse_coverage": {"expected": len(eval_ids), "present": len(gold_inverse_ids)}, "pred_inverse_coverage": {method: {"expected": len(eval_ids), "present": len(pred_inverse_ids.get(method, set()))} for method in sorted(REQUIRED_METHODS)}, "shuffle_assignment_audit": shuffle_audit, "cells": cells, "summary": dict(summary), "paired_gaps_vs_correct": gaps, "progress_contract": {"required_mean_gap": .10, "requires_all_three_seeds": True, "requires_same_instance_snapshot": True, "requires_explicit_instance_fingerprint": True, "requires_complete_prediction_coverage": True, "requires_shuffle_provenance": True, "requires_shuffle_donor_value_binding": True, "requires_within_cell_derangement": True, "requires_split_condition_cells": True, "requires_ci_excludes_zero": True, "requires_instance_cluster_ci_excludes_zero": True, "internal_metrics_do_not_count": True}, "allowed_train_splits": sorted(TRAIN_SPLITS), "allowed_evaluation_splits": sorted(EVAL_SPLITS), "split_scope_fail_closed": True, "canonical_instance_identity_required": True, "exact_prediction_instance_id_required": True, "instance_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters"}


RAW_LOG_MEASUREMENT_FIELDS = (
    "method", "seed", "domain", "split", "condition", "code_commit",
    "model_bytes", "peak_rss_bytes", "training_wall_seconds",
    "cpu_inference_ms_per_item", "model_sha256", "data_sha256",
)


def _iter_raw_log_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_raw_log_objects(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_raw_log_objects(nested)


def _read_raw_log_objects(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    objects: list[dict[str, Any]] = []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                parsed_line = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: raw log must be JSON, JSONL, or nested JSON: {exc}"
                ) from exc
            objects.extend(obj for obj in _iter_raw_log_objects(parsed_line) if isinstance(obj, dict))
    else:
        objects.extend(obj for obj in _iter_raw_log_objects(parsed) if isinstance(obj, dict))
    return objects


def _raw_log_cell(row: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(row["method"]),
        int(row["seed"]),
        str(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        str(row["condition"]),
    )


def _is_raw_log_measurement(row: dict[str, Any]) -> bool:
    kind = str(row.get("record_type", row.get("event", row.get("type", "")))).casefold()
    return kind in {"r0_measurement", "resource_measurement", "measurement"} and all(
        field in row for field in RAW_LOG_MEASUREMENT_FIELDS
    )


def _audit_run_raw_log_binding(
    run: dict[str, Any], index: int, base_dir: Path, cache: dict[Path, list[dict[str, Any]]]
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    finding: dict[str, Any] = {"run": index, "matching_measurement_records": 0}
    raw_path, path_error = _resolve_contained_artifact(base_dir, run.get("raw_log_path", ""))
    if path_error is not None:
        errors.append(f"run {index}: raw_log_path {path_error}")
        return errors, finding
    assert raw_path is not None
    finding["raw_log_path"] = str(raw_path.relative_to(base_dir.resolve()))
    try:
        records = cache.setdefault(raw_path, _read_raw_log_objects(raw_path))
        cell = _raw_log_cell(run)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"run {index}: invalid raw-log measurement schema: {exc}")
        return errors, finding
    finding["cell"] = list(cell)
    matches: list[dict[str, Any]] = []
    for record in records:
        if not _is_raw_log_measurement(record):
            continue
        try:
            if _raw_log_cell(record) == cell:
                matches.append(record)
        except (KeyError, TypeError, ValueError):
            continue
    finding["matching_measurement_records"] = len(matches)
    if len(matches) != 1:
        errors.append(
            f"run {index}: expected exactly one raw-log measurement record for cell {cell}, found {len(matches)}"
        )
        return errors, finding
    record = matches[0]
    for field in RAW_LOG_MEASUREMENT_FIELDS:
        expected, observed = run.get(field), record.get(field)
        if field == "split":
            expected = unicodedata.normalize("NFKC", str(expected)).casefold()
            observed = unicodedata.normalize("NFKC", str(observed)).casefold()
        elif field == "seed":
            try:
                expected, observed = int(expected), int(observed)
            except (TypeError, ValueError):
                errors.append(f"run {index}: seed is not integer-like in manifest or raw log")
                continue
        elif field in {"model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"}:
            if not _finite_positive(expected) or not _finite_positive(observed):
                errors.append(f"run {index}: raw-log {field} must be finite and positive")
                continue
            expected, observed = float(expected), float(observed)
        if observed != expected:
            errors.append(f"run {index}: raw-log {field} mismatch: manifest={expected!r}, log={observed!r}")
    return errors, finding

def audit_artifacts(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    errors, checks, raw_log_findings = [], [], []; raw_log_cache: dict[Path, list[dict[str, Any]]] = {}; runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs: return {"valid": False, "errors": ["manifest.runs must be a non-empty list"], "checks": [], "classification": "initial_reproduction_failure"}
    methods, cells, seeds, domains, topology, commits = set(), set(), set(), set(), set(), set(); identity = defaultdict(set)
    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict): errors.append(f"run {index}: must be an object"); continue
        missing = RESOURCE_FIELDS - run.keys()
        if missing: errors.append(f"run {index}: missing resource/provenance fields {sorted(missing)}")
        try:
            method = str(run["method"])
            seed = int(run["seed"])
            domain = str(run["domain"])
            split = unicodedata.normalize("NFKC", str(run["split"])).casefold()
            condition = str(run["condition"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"run {index}: invalid indexing field {exc}")
            continue
        if not domain: errors.append(f"run {index}: domain must be non-empty")
        if not split:
            errors.append(f"run {index}: split must be non-empty")
        elif split not in EVAL_SPLITS:
            errors.append(f"run {index}: artifact split={split!r} is not a registered evaluation split; allowed={sorted(EVAL_SPLITS)}")
        if not condition: errors.append(f"run {index}: condition must be non-empty")
        cell = (method, seed, domain, split, condition)
        if cell in cells: errors.append(f"run {index}: duplicate run cell {cell}")
        cells.add(cell); methods.add(method); seeds.add(seed); domains.add(domain); topology.add((domain, split, condition)); commits.add(str(run.get("code_commit", ""))); identity[(seed, domain, split, condition)].add((str(run.get("data_path", "")), str(run.get("data_sha256", ""))))
        for key in ("model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"):
            if not _finite_positive(run.get(key)): errors.append(f"run {index}: {key} must be a finite positive number")
        if not _is_hex(run.get("code_commit"), 40): errors.append(f"run {index}: code_commit must be a full 40-hex commit SHA")
        for path_key, hash_key in ARTIFACT_FIELDS:
            rel, expected = run.get(path_key), run.get(hash_key)
            if not rel: errors.append(f"run {index}: {path_key} is required for independent checksum verification"); continue
            if not _is_hex(expected, 64): errors.append(f"run {index}: {hash_key} must be a full 64-hex SHA-256"); continue
            path, containment_error = _resolve_contained_artifact(base_dir, rel)
            if containment_error is not None:
                errors.append(f"run {index}: {path_key} {containment_error}")
                continue
            assert path is not None
            actual = file_sha256(path); ok = actual == str(expected).lower(); checks.append({"run": index, "path": str(path.relative_to(base_dir.resolve())), "expected": expected, "actual": actual, "ok": ok, "size_bytes": path.stat().st_size, "contained": True})
            if not ok: errors.append(f"run {index}: checksum mismatch for {path_key}")
            if path_key == "model_path" and _finite_positive(run.get("model_bytes")) and int(run["model_bytes"]) != path.stat().st_size: errors.append(f"run {index}: model_bytes does not match model artifact size")
        binding_errors, binding_finding = _audit_run_raw_log_binding(run, index, base_dir, raw_log_cache)
        errors.extend(binding_errors); raw_log_findings.append(binding_finding)
    required = REQUIRED_METHODS; missing_methods, unexpected_methods = required - methods, methods - required
    if missing_methods: errors.append(f"manifest missing required methods {sorted(missing_methods)}")
    if unexpected_methods: errors.append(f"manifest contains unexpected methods {sorted(unexpected_methods)}")
    if len(commits) != 1: errors.append(f"manifest must use exactly one code_commit, found {sorted(commits)}")
    for cell_key, values in sorted(identity.items()):
        if len(values) != 1: errors.append(f"manifest cell {cell_key}: methods must share one data_path/data_sha256, found {sorted(values)}")
    if seeds != CANONICAL_SEEDS: errors.append(f"manifest seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
    expected = {(m, s, d, sp, c) for m in required for s in CANONICAL_SEEDS for d, sp, c in topology}; missing_cells = expected - cells
    if missing_cells: errors.append(f"manifest incomplete observed-topology coverage: {len(missing_cells)} missing cells")
    return {"valid": not errors, "errors": errors, "warnings": [], "checks": checks, "methods": sorted(methods), "seeds": sorted(seeds), "domains": sorted(domains), "observed_topology": [list(v) for v in sorted(topology)], "runs": len(runs), "missing_run_cells": len(missing_cells), "missing_run_cell_examples": [list(v) for v in sorted(missing_cells)[:10]], "independent_artifacts_required": True, "positive_resource_measurements_required": True, "artifact_path_containment_required": True, "nonempty_artifacts_required": True, "condition_index_required": True, "exact_method_topology_required": True, "single_commit_required": True, "same_dataset_per_cell_required": True, "canonical_seeds": sorted(CANONICAL_SEEDS), "allowed_evaluation_splits": sorted(EVAL_SPLITS), "artifact_split_scope_fail_closed": True, "raw_log_measurement_findings": raw_log_findings, "raw_log_measurement_binding_required": True, "exactly_one_measurement_record_per_run_required": True, "raw_log_bound_fields": list(RAW_LOG_MEASUREMENT_FIELDS), "classification": "reproduced" if not errors else "initial_reproduction_failure"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate"); v.add_argument("data", type=Path)
    s = sub.add_parser("score"); s.add_argument("data", type=Path); s.add_argument("predictions", type=Path)
    a = sub.add_parser("audit-artifacts"); a.add_argument("manifest", type=Path); a.add_argument("--base-dir", type=Path, default=Path("."))
    args = p.parse_args(argv)
    try:
        if args.command == "audit-artifacts": result = audit_artifacts(read_json(args.manifest), args.base_dir)
        else:
            data = read_jsonl(args.data); result = validate_dataset(data)
            if args.command == "score": result["scores"] = score(data, read_jsonl(args.predictions)); result["valid"] = result["valid"] and result["scores"]["valid"]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2)); return 2
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
