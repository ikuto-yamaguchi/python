# R0-D Cycle 088 — canonical split regression repair

## Scope

Continue fail-closed R0 benchmark reproducibility, statistics, leakage, and artifact auditing on the single canonical branch. No memory, replay, fast weights, sleep, forgetting, or new mechanism work is introduced.

## Finding

The Cycle 087 canonical split hardening workflow applied the core patch and compiled successfully, but its focused regression failed before testing split aliases. The fixture declared `entity_holdout` and `dynamics_holdout` on its training rows, which correctly violates the existing dataset contract.

This was a test-fixture defect, not a reason to weaken the production holdout contract.

## Repair

The Cycle 087 fixture now uses:

- `in_distribution` for training rows;
- `entity_holdout+dynamics_holdout+language_holdout` only for evaluation rows;
- distinct train/evaluation entity and dynamics identities.

The canonical split assertions remain unchanged:

- canonical `train` / `test` spelling is accepted;
- full-width, zero-width-character, and surrounding-space aliases are rejected;
- alias spellings canonicalize to the same fingerprint identity but are not accepted as evidence labels.

## Classification

Until the core patch is committed by the workflow and the full focused/acceptance suite succeeds, the reproduction status remains `initial_reproduction_failure`.
