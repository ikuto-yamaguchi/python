#!/usr/bin/env python3
"""Apply R0-D Cycle 084 strict JSON-integer seed identity to the core contract."""
from pathlib import Path

CORE = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")
REPORT = Path("research/intelligence_swarm/governance/REPORT_R0D_CYCLE_084.md")

text = CORE.read_text(encoding="utf-8")

anchor = '''def canonical_instance_id(value: Any) -> str:\n    """Canonical identity used only to detect aliases; raw IDs remain binding keys."""\n    return canonical_text(value)\n\n\n'''
insert = '''def canonical_instance_id(value: Any) -> str:\n    """Canonical identity used only to detect aliases; raw IDs remain binding keys."""\n    return canonical_text(value)\n\n\ndef strict_seed(value: Any) -> int:\n    """Accept only a real JSON integer, never bool/float/string aliases."""\n    if type(value) is not int:\n        raise ValueError("seed must be a JSON integer (bool/float/string aliases are forbidden)")\n    return value\n\n\n'''
if "def strict_seed(" not in text:
    if anchor not in text:
        raise SystemExit("canonical_instance_id anchor not found")
    text = text.replace(anchor, insert, 1)

text = text.replace('''        int(row["seed"]),\n        canonical_domain(row["domain"]),''', '''        strict_seed(row["seed"]),\n        canonical_domain(row["domain"]),''')
text = text.replace('''            seed = int(row["seed"])\n            seeds.add(seed); topology[(domain, split, condition)].add(seed); per_seed_splits[seed].add(split); per_domain_seed_splits[(domain, seed)].add(split)\n        except (TypeError, ValueError):\n            errors.append(f"row {index}: seed must be integer-like")''', '''            seed = strict_seed(row["seed"])\n            seeds.add(seed); topology[(domain, split, condition)].add(seed); per_seed_splits[seed].add(split); per_domain_seed_splits[(domain, seed)].add(split)\n        except (TypeError, ValueError):\n            errors.append(f"row {index}: seed must be a JSON integer; bool/float/string aliases are forbidden")''')

# All remaining cell/binding conversions must use the same strict rule.
text = text.replace('int(row.get("seed"))', 'strict_seed(row.get("seed"))')
text = text.replace('int(row["seed"])', 'strict_seed(row["seed"])')
text = text.replace('int(record.get("seed"))', 'strict_seed(record.get("seed"))')
text = text.replace('int(run.get("seed"))', 'strict_seed(run.get("seed"))')

# Persist the contract in audit artifacts when the return mapping has canonical identity flags.
marker = '"canonical_instance_identity_required": True,'
if marker in text and '"strict_seed_identity_required": True,' not in text:
    text = text.replace(marker, marker + '\n        "strict_seed_identity_required": True,\n        "seed_identity_rule": "type(seed) is int; bool, float and string aliases forbidden",', 1)

CORE.write_text(text, encoding="utf-8")
REPORT.write_text('''# R0-D Cycle 084 — strict seed identity core integration\n\n## Scope\n\nThis cycle changes only the R0 reproducibility/evaluation contract. It adds no memory, replay, fast weights, sleep or forgetting mechanism.\n\n## Fail-closed rule\n\nEvery dataset, score, resource-manifest and raw-log cell accepts a seed only when `type(seed) is int`. Python booleans, floats, numeric strings and Unicode-width numeric strings are rejected rather than coerced.\n\nExamples rejected: `true`, `1.0`, `1.9`, `"1"`, `"１"`.\n\nAny violation is classified as `initial_reproduction_failure`, and invalid score statistics remain suppressed.\n''', encoding="utf-8")
print("Cycle 084 strict seed patch applied")
