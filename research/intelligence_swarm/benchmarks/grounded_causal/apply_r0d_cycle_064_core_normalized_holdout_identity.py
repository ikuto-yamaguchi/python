#!/usr/bin/env python3
"""Idempotently integrate normalized entity/dynamics identity hashing into the R0 core contract."""
from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0 and new in text:
        return text
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one old block, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import unicodedata\n",
        "import unicodedata\nfrom decimal import Decimal, InvalidOperation\n",
        "decimal import",
    )
    old = '''def _split_sig(row: dict[str, Any], *keys: str) -> str | None:\n    for key in keys:\n        if row.get(key) is not None:\n            return stable_hash(row[key])\n    return None\n'''
    new = '''def _canonical_identity_number(value: Any) -> str | None:\n    if isinstance(value, bool):\n        return None\n    if isinstance(value, (int, float)):\n        if isinstance(value, float) and not math.isfinite(value):\n            return None\n        raw = str(value)\n    elif isinstance(value, str):\n        raw = canonical_text(value)\n        if not re.fullmatch(r"[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:e[+-]?\\d+)?", raw):\n            return None\n    else:\n        return None\n    try:\n        number = Decimal(raw)\n    except InvalidOperation:\n        return None\n    if not number.is_finite():\n        return None\n    number = number.normalize()\n    if number == 0:\n        number = Decimal(0)\n    return format(number, "f")\n\n\ndef canonical_holdout_identity(value: Any) -> Any:\n    """Canonicalize semantic split identities before hashing.\n\n    This intentionally collapses Unicode width/case, whitespace and control/format\n    differences, numeric-vs-string scalar aliases, and recursively normalizes\n    mappings and sequences. Mapping keys are represented as sorted pairs so that\n    normalization collisions remain visible and deterministic.\n    """\n    if value is None:\n        return {"type": "null", "value": None}\n    if isinstance(value, bool):\n        return {"type": "bool", "value": value}\n    number = _canonical_identity_number(value)\n    if number is not None:\n        return {"type": "number", "value": number}\n    if isinstance(value, str):\n        return {"type": "text", "value": canonical_text(value)}\n    if isinstance(value, dict):\n        pairs = [\n            [canonical_holdout_identity(key), canonical_holdout_identity(item)]\n            for key, item in value.items()\n        ]\n        pairs.sort(key=lambda pair: json.dumps(pair[0], ensure_ascii=False, sort_keys=True, separators=(",", ":")))\n        return {"type": "mapping", "value": pairs}\n    if isinstance(value, (list, tuple)):\n        return {"type": "sequence", "value": [canonical_holdout_identity(item) for item in value]}\n    if isinstance(value, (set, frozenset)):\n        items = [canonical_holdout_identity(item) for item in value]\n        items.sort(key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))\n        return {"type": "set", "value": items}\n    return {"type": "text", "value": canonical_text(value)}\n\n\ndef _split_sig(row: dict[str, Any], *keys: str) -> str | None:\n    for key in keys:\n        if row.get(key) is not None:\n            return stable_hash(canonical_holdout_identity(row[key]))\n    return None\n'''
    text = replace_once(text, old, new, "normalized split signature")
    text = replace_once(
        text,
        '"unicode_utterance_overlap_required": True, "alias_normalized_leakage_required": True',
        '"unicode_utterance_overlap_required": True, "holdout_identity_normalization": "recursive NFKC + casefold + remove whitespace/control-format + numeric scalar alias collapse", "normalized_holdout_identity_required": True, "alias_normalized_leakage_required": True',
        "audit metadata",
    )
    TARGET.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
