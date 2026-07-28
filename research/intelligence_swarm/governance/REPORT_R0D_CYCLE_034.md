# R0-D Cycle 034 — Alias-normalized schema leakage audit

## Scope

This cycle changes only the R0 reproducibility/leakage contract. It does not add memory, replay, fast weights, sleep, forgetting, a toy mechanism, or a new architecture.

## Defect

`evaluation_contract.py` rejects registered snake_case leakage keys, but concrete exporters may emit equivalent camelCase, kebab-case, spaced, or punctuation variants. Examples include:

- `goldStateAfter`
- `gold-action`
- `completedTrajectory`
- `terminalObservation`
- `episodeReturn`

A nested `model_input` payload using one of these variants could evade exact-string matching while carrying the same post-treatment, oracle, outcome, or completed-trajectory information.

## Change

Added `audit_schema_alias_leakage.py`, which normalizes keys by case-folding and removing non-alphanumeric characters before comparison with the forbidden model-input and prediction key sets.

The auditor checks:

1. `model_input_fields` entries;
2. arbitrarily nested dictionaries and lists under `model_input`;
3. prediction top-level keys;
4. unregistered prediction keys.

Any finding fails closed as `initial_reproduction_failure`.

## Regression coverage

`test_audit_schema_alias_leakage.py` fixes the following cases:

- clean canonical bundle passes;
- nested `goldStateAfter` fails;
- nested `completed-trajectory` fails;
- `goldAction` in `model_input_fields` fails;
- prediction `episodeReturn` fails;
- unknown prediction `debugPayload` fails.

A dedicated short GitHub Actions workflow compiles and runs these tests without starting the long SILG training workflow.

## Evidence status

This cycle creates no accepted benchmark result. It does not establish public-baseline reproduction, novelty, an intelligence principle, capability progress, or high-school-level intelligence. Until an immutable real R0 bundle passes the full acceptance gate, the formal status remains `initial_reproduction_failure`.
