# R0-D Cycle 044 — Explicit holdout-condition integrity

## Scope

This cycle changes only R0 benchmark reproducibility and leakage auditing. It adds no memory mechanism, replay, fast weights, sleep, forgetting, architecture, toy mechanism, or capability claim.

## Defect found

`evaluation_contract.validate_dataset()` collected entity and dynamics signatures by split, but rejected overlap only when a legacy boolean field such as `entity_holdout=true` or `dynamics_holdout=true` was present.

The concrete R0 schema also permits an explicit condition label, for example:

- `condition: entity_holdout`
- `condition: dynamics_holdout`
- `condition: entity_holdout+dynamics_holdout`

When the condition was explicit and the legacy boolean field was absent, train/evaluation signature overlap was reported in `holdout_integrity` but was not fail-closed. A manifest could therefore describe a held-out cell while reusing train entities or dynamics.

## Change

Added `audit_explicit_holdout_condition.py` and made it mandatory in `audit_r0_acceptance_bundle.py`.

The contract now treats an explicit condition label as authoritative, even without legacy boolean flags. For every evaluation row declaring entity or dynamics holdout it requires:

1. the corresponding `*_id` or `*_signature` to be present;
2. the normalized signature to be absent from the training split;
3. combined condition labels to enforce every declared holdout dimension;
4. failure classification as `initial_reproduction_failure`.

The auditor records train unique signature counts, held-out row counts, missing-signature examples, overlap examples, and domain/split/condition cells.

## Regression coverage

`test_audit_explicit_holdout_condition.py` fixes the following cases:

- explicit `entity_holdout` without a boolean flag still rejects train overlap;
- explicit `dynamics_holdout` without a boolean flag still rejects train overlap;
- a held-out row without the required signature is rejected;
- `entity_holdout+dynamics_holdout` enforces both dimensions;
- disjoint explicit holdouts pass.

A short GitHub Actions workflow compiles the core and integrated acceptance gate and runs these regressions. It does not start the long SILG workflow.

## Status

- Accepted real R0 evidence bundles: 0
- Public baseline reproduction: not accepted
- Accepted model/RSS/runtime/latency bundles: 0
- Classification until a complete bundle passes: `initial_reproduction_failure`
- Capability progress: not claimed
- New intelligence principle: not claimed
