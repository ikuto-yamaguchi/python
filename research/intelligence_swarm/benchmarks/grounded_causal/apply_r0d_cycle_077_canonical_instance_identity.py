#!/usr/bin/env python3
"""Apply Cycle 077 canonical instance identity hardening to evaluation_contract.py."""
from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")
text = TARGET.read_text(encoding="utf-8")

anchor = '''def canonical_condition(value: Any) -> str:
    """Canonical order-independent condition token set."""
    raw = unicodedata.normalize("NFKC", str(value)).casefold()
    parts = {
        canonical_text(part)
        for part in re.split(r"[+,|\\s]+", raw)
        if canonical_text(part)
    }
    return "+".join(sorted(parts))
'''
replacement = anchor + '''\n\ndef canonical_instance_id(value: Any) -> str:
    """Canonical identity used only to detect aliases; raw IDs remain binding keys."""
    return canonical_text(value)
'''
if "def canonical_instance_id(" not in text:
    if anchor not in text:
        raise SystemExit("canonical_condition anchor not found")
    text = text.replace(anchor, replacement, 1)

old = '''    seen, domains, seeds, conditions = set(), set(), set(), set()
'''
new = '''    seen, canonical_instance_ids, domains, seeds, conditions = set(), defaultdict(set), set(), set(), set()
'''
if old in text:
    text = text.replace(old, new, 1)
elif "canonical_instance_ids" not in text:
    raise SystemExit("validate_dataset state anchor not found")

old = '''        iid = str(row["instance_id"])
        if iid in seen:
            errors.append(f"row {index}: duplicate instance_id={iid}")
        seen.add(iid)
        fingerprints[iid] = instance_fingerprint(row)
'''
new = '''        iid = str(row["instance_id"])
        canonical_iid = canonical_instance_id(iid)
        if not canonical_iid:
            errors.append(f"row {index}: instance_id must be non-empty after canonicalization")
        if iid in seen:
            errors.append(f"row {index}: duplicate instance_id={iid}")
        seen.add(iid)
        canonical_instance_ids[canonical_iid].add(iid)
        fingerprints[iid] = instance_fingerprint(row)
'''
if old in text:
    text = text.replace(old, new, 1)
elif "canonical_iid = canonical_instance_id(iid)" not in text:
    raise SystemExit("dataset instance anchor not found")

old = '''    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if len(values) > 1}
'''
new = '''    instance_id_collisions = {key: sorted(values) for key, values in canonical_instance_ids.items() if key and len(values) > 1}
    if instance_id_collisions:
        errors.append(f"instance_id aliases collide after canonicalization: {instance_id_collisions}")
    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if len(values) > 1}
'''
if old in text:
    text = text.replace(old, new, 1)
elif "instance_id_collisions =" not in text:
    raise SystemExit("collision anchor not found")

old = '''"domain_label_collisions": domain_collisions, "condition_label_collisions": condition_collisions}
'''
new = '''"domain_label_collisions": domain_collisions, "condition_label_collisions": condition_collisions, "canonical_instance_identity_required": True, "exact_prediction_instance_id_required": True, "instance_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters", "instance_id_collisions": instance_id_collisions}
'''
if old in text:
    text = text.replace(old, new, 1)
elif '"canonical_instance_identity_required": True' not in text:
    raise SystemExit("dataset audit return anchor not found")

old = '''    by_id = {str(r["instance_id"]): r for r in adapted}
'''
new = '''    by_id = {str(r["instance_id"]): r for r in adapted}
    canonical_to_raw_ids = defaultdict(set)
    for raw_id in by_id:
        canonical_to_raw_ids[canonical_instance_id(raw_id)].add(raw_id)
'''
if old in text:
    text = text.replace(old, new, 1)
elif "canonical_to_raw_ids" not in text:
    raise SystemExit("score by_id anchor not found")

old = '''        seen.add(key); gold = by_id.get(iid)
        if gold is None: errors.append(f"prediction row {index}: unknown instance_id={iid}"); continue
'''
new = '''        seen.add(key); gold = by_id.get(iid)
        if gold is None:
            aliases = sorted(canonical_to_raw_ids.get(canonical_instance_id(iid), set()))
            if aliases:
                errors.append(f"prediction row {index}: instance_id must exactly match dataset ID; alias {iid!r} canonicalizes to {aliases}")
            else:
                errors.append(f"prediction row {index}: unknown instance_id={iid}")
            continue
'''
if old in text:
    text = text.replace(old, new, 1)
elif "instance_id must exactly match dataset ID" not in text:
    raise SystemExit("prediction binding anchor not found")

old = '''"split_scope_fail_closed": True}
'''
new = '''"split_scope_fail_closed": True, "canonical_instance_identity_required": True, "exact_prediction_instance_id_required": True, "instance_identity_normalization": "NFKC + casefold + remove whitespace/control-format characters"}
'''
if old in text:
    text = text.replace(old, new, 1)
elif text.count('"canonical_instance_identity_required": True') < 2:
    raise SystemExit("score return anchor not found")

TARGET.write_text(text, encoding="utf-8")
print(f"patched {TARGET}")
