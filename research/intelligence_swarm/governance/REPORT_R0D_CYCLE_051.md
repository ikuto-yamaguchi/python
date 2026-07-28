# R0-D Cycle 051 — Core explicit-holdout conformance audit

## Scope

This cycle advances R0 benchmark reproducibility, statistics, and leakage auditing only. It introduces no memory mechanism, replay, fast weights, sleep, forgetting, toy operation/goal hypothesis, architecture, or capability claim.

## Verified prior change

The canonical `evaluation_contract.py` now contains a fail-closed split vocabulary:

- train: `train`
- evaluation: `test`, `eval`, `validation`, `valid`

Both `validate_dataset()` and `score()` reject unregistered splits. The previously incomplete Cycle 050 split-scope change is therefore present on the canonical branch.

## Remaining defect found

The core entity/dynamics holdout rejection still depends on legacy boolean fields (`entity_holdout=true`, `dynamics_holdout=true`) when deciding whether train/evaluation signature overlap is an error.

The real-data schema also declares holdouts through `condition`, for example:

- `condition="entity_holdout"`
- `condition="dynamics_holdout"`
- compound condition strings

For those rows, the standalone explicit-condition auditor rejects missing or overlapping signatures even when the legacy boolean is absent, while `evaluation_contract.validate_dataset()` can still report `valid=true`.

This is a direct-core bypass: a caller that runs only `evaluation_contract.py validate` can obtain a successful result for a dataset that violates the authoritative explicit holdout contract.

## Completed audit artifact

Added:

- `audit_core_holdout_conformance.py`
- `test_audit_core_holdout_conformance.py`
- `.github/workflows/r0_core_holdout_conformance_tests.yml`

The conformance auditor executes both contracts on the same rows and fails closed when the explicit holdout audit rejects a dataset that the core contract accepts. The failure classification is always:

`initial_reproduction_failure`

Evidence saved includes:

- core validity
- explicit-condition validity
- agreement status
- direct-core bypass status
- error counts and examples from both contracts

## Regression cases

The focused tests cover:

1. a clean three-seed bundle where both contracts agree;
2. explicit `entity_holdout` overlap without a boolean flag;
3. explicit `dynamics_holdout` overlap without a boolean flag;
4. the legacy boolean path where both contracts reject the same violation.

## Decision

- R0 public baseline reproduced: **no**
- accepted model/RSS/runtime/latency bundle: **0**
- core explicit-condition holdout enforcement: **not yet integrated**
- direct-core bypass: **detected and now independently audited**
- classification until core and bundle acceptance both pass: **`initial_reproduction_failure`**
- capability progress, novelty, intelligence principle: **not recognized**

The next admissible change is to move the explicit-condition holdout declaration logic into `evaluation_contract.validate_dataset()` itself and add a core regression test. No new mechanism or next research stage is justified before that change and an accepted real artifact bundle.
