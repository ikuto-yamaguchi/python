#!/usr/bin/env python3
"""Apply the fail-closed normalized domain/condition cell identity patch.

The patch is deliberately exact and idempotent: it refuses to modify an
unexpected core file instead of silently producing a partial audit contract.
"""
from pathlib import Path

CORE = Path(__file__).with_name("evaluation_contract.py")
text = CORE.read_text(encoding="utf-8")

helper_anchor = '''def _split_sig(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        if row.get(key) is not None:
            return stable_hash(canonical_holdout_identity(row[key]))
    return None


def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (int(row["seed"]), str(row["domain"]), str(row["split"]).lower(), str(row["condition"]))
'''
helper_replacement = '''def _split_sig(row: dict[str, Any], *keys: str) -> str | None:
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
        for part in re.split(r"[+,|\\s]+", raw)
        if canonical_text(part)
    }
    return "+".join(sorted(parts))


def _cell_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(row["seed"]),
        canonical_domain(row["domain"]),
        str(row["split"]).lower(),
        canonical_condition(row["condition"]),
    )
'''
if "def canonical_domain(value: Any)" not in text:
    if helper_anchor not in text:
        raise SystemExit("unexpected core: _cell_key anchor not found")
    text = text.replace(helper_anchor, helper_replacement, 1)

fp_anchor = '''def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    return stable_hash({k: row.get(k) for k in keys})
'''
fp_replacement = '''def instance_fingerprint(row: dict[str, Any]) -> str:
    keys = ("domain", "seed", "split", "condition", "utterance", "state_before", "history", "valid_action_mask", "entity_id", "entity_signature", "dynamics_id", "dynamics_signature", "episode_id", "episode_seed", "observation_fingerprint")
    payload = {k: row.get(k) for k in keys}
    payload["domain"] = canonical_domain(row.get("domain", ""))
    payload["condition"] = canonical_condition(row.get("condition", ""))
    payload["split"] = str(row.get("split", "")).lower()
    return stable_hash(payload)
'''
if 'payload["domain"] = canonical_domain' not in text:
    if fp_anchor not in text:
        raise SystemExit("unexpected core: instance_fingerprint anchor not found")
    text = text.replace(fp_anchor, fp_replacement, 1)

validate_anchor = '''    alias_findings = []
    explicit_holdout_findings = []
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
    per_domain_seed_splits = defaultdict(set)
'''
validate_replacement = '''    alias_findings = []
    explicit_holdout_findings = []
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
    per_domain_seed_splits = defaultdict(set)
    raw_domains_by_canonical, raw_conditions_by_canonical = defaultdict(set), defaultdict(set)
'''
if "raw_domains_by_canonical" not in text:
    if validate_anchor not in text:
        raise SystemExit("unexpected core: validate state anchor not found")
    text = text.replace(validate_anchor, validate_replacement, 1)

row_anchor = '''        domain, condition, split = str(row["domain"]), str(row["condition"]), str(row["split"]).lower()
        if not domain:
            errors.append(f"row {index}: domain must be non-empty")
'''
row_replacement = '''        raw_domain, raw_condition = str(row["domain"]), str(row["condition"])
        domain, condition, split = canonical_domain(raw_domain), canonical_condition(raw_condition), str(row["split"]).lower()
        raw_domains_by_canonical[domain].add(raw_domain)
        raw_conditions_by_canonical[condition].add(raw_condition)
        if not domain:
            errors.append(f"row {index}: domain must be non-empty after canonicalization")
'''
if "raw_domain, raw_condition" not in text:
    if row_anchor not in text:
        raise SystemExit("unexpected core: validate row anchor not found")
    text = text.replace(row_anchor, row_replacement, 1)

collision_anchor = '''    overlap = {}; train_text = set(texts.get("train", {}))
'''
collision_replacement = '''    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if len(values) > 1}
    condition_collisions = {key: sorted(values) for key, values in raw_conditions_by_canonical.items() if len(values) > 1}
    if domain_collisions:
        errors.append(f"domain labels collide after canonicalization: {domain_collisions}")
    if condition_collisions:
        errors.append(f"condition labels collide after canonicalization: {condition_collisions}")
    overlap = {}; train_text = set(texts.get("train", {}))
'''
if "domain_collisions =" not in text:
    if collision_anchor not in text:
        raise SystemExit("unexpected core: collision anchor not found")
    text = text.replace(collision_anchor, collision_replacement, 1)

group_anchor = '''        grouped[(method, int(gold["seed"]), str(gold["domain"]), str(gold["split"]).lower(), str(gold["condition"]))].append(item); outcomes[method][iid] = item
'''
group_replacement = '''        cell = _cell_key(gold)
        grouped[(method, *cell)].append(item); outcomes[method][iid] = item
'''
if "grouped[(method, *cell)]" not in text:
    if group_anchor not in text:
        raise SystemExit("unexpected core: score grouping anchor not found")
    text = text.replace(group_anchor, group_replacement, 1)

return_marker = '"split_scope_fail_closed": True}'
return_replacement = '"split_scope_fail_closed": True, "normalized_cell_identity_required": True, "cell_identity_normalization": "domain=NFKC+casefold+remove whitespace/control-format; condition=canonical sorted token set", "domain_label_collisions": domain_collisions, "condition_label_collisions": condition_collisions}'
if '"normalized_cell_identity_required": True' not in text:
    if return_marker not in text:
        raise SystemExit("unexpected core: validate return marker not found")
    text = text.replace(return_marker, return_replacement, 1)

CORE.write_text(text, encoding="utf-8")
print("cycle 074 normalized cell identity patch applied")
