# R0-D Cycle 086 — canonical split identity audit

## Scope

This cycle stays inside the R0 benchmark reproducibility/statistics/leakage audit. It does not add memory, replay, fast weights, sleep, or forgetting mechanisms.

## Finding

`evaluation_contract.py` currently normalizes split labels with `str(...).lower()` in dataset scoring and with NFKC+casefold in resource evidence. Neither path removes whitespace/control-format characters or requires exact canonical spelling.

Therefore semantically identical split labels such as `test`, `ＴＥＳＴ`, `te\u200bst`, and ` validation ` can be treated inconsistently across dataset topology, trajectory leakage checks, prediction eligibility, resource topology, and raw-log binding.

This can fragment train/evaluation evidence and prevent leakage/topology checks from comparing records that belong to the same canonical split.

## Added fail-closed auditor

- `audit_canonical_split_identity.py`
- `test_audit_canonical_split_identity.py`
- `.github/workflows/r0_canonical_split_identity_tests.yml`

The auditor applies:

- Unicode NFKC
- case folding
- whitespace removal
- control/format character removal
- exact canonical spelling requirement
- collision detection when multiple raw labels map to one canonical split
- evaluation-only split scope for resource manifests

Any violation is classified as `initial_reproduction_failure`.

## Regression cases

1. canonical `train`, `test`, and `validation` pass;
2. full-width split aliases fail;
3. zero-width/whitespace aliases fail;
4. canonical collisions are saved in the audit artifact;
5. labels empty after normalization fail;
6. resource manifests reject `train` and non-exact evaluation aliases.

## Status

The focused auditor and CI are present on the canonical branch. Direct integration into `evaluation_contract.py` remains required so dataset scoring, trajectory isolation, artifact topology, and raw-log binding cannot bypass this contract.

No R0 reproduction bundle is accepted. Public baseline reproduction remains unverified. Formal classification remains `initial_reproduction_failure`.
