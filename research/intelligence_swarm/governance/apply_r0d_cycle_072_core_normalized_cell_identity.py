#!/usr/bin/env python3
"""Apply the Cycle 072 normalized domain/condition cell identity hardening.

The patch is deliberately fail-closed and idempotent: it only rewrites the
known Cycle 071 core shape and refuses an unexpected source layout.
"""
from __future__ import annotations

from pathlib import Path

TARGET = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one source fragment, found {count}: {old[:80]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    marker = 'normalized_cell_identity_required": True'
    if marker in text:
        print("Cycle 072 core patch already applied")
        return

    text = replace_once(
        text,
        '''def _condition_parts(row: dict[str, Any]) -> set[str]:
    raw = unicodedata.normalize("NFKC", str(row.get("condition", ""))).casefold()
    return {part for part in re.split(r"[+,|\\s]+", raw) if part}
''',
        '''def canonical_domain_label(value: Any) -> str:
    """Canonical domain identity used by topology, statistics and controls."""
    return canonical_text(value)


def canonical_condition_label(value: Any) -> str:
    """Canonicalize a condition as an order-independent token set."""
    raw = unicodedata.normalize("NFKC", str(value)).casefold()
    parts = {canonical_text(part) for part in re.split(r"[+,|\\s]+", raw)}
    parts.discard("")
    return "+".join(sorted(parts))


def _condition_parts(row: dict[str, Any]) -> set[str]:
    canonical = canonical_condition_label(row.get("condition", ""))
    return set(canonical.split("+")) if canonical else set()
''',
    )

    text = replace_once(
        text,
        '''def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (int(row["seed"]), str(row["domain"]), str(row["split"]).lower(), str(row["condition"]))
''',
        '''def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(row["seed"]),
        canonical_domain_label(row["domain"]),
        str(row["split"]).lower(),
        canonical_condition_label(row["condition"]),
    )
''',
    )

    text = replace_once(
        text,
        '''def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    return stable_hash({k: row.get(k) for k in keys})
''',
        '''def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    payload = {k: row.get(k) for k in keys}
    payload["domain"] = canonical_domain_label(row.get("domain"))
    payload["condition"] = canonical_condition_label(row.get("condition"))
    return stable_hash(payload)
''',
    )

    text = replace_once(
        text,
        '''    alias_findings = []
    explicit_holdout_findings = []
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
''',
        '''    alias_findings = []
    explicit_holdout_findings = []
    raw_domain_labels, raw_condition_labels = defaultdict(set), defaultdict(set)
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
''',
    )

    text = replace_once(
        text,
        '''        domain, condition, split = str(row["domain"]), str(row["condition"]), str(row["split"]).lower()
        if not domain:
            errors.append(f"row {index}: domain must be non-empty")
''',
        '''        raw_domain, raw_condition = str(row["domain"]), str(row["condition"])
        domain = canonical_domain_label(raw_domain)
        condition = canonical_condition_label(raw_condition)
        split = str(row["split"]).lower()
        raw_domain_labels[domain].add(raw_domain)
        raw_condition_labels[condition].add(raw_condition)
        if not domain:
            errors.append(f"row {index}: domain must be non-empty after canonical normalization")
''',
    )

    text = replace_once(
        text,
        '''    overlap = {}; train_text = set(texts.get("train", {}))
''',
        '''    for canonical, raw_labels in sorted(raw_domain_labels.items()):
        if canonical and len(raw_labels) > 1:
            errors.append(f"domain label normalization collision for {canonical!r}: {sorted(raw_labels)!r}")
    for canonical, raw_labels in sorted(raw_condition_labels.items()):
        if canonical and len(raw_labels) > 1:
            errors.append(f"condition label normalization collision for {canonical!r}: {sorted(raw_labels)!r}")
    overlap = {}; train_text = set(texts.get("train", {}))
''',
    )

    old_return = '"split_scope_fail_closed": True}'
    new_return = '"split_scope_fail_closed": True, "normalized_cell_identity_required": True, "cell_identity_normalization": "domain=NFKC+casefold+remove whitespace/control-format; condition=same plus sorted unique token set", "canonical_domain_labels": {k: sorted(v) for k, v in sorted(raw_domain_labels.items())}, "canonical_condition_labels": {k: sorted(v) for k, v in sorted(raw_condition_labels.items())}}'
    text = replace_once(text, old_return, new_return)

    TARGET.write_text(text, encoding="utf-8")
    print("Applied Cycle 072 normalized cell identity core patch")


if __name__ == "__main__":
    main()
