# R0-D Cycle 073 — normalized domain/condition cell identity

## Scope

This cycle remains limited to R0 benchmark reproducibility, leakage, statistics, and artifact auditing. It does not add memory, replay, fast weights, sleep, forgetting, or a new learning mechanism.

## Failure found

The core contract still used raw `domain` and `condition` strings in dataset topology, shuffle cells, score cells, instance fingerprints, artifact cells, and raw-log measurement cells. Unicode width/case differences, invisible whitespace, condition token ordering, and delimiter differences could therefore split one semantic cell into multiple apparent cells.

Examples include:

- `RTFM` versus `ＲＴＦＭ`
- `dark world` versus `dark\u200bworld`
- `entity_holdout+dynamics_holdout` versus `DYNAMICS_HOLDOUT | ENTITY_HOLDOUT`

This could distort domain×seed×condition coverage, minimum-cell gaps, confidence intervals, paired tests, shuffle donor restrictions, and resource evidence binding.

## Fail-closed correction

Cycle 073 adds an idempotent core patch that canonicalizes:

- domain labels with Unicode NFKC, case folding, and whitespace/control-format removal;
- condition labels as normalized, sorted, unique tokens split on `+`, `,`, `|`, or whitespace;
- dataset topology, `_cell_key`, instance fingerprints, score grouping, raw-log cells, and artifact cells with the same identity rules.

Multiple distinct raw labels collapsing to one canonical domain or condition are rejected rather than silently merged. The failure classification remains `initial_reproduction_failure`.

## Evidence added

- `apply_r0d_cycle_073_core_normalized_cell_identity.py`
- `test_evaluation_contract_normalized_cell_identity_core.py`
- `.github/workflows/r0d_cycle_073_core_normalized_cell_identity.yml`

The focused regression checks Unicode aliases, condition order/delimiter aliases, canonical `_cell_key` equality, fingerprint stability, and fail-closed collision reporting.

## Reproduction status

No real R0 bundle or public baseline is accepted by this report. Resource/statistics acceptance remains zero until a complete bundle passes every contract with raw logs, checksums, public-baseline binding, and canonical cell coverage.
