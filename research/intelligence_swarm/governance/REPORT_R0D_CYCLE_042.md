# R0-D Cycle 042 — Prediction artifact cell binding

## Scope

This cycle advances only R0 benchmark reproducibility, statistics, and leakage auditing on the canonical reconstruction branch. It introduces no memory, replay, fast-weights, sleep, forgetting, architecture, or capability claim.

## Defect found

The existing checksummed prediction-evidence audit verified that each prediction file existed, matched its SHA-256, was non-empty, and contained only the manifest-declared method. It did not require prediction rows to carry or match the manifest-declared `seed`, `domain`, `split`, and `condition`.

Consequently, one pooled or arbitrary prediction file could be referenced by multiple manifest run cells. The manifest could appear to have complete `domain × seed × condition × method` coverage while the prediction bytes did not prove which cell produced them.

A checksum binds bytes to a path; it does not bind those bytes to a declared experimental cell.

## Fail-closed correction

Added `audit_prediction_cell_binding.py` and made it mandatory in `audit_r0_acceptance_bundle.py`.

For every manifest run, the auditor now requires:

- prediction rows include `method`, `seed`, `domain`, `split`, and `condition`;
- every row exactly matches the run's declared cell;
- each prediction artifact contains exactly one declared cell;
- one prediction artifact path is not reused across multiple declared cells;
- methods are exactly `correct`, `random`, `language_blind`, `state_only`, `target_label_shuffle`, and `outcome_shuffle`;
- seeds are exactly `1`, `7`, and `19`.

Any mismatch is classified as `initial_reproduction_failure`.

## Regression coverage

Added tests for:

1. a complete cell-bound 6-method × 3-seed bundle;
2. a prediction row with the wrong seed;
3. a pooled artifact containing multiple cells;
4. one artifact reused by two declared cells;
5. a prediction row missing a cell-index field;
6. unified acceptance rejection when only the new cell-binding contract fails.

Dedicated short CI and the unified acceptance CI were updated. The long-running SILG reproduction workflow is not triggered by this change.

## Research status

- Accepted R0 evidence bundles: 0
- Public baseline reproduction: not accepted
- Accepted model/RSS/runtime/latency evidence: 0
- Capability progress: not recognized
- New intelligence principle: not recognized
- Current failure class: `initial_reproduction_failure`
