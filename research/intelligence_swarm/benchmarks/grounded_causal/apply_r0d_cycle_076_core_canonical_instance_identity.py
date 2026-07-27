#!/usr/bin/env python3
"""Apply Cycle 076 canonical instance identity hardening to evaluation_contract.py."""
from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")
text = TARGET.read_text(encoding="utf-8")

needle = '''def canonical_condition(value: Any) -> str:
    """Canonical order-independent condition token set."""
    raw = unicodedata.normalize("NFKC", str(value)).casefold()
    parts = {
        canonical_text(part)
        for part in re.split(r"[+,|\\s]+", raw)
        if canonical_text(part)
    }
    return "+".join(sorted(parts))
'''
replacement = needle + '''\n\ndef canonical_instance_id(value: Any) -> str:
    """Canonical instance identity used only for collision/alias detection."""
    return canonical_text(value)
'''
if "def canonical_instance_id(" not in text:
    if needle not in text:
        raise SystemExit("canonical_condition anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''    raw_domains_by_canonical, raw_conditions_by_canonical = defaultdict(set), defaultdict(set)
'''
replacement = '''    raw_domains_by_canonical, raw_conditions_by_canonical = defaultdict(set), defaultdict(set)
    raw_instance_ids_by_canonical = defaultdict(set)
'''
if "raw_instance_ids_by_canonical" not in text:
    if needle not in text:
        raise SystemExit("dataset identity-map anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''        iid = str(row["instance_id"])
        if iid in seen:
            errors.append(f"row {index}: duplicate instance_id={iid}")
        seen.add(iid)
        fingerprints[iid] = instance_fingerprint(row)
'''
replacement = '''        iid = str(row["instance_id"])
        canonical_iid = canonical_instance_id(iid)
        if not canonical_iid:
            errors.append(f"row {index}: instance_id must be non-empty after canonicalization")
        raw_instance_ids_by_canonical[canonical_iid].add(iid)
        if canonical_iid in seen:
            errors.append(f"row {index}: duplicate canonical instance_id={canonical_iid!r} raw={iid!r}")
        seen.add(canonical_iid)
        fingerprints[canonical_iid] = instance_fingerprint(row)
'''
if "duplicate canonical instance_id" not in text:
    if needle not in text:
        raise SystemExit("dataset instance-id anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if len(values) > 1}
    condition_collisions = {key: sorted(values) for key, values in raw_conditions_by_canonical.items() if len(values) > 1}
'''
replacement = '''    instance_id_collisions = {key: sorted(values) for key, values in raw_instance_ids_by_canonical.items() if len(values) > 1}
    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if len(values) > 1}
    condition_collisions = {key: sorted(values) for key, values in raw_conditions_by_canonical.items() if len(values) > 1}
    if instance_id_collisions:
        errors.append(f"instance_id values collide after canonicalization: {instance_id_collisions}")
'''
if "instance_id_collisions =" not in text:
    if needle not in text:
        raise SystemExit("collision anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''"domain_label_collisions": domain_collisions, "condition_label_collisions": condition_collisions}
'''
replacement = '''"domain_label_collisions": domain_collisions, "condition_label_collisions": condition_collisions, "canonical_instance_identity_required": True, "instance_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters", "instance_id_collisions": instance_id_collisions}
'''
if '"canonical_instance_identity_required": True' not in text:
    if needle not in text:
        raise SystemExit("dataset report anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''    by_id = {str(r["instance_id"]): r for r in adapted}
'''
replacement = '''    by_id = {str(r["instance_id"]): r for r in adapted}
    canonical_dataset_ids = defaultdict(set)
    for raw_iid in by_id:
        canonical_dataset_ids[canonical_instance_id(raw_iid)].add(raw_iid)
'''
if "canonical_dataset_ids =" not in text:
    if needle not in text:
        raise SystemExit("score dataset-id anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''        iid, method = str(pred["instance_id"]), str(pred["method"]); key = (iid, method)
'''
replacement = '''        iid, method = str(pred["instance_id"]), str(pred["method"]); canonical_iid = canonical_instance_id(iid); key = (canonical_iid, method)
        if not canonical_iid:
            errors.append(f"prediction row {index}: instance_id must be non-empty after canonicalization")
            continue
        canonical_matches = canonical_dataset_ids.get(canonical_iid, set())
        if iid not in by_id and canonical_matches:
            errors.append(f"prediction row {index}: non-exact instance_id alias {iid!r} resolves to dataset id(s) {sorted(canonical_matches)}")
            continue
'''
if "non-exact instance_id alias" not in text:
    if needle not in text:
        raise SystemExit("prediction id anchor not found")
    text = text.replace(needle, replacement, 1)

needle = '''"strict_prediction_schema": True, "forbidden_prediction_fields": sorted(FORBIDDEN_PREDICTION_FIELDS),
'''
replacement = '''"strict_prediction_schema": True, "canonical_instance_identity_required": True, "exact_prediction_instance_id_required": True, "instance_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters", "forbidden_prediction_fields": sorted(FORBIDDEN_PREDICTION_FIELDS),
'''
if '"exact_prediction_instance_id_required": True' not in text:
    if needle not in text:
        raise SystemExit("score report anchor not found")
    text = text.replace(needle, replacement, 1)

TARGET.write_text(text, encoding="utf-8")
print(f"patched {TARGET}")
