#!/usr/bin/env python3
"""Apply R0-D Cycle 083 strict JSON-integer seed identity hardening."""
from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")
text = TARGET.read_text(encoding="utf-8")

needle = '''def canonical_instance_id(value: Any) -> str:
    """Canonical identity used only to detect aliases; raw IDs remain binding keys."""
    return canonical_text(value)


'''
replacement = needle + '''def canonical_seed(value: Any, *, allow_invalid: bool = False) -> int:
    """Require an actual JSON integer seed; reject bool/float/string aliases."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if allow_invalid:
        return -1
    raise ValueError("seed must be a JSON integer; bool, float, and string aliases are forbidden")


'''
if needle not in text:
    raise SystemExit("canonical_instance_id insertion point not found")
text = text.replace(needle, replacement, 1)

cell_anchor = '        int(row["seed"]),\n        canonical_domain(row["domain"]),'
if text.count(cell_anchor) != 2:
    raise SystemExit(f"expected two row seed cell anchors, found {text.count(cell_anchor)}")
text = text.replace(
    cell_anchor,
    '        canonical_seed(row["seed"], allow_invalid=True),\n        canonical_domain(row["domain"]),',
)

replacements = {
    '    payload["domain"] = canonical_domain(row.get("domain", ""))\n': '    payload["seed"] = canonical_seed(row.get("seed"), allow_invalid=True)\n    payload["domain"] = canonical_domain(row.get("domain", ""))\n',
    '            seed = int(row["seed"])\n': '            seed = canonical_seed(row["seed"])\n',
    '                expected, observed = int(expected), int(observed)\n': '                expected, observed = canonical_seed(expected), canonical_seed(observed)\n',
    '                errors.append(f"run {index}: seed is not integer-like in manifest or raw log")\n': '                errors.append(f"run {index}: seed must be an exact JSON integer in manifest and raw log")\n',
    '            seed = int(run["seed"])\n': '            seed = canonical_seed(run["seed"])\n',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"required patch anchor not found: {old!r}")
    text = text.replace(old, new)

return_anchor = '"instance_id_collisions": instance_id_collisions}'
if return_anchor not in text:
    raise SystemExit("dataset audit return anchor not found")
text = text.replace(
    return_anchor,
    '"instance_id_collisions": instance_id_collisions, "canonical_seed_identity_required": True, "seed_identity_schema": "exact JSON integer; bool/float/string aliases forbidden"}',
    1,
)

TARGET.write_text(text, encoding="utf-8")
print(f"patched {TARGET}")
