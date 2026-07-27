#!/usr/bin/env python3
"""Apply R0-D Cycle 073 normalized domain/condition cell identity hardening."""
from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    marker = "normalized_cell_identity_required"
    if marker in text:
        print("Cycle 073 already applied")
        return

    old = '''def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (int(row["seed"]), str(row["domain"]), str(row["split"]).lower(), str(row["condition"]))
'''
    new = '''def canonical_domain_label(value: Any) -> str:
    """Canonical domain identity for topology, statistics, and artifact cells."""
    return canonical_text(value)


def canonical_condition_label(value: Any) -> str:
    """Canonicalize condition tokens independent of width, case, order, or delimiter."""
    raw = unicodedata.normalize("NFKC", str(value)).casefold()
    tokens = {canonical_text(token) for token in re.split(r"[+,|\\s]+", raw)}
    tokens.discard("")
    return "+".join(sorted(tokens))


def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(row["seed"]),
        canonical_domain_label(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        canonical_condition_label(row["condition"]),
    )
'''
    text = replace_once(text, old, new)

    old = '''def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    return stable_hash({k: row.get(k) for k in keys})
'''
    new = '''def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    payload = {k: row.get(k) for k in keys}
    payload["domain"] = canonical_domain_label(row.get("domain", ""))
    payload["condition"] = canonical_condition_label(row.get("condition", ""))
    payload["split"] = unicodedata.normalize("NFKC", str(row.get("split", ""))).casefold()
    return stable_hash(payload)
'''
    text = replace_once(text, old, new)

    old = '''    topology, per_seed_splits = defaultdict(set), defaultdict(set)
    per_domain_seed_splits = defaultdict(set)
'''
    new = '''    topology, per_seed_splits = defaultdict(set), defaultdict(set)
    per_domain_seed_splits = defaultdict(set)
    raw_domain_labels, raw_condition_labels = defaultdict(set), defaultdict(set)
'''
    text = replace_once(text, old, new)

    old = '''        domain, condition, split = str(row["domain"]), str(row["condition"]), str(row["split"]).lower()
        if not domain:
            errors.append(f"row {index}: domain must be non-empty")
'''
    new = '''        raw_domain, raw_condition = str(row["domain"]), str(row["condition"])
        domain, condition = canonical_domain_label(raw_domain), canonical_condition_label(raw_condition)
        split = unicodedata.normalize("NFKC", str(row["split"])).casefold()
        raw_domain_labels[domain].add(raw_domain)
        raw_condition_labels[condition].add(raw_condition)
        if not domain:
            errors.append(f"row {index}: domain must be non-empty after canonicalization")
'''
    text = replace_once(text, old, new)

    old = '''        if not condition:
            errors.append(f"row {index}: condition must be non-empty")
'''
    new = '''        if not condition:
            errors.append(f"row {index}: condition must be non-empty after canonicalization")
'''
    text = replace_once(text, old, new)

    old = '''    overlap = {}; train_text = set(texts.get("train", {}))
'''
    new = '''    domain_label_collisions = {key: sorted(values) for key, values in raw_domain_labels.items() if key and len(values) > 1}
    condition_label_collisions = {key: sorted(values) for key, values in raw_condition_labels.items() if key and len(values) > 1}
    for canonical, raw_values in sorted(domain_label_collisions.items()):
        errors.append(f"domain labels collide after canonicalization {canonical!r}: {raw_values}")
    for canonical, raw_values in sorted(condition_label_collisions.items()):
        errors.append(f"condition labels collide after canonicalization {canonical!r}: {raw_values}")
    overlap = {}; train_text = set(texts.get("train", {}))
'''
    text = replace_once(text, old, new)

    old = '''"alias_normalized_leakage_required": True, "allowed_train_splits": sorted(TRAIN_SPLITS)'''
    new = '''"alias_normalized_leakage_required": True, "normalized_cell_identity_required": True, "cell_identity_normalization": "domain=NFKC+casefold+remove whitespace/control-format; condition=normalized sorted unique tokens", "canonical_domain_labels": {key: sorted(values) for key, values in sorted(raw_domain_labels.items())}, "canonical_condition_labels": {key: sorted(values) for key, values in sorted(raw_condition_labels.items())}, "domain_label_collisions": domain_label_collisions, "condition_label_collisions": condition_label_collisions, "allowed_train_splits": sorted(TRAIN_SPLITS)'''
    text = replace_once(text, old, new)

    old = '''        grouped[(method, int(gold["seed"]), str(gold["domain"]), str(gold["split"]).lower(), str(gold["condition"]))].append(item); outcomes[method][iid] = item
'''
    new = '''        seed, domain, split, condition = _cell_key(gold)
        grouped[(method, seed, domain, split, condition)].append(item); outcomes[method][iid] = item
'''
    text = replace_once(text, old, new)

    old = '''        str(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        str(row["condition"]),
'''
    new = '''        canonical_domain_label(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        canonical_condition_label(row["condition"]),
'''
    text = replace_once(text, old, new)

    old = '''            domain = str(run["domain"])
            split = unicodedata.normalize("NFKC", str(run["split"])).casefold()
            condition = str(run["condition"])
'''
    new = '''            domain = canonical_domain_label(run["domain"])
            split = unicodedata.normalize("NFKC", str(run["split"])).casefold()
            condition = canonical_condition_label(run["condition"])
'''
    text = replace_once(text, old, new)

    old = '''"raw_log_bound_fields": list(RAW_LOG_MEASUREMENT_FIELDS), "classification": "reproduced" if not errors else "initial_reproduction_failure"}'''
    new = '''"raw_log_bound_fields": list(RAW_LOG_MEASUREMENT_FIELDS), "normalized_cell_identity_required": True, "cell_identity_normalization": "domain=NFKC+casefold+remove whitespace/control-format; condition=normalized sorted unique tokens", "classification": "reproduced" if not errors else "initial_reproduction_failure"}'''
    text = replace_once(text, old, new)

    TARGET.write_text(text, encoding="utf-8")
    print(f"Applied Cycle 073 to {TARGET}")


if __name__ == "__main__":
    main()
