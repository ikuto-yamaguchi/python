# R0.2 Environment-first baseline — Cycle 011

## Decision

Status: `matched_typed_offline_comparison_harness_implemented_execution_on_qualified_silg_data_blocked`

No new operation/goal hypothesis, memory mechanism, architecture family, branch or PR chain was created.

## What was completed

The previously committed typed Gaddy--Klein-style implementation could train an environment-first model, but it did not yet execute the requested matched comparison. Cycle 011 adds `r02_typed_comparison.py`, which runs three methods on the same immutable typed trajectory file:

1. environment-first: language-free transition-message pretraining, frozen typed decoder, then instruction-to-message alignment;
2. end-to-end: the same language encoder and typed decoder trained directly;
3. state-only: the same typed decoder with an instruction-independent learned message.

The environment-first and end-to-end inference paths are required to have exactly equal parameter bytes. A mismatch fails closed.

## Saved measurements

For every method the harness saves:

- action accuracy;
- typed next-state loss;
- entity-holdout, dynamics-holdout and language-form-holdout metrics when those externally defined subsets are non-empty;
- task success only when an independently produced online `task_success` field is present;
- mean and median CPU inference latency per instance;
- training wall time;
- peak RSS;
- checkpoint path, bytes and SHA-256;
- dataset path, SHA-256, row counts and split names;
- parameter-budget accounting.

Offline reconstruction or action accuracy is never substituted for online task success.

## Reproducibility and rejection rules

The harness rejects:

- noncanonical requested seeds;
- a dataset whose recorded seed differs from the requested seed;
- train/test episode overlap;
- missing typed state schema;
- changing schema across rows;
- missing fields or invalid field widths;
- unequal environment-first/end-to-end inference parameter bytes.

Canonical seeds remain `1, 7, 19`.

## Regression path

Added:

- `test_r02_typed_comparison.py`
- `.github/workflows/r02_typed_comparison_tests.yml`

The test fixture verifies matched parameter bytes, all three methods, held-out-cell counts, typed next-state/action/task-success outputs, CPU latency, checkpoint bytes/hashes and seed mismatch rejection. The workflow is independent of the long SILG reproduction job and therefore does not restart R0.1.

At the time of this report, the workflow completion result has not been verified. No passing-test count is claimed.

## Remaining blocker

The canonical branch still has no verified completed 131,072-frame R0.1 source-policy artifact at the current head. Therefore no qualified three-seed SILG typed trajectories exist yet, and this comparison harness has not been run on public benchmark data.

The next admissible execution is:

1. finish exactly one competent R0.1 source-policy run;
2. export typed train/test trajectories for seeds `1, 7, 19`;
3. define real entity/dynamics/language-form holdouts without deriving labels from the evaluation outcomes;
4. run this comparison harness once per seed;
5. perform online SILG rollouts for task success on the same frozen splits;
6. join checkpoints, logs, datasets, predictions and checksums under the evaluation contract.

## Claims

- formal R0.2 public reproduction: not completed;
- public capability progress: not recognized;
- novelty: not claimed;
- intelligence principle: not claimed;
- high-school-level intelligence: not achieved.
