# R0-D Cycle 046 — Matched Metric Coverage Audit

## Scope

This cycle continues R0 benchmark reproducibility, statistics, and leakage auditing on the canonical reconstruction branch. It introduces no memory mechanism, replay, fast weights, sleep, forgetting, toy operation/goal hypothesis, or new architecture.

## Defect found

The current evaluation contract requires complete method-by-instance prediction coverage for the base action and prospective-state outputs. However, optional outputs such as `pred_inverse` can be present for only a subset of methods, instances, seeds, or cells. The scorer then constructs the corresponding metric from the surviving rows only.

Consequently, a method can omit a difficult optional metric on selected instances or cells while the remaining values still receive cell means, confidence intervals, and paired comparisons. This is selective metric reporting, not a matched comparison.

A related schema ambiguity exists when `gold_inverse` is present on only part of the evaluation set, or when predictions contain `pred_inverse` although no corresponding gold field exists.

## Added fail-closed auditor

`audit_prediction_metric_coverage.py` now requires:

- exactly the preregistered six methods;
- the same registered evaluation instances for every method;
- the base prediction fields on every row;
- canonical seeds `1 / 7 / 19`;
- only registered evaluation splits (`test`, `eval`, `validation`, `valid`);
- equal method counts inside every `domain × seed × split × condition` cell;
- all-or-none gold coverage for every optional metric;
- when an optional metric is defined by gold data, every method must predict it on every evaluation instance;
- when no gold field exists, methods must not inject that optional prediction field.

Any violation is classified as `initial_reproduction_failure`.

## Regression coverage

The new test suite fixes the following cases:

1. complete matched inverse-metric coverage passes;
2. one `state_only` row omitting `pred_inverse` fails;
3. partial `gold_inverse` coverage fails;
4. `pred_inverse` without `gold_inverse` fails;
5. one `outcome_shuffle` instance missing fails;
6. an unregistered `posthoc` split fails;
7. a noncanonical seed fails.

A short GitHub Actions workflow compiles and runs this suite without starting the long SILG workflow.

## Status

- accepted real R0 bundle: **0**
- accepted public baseline reproduction: **0**
- accepted model/RSS/runtime/latency bundle: **0**
- new intelligence principle: **not recognized**
- capability progress: **not recognized**
- classification until a complete bundle passes: **`initial_reproduction_failure`**

## Remaining integration work

The new auditor is currently an independent fail-closed contract. Direct invocation from the unified acceptance gate and equivalent enforcement inside `evaluation_contract.py score` remain required before this check is impossible to omit.
