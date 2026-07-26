# R0-D Cycle 047 — Metric coverage made mandatory in the unified acceptance gate

## Scope

This cycle continues the R0 benchmark reproducibility, statistics, and leakage audit on the canonical reconstruction branch. It adds no memory, replay, fast-weights, sleep, forgetting, toy mechanism, architecture, or capability claim.

## Defect closed

`audit_prediction_metric_coverage.py` already rejected selective reporting of optional metrics, unequal per-method metric coverage, partial gold metric availability, unregistered evaluation splits, and noncanonical seeds. However, the single formal acceptance path in `audit_r0_acceptance_bundle.py` did not invoke that auditor.

Consequently, a bundle could pass dataset, payload, paired-statistics, resource, checksum, path-containment, and prediction-cell-binding checks while omitting `pred_inverse` only for difficult instances or methods. The core scorer would then aggregate only the surviving metric values and could emit cell means, confidence intervals, and paired gaps from a selectively reduced subset.

## Fail-closed change

The unified acceptance gate now requires `prediction_metric_coverage_contract` in the same invocation as all other contracts.

Acceptance now requires:

- exactly the registered six methods;
- identical evaluation-instance coverage for every method;
- registered evaluation splits only;
- canonical seeds `1`, `7`, and `19`;
- equal method counts in every `domain × seed × split × condition` cell;
- optional gold metrics to be present on all evaluation instances or none;
- when an optional gold metric is present, every method must emit its corresponding prediction for every instance;
- prediction-only optional metrics without a gold target are rejected.

Any failure is classified as `initial_reproduction_failure`, even when the paired-statistics contract itself returns `valid=true`.

## Regression coverage

The unified-gate regression tests now verify that:

1. all contracts must pass for `reproduced`;
2. selective metric omission alone rejects an otherwise valid bundle;
3. paired-statistics success cannot hide metric-coverage failure;
4. metric-coverage failure is preserved alongside alias, payload, resource, path, cell-binding, and checksum failures;
5. acceptance metadata explicitly records same-instance metric coverage and forbids selective metric reporting.

The short CI workflow now compiles `audit_prediction_metric_coverage.py` and is triggered when that auditor changes.

## Formal status

- Accepted real R0 bundles: 0
- Public baseline reproduction: not yet accepted
- Accepted model/RSS/runtime/latency evidence bundles: 0
- Classification until a complete bundle passes: `initial_reproduction_failure`
- New mechanism introduced: no
- Capability progress claimed: no
- New intelligence principle claimed: no
