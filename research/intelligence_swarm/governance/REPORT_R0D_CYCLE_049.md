# R0-D Cycle 049 — Registered evaluation split scope is mandatory

## Scope

This cycle advances R0 benchmark reproducibility/statistics/leakage auditing only.
No memory mechanism, replay, fast weights, sleep, forgetting, model architecture,
or new toy hypothesis was introduced.

## Finding

`audit_prediction_eval_split_scope.py` already rejected unregistered dataset splits
such as `debug`, `calibration`, `analysis`, and `posthoc`. However, the canonical
single acceptance gate did not invoke that auditor.

The core scorer still builds its evaluation set from rows whose split is merely
not `train`. Therefore a bundle could obtain a valid paired-statistics result while
including a non-preregistered split, and the unified gate could accept the bundle
if the split-scope companion auditor was not run separately.

"Not train" is not equivalent to "registered evaluation split".

## Change

The canonical unified gate now requires
`prediction_eval_split_scope_contract` in the same fail-closed invocation as:

- dataset/schema and leakage validation,
- explicit entity/dynamics holdout integrity,
- prediction payload validation,
- complete same-instance metric coverage,
- paired statistics,
- resource and checksum evidence,
- bundle path containment,
- prediction-cell binding, and
- statistics recomputation binding.

The only accepted split vocabulary is:

- training: `train`
- evaluation: `test`, `eval`, `validation`, `valid`

Any other split causes the whole bundle to be classified as
`initial_reproduction_failure`, even when `evaluation_contract.score()` reports a
valid paired-statistics result.

## Regression coverage

The unified-gate tests now establish that:

1. all contracts, including split scope, must pass for `reproduced`;
2. an unregistered `debug` split cannot be hidden by a valid paired score;
3. split-scope failure is preserved alongside alias, payload, metric-coverage,
   resource, path, cell-binding, checksum, and recomputation failures; and
4. the acceptance result records the exact permitted split vocabulary.

The short CI workflow now watches and compiles
`audit_prediction_eval_split_scope.py` as a mandatory dependency of the unified
gate. It does not trigger the long SILG training workflow.

## Classification

- Accepted real R0 reproduction bundles: 0
- Public baseline reproduction: not yet accepted
- Accepted model/RSS/runtime/latency evidence bundles: 0
- Capability progress: not recognized
- New intelligence principle: not recognized
- Failure classification: `initial_reproduction_failure`

## Remaining core gap

`evaluation_contract.score()` itself still defines evaluation rows using
`split != "train"`. The canonical acceptance path is now fail-closed because the
registered split-scope auditor is mandatory, but direct core scoring should later
replace that predicate with explicit membership in the registered evaluation
split set.
