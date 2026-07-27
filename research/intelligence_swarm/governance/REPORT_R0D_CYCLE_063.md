# R0-D Cycle 063 — normalized entity/dynamics holdout identity audit

## Scope

This cycle continues R0 benchmark reproducibility, leakage, statistics, and evidence auditing only. It does not add memory, replay, fast weights, sleep, or forgetting mechanisms.

## Defect

`evaluation_contract.validate_dataset()` normalized utterances before train/evaluation overlap checks, but entity and dynamics split signatures were hashed from raw values. A semantically identical identity could therefore evade holdout isolation through representation-only changes, including:

- Unicode fullwidth versus ASCII characters;
- letter case changes;
- whitespace or invisible control/format characters;
- numeric identifiers represented as numbers versus strings;
- structured dynamics values containing equivalent Unicode/case/number aliases.

Example: train `entity_id="Goblin"` and test `entity_id="ＧＯＢＬＩＮ"` produced different raw hashes even though they identify the same entity.

## Added fail-closed audit

`audit_normalized_holdout_identity.py` adapts the real dataset schema and independently checks every explicit entity/dynamics holdout against train identities after recursive canonicalization:

- Unicode NFKC;
- case folding;
- whitespace and Unicode control/format removal;
- scalar numeric/string alias collapse;
- deterministic recursive list and mapping canonicalization;
- exact normalized-signature comparison against train.

A missing holdout identity or any normalized train/evaluation overlap is classified as `initial_reproduction_failure`.

## Regression coverage

Focused tests cover:

1. distinct normalized entity holdout passes;
2. fullwidth/case entity alias fails;
3. numeric/string entity alias fails;
4. whitespace/invisible-character alias fails;
5. structured dynamics alias fails;
6. missing explicit holdout identity fails closed.

A short GitHub Actions workflow compiles and runs these regressions without starting model training.

## Current status

- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- New PR chain: none
- Actual accepted R0 reproduction bundles: 0
- Public baseline reproduction: not established
- Classification until a complete audited bundle passes: `initial_reproduction_failure`

The focused auditor is now present. Direct integration of the same canonical identity representation into `_split_sig()` in `evaluation_contract.py` and the unified acceptance gate remains required before the bypass is considered fully closed.
