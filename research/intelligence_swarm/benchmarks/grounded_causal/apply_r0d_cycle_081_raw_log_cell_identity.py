#!/usr/bin/env python3
"""Apply R0-D Cycle 081: canonical raw-log/resource cell identity.

Fail closed when resource manifests use raw domain/condition aliases and bind raw-log
measurement records with the same canonical cell identity used by score statistics.
"""
from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one patch anchor, found {count}: {old[:80]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '''def _raw_log_cell(row: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(row["method"]),
        int(row["seed"]),
        str(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        str(row["condition"]),
    )
''',
        '''def _raw_log_cell(row: dict[str, Any]) -> tuple[str, int, str, str, str]:
    """Use the same canonical cell identity as dataset scoring and artifact topology."""
    return (
        str(row["method"]),
        int(row["seed"]),
        canonical_domain(row["domain"]),
        unicodedata.normalize("NFKC", str(row["split"])).casefold(),
        canonical_condition(row["condition"]),
    )
''',
    )

    text = replace_once(
        text,
        '''        if field == "split":
            expected = unicodedata.normalize("NFKC", str(expected)).casefold()
            observed = unicodedata.normalize("NFKC", str(observed)).casefold()
        elif field == "seed":
''',
        '''        if field == "split":
            expected = unicodedata.normalize("NFKC", str(expected)).casefold()
            observed = unicodedata.normalize("NFKC", str(observed)).casefold()
        elif field == "domain":
            expected, observed = canonical_domain(expected), canonical_domain(observed)
        elif field == "condition":
            expected, observed = canonical_condition(expected), canonical_condition(observed)
        elif field == "seed":
''',
    )

    text = replace_once(
        text,
        '''    methods, cells, seeds, domains, topology, commits = set(), set(), set(), set(), set(), set(); identity = defaultdict(set)
''',
        '''    methods, cells, seeds, domains, topology, commits = set(), set(), set(), set(), set(), set(); identity = defaultdict(set)
    raw_domains_by_canonical, raw_conditions_by_canonical = defaultdict(set), defaultdict(set)
''',
    )

    text = replace_once(
        text,
        '''            domain = str(run["domain"])
            split = unicodedata.normalize("NFKC", str(run["split"])).casefold()
            condition = str(run["condition"])
''',
        '''            raw_domain, raw_condition = str(run["domain"]), str(run["condition"])
            domain = canonical_domain(raw_domain)
            split = unicodedata.normalize("NFKC", str(run["split"])).casefold()
            condition = canonical_condition(raw_condition)
            raw_domains_by_canonical[domain].add(raw_domain)
            raw_conditions_by_canonical[condition].add(raw_condition)
''',
    )

    text = replace_once(
        text,
        '''    required = REQUIRED_METHODS; missing_methods, unexpected_methods = required - methods, methods - required
''',
        '''    domain_collisions = {key: sorted(values) for key, values in raw_domains_by_canonical.items() if key and len(values) > 1}
    condition_collisions = {key: sorted(values) for key, values in raw_conditions_by_canonical.items() if key and len(values) > 1}
    if domain_collisions:
        errors.append(f"artifact domain labels collide after canonicalization: {domain_collisions}")
    if condition_collisions:
        errors.append(f"artifact condition labels collide after canonicalization: {condition_collisions}")
    required = REQUIRED_METHODS; missing_methods, unexpected_methods = required - methods, methods - required
''',
    )

    text = replace_once(
        text,
        '''"raw_log_bound_fields": list(RAW_LOG_MEASUREMENT_FIELDS), "classification": "reproduced" if not errors else "initial_reproduction_failure"}
''',
        '''"raw_log_bound_fields": list(RAW_LOG_MEASUREMENT_FIELDS), "normalized_resource_cell_identity_required": True, "resource_cell_identity_normalization": "domain=NFKC+casefold+remove whitespace/control-format; condition=canonical sorted token set", "artifact_domain_label_collisions": domain_collisions, "artifact_condition_label_collisions": condition_collisions, "classification": "reproduced" if not errors else "initial_reproduction_failure"}
''',
    )

    TARGET.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
