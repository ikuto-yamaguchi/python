#!/usr/bin/env python3
"""Apply Cycle 087 canonical split identity hardening to evaluation_contract.py."""
from pathlib import Path

CORE = Path(__file__).parents[1] / "benchmarks/grounded_causal/evaluation_contract.py"
text = CORE.read_text(encoding="utf-8")

anchor = '''def strict_seed(value: Any) -> int:\n    """Accept only a real JSON integer, never bool/float/string aliases."""\n    if type(value) is not int:\n        raise ValueError("seed must be a JSON integer (bool/float/string aliases are forbidden)")\n    return value\n\n\n'''
insert = anchor + '''def canonical_split(value: Any) -> str:\n    """Canonical split identity used by dataset, scoring and fingerprints."""\n    return canonical_text(value)\n\n\ndef split_spelling_is_canonical(value: Any) -> bool:\n    """Evidence split labels must already use the registered canonical spelling."""\n    return type(value) is str and value == canonical_split(value) and value in ALLOWED_SPLITS\n\n\n'''
if "def canonical_split(" not in text:
    if anchor not in text:
        raise SystemExit("strict_seed anchor not found")
    text = text.replace(anchor, insert, 1)

replacements = {
    'str(row["split"]).lower()': 'canonical_split(row["split"])',
    'str(row.get("split", "")).lower()': 'canonical_split(row.get("split", ""))',
    'str(r.get("split", "")).lower()': 'canonical_split(r.get("split", ""))',
    'str(r["split"]).lower()': 'canonical_split(r["split"])',
}
for old, new in replacements.items():
    text = text.replace(old, new)

old = '''        if not split:\n            errors.append(f"row {index}: split must be non-empty")\n        elif split not in ALLOWED_SPLITS:\n            errors.append(f"row {index}: unregistered split={split!r}; allowed={sorted(ALLOWED_SPLITS)}")\n'''
new = '''        if not split:\n            errors.append(f"row {index}: split must be non-empty after canonicalization")\n        elif split not in ALLOWED_SPLITS:\n            errors.append(f"row {index}: unregistered split={split!r}; allowed={sorted(ALLOWED_SPLITS)}")\n        elif not split_spelling_is_canonical(row["split"]):\n            errors.append(\n                f"row {index}: split must use exact canonical spelling; "\n                f"raw={row['split']!r}, canonical={split!r}"\n            )\n'''
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("dataset split validation anchor not found")

marker = '"split_scope_fail_closed": True,'
if '"canonical_split_identity_required": True' not in text:
    if marker not in text:
        raise SystemExit("split-scope result marker not found")
    text = text.replace(
        marker,
        marker + ' "canonical_split_identity_required": True, "split_identity_normalization": "NFKC + casefold + remove whitespace/control-format; exact registered spelling required",',
        1,
    )

CORE.write_text(text, encoding="utf-8")
print(CORE)
