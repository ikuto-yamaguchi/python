# R0-D Cycle 010 — Native SILG matched-episode reproducibility audit

## Scope

This cycle extends the R0 evaluation contract to the native JSON schema emitted by `run_silg_matched_eval.py`. It does not add a memory mechanism, architecture, replay system, fast weights, sleep, or forgetting logic.

## Problem fixed

The existing `evaluation_contract.py` is strict for transition-level JSONL containing gold action and next-state labels. The public RTFM matched evaluator instead emits episode-level records:

- method
- seed
- episode seed
- immutable initial-instance fingerprint
- win
- return
- episode length
- checkpoint hashes and source pins

Previously, auditing this output required a lossy or hand-written conversion before paired statistics could be applied. That conversion could hide missing episodes, altered initial snapshots, or incomplete controls.

## Implementation

Added `evaluation_contract_silg_episode.py`, a companion native-schema adapter in the same benchmark contract directory.

It checks:

1. exact canonical seeds `1, 7, 19`;
2. `correct`, `random`, `language_blind`, `state_only`, and `language_shuffle` core coverage;
3. strict-control presence for `target_label_shuffle` and `outcome_shuffle`;
4. identical episode keys for every method;
5. one immutable initial-instance fingerprint per seed and episode across all methods;
6. duplicate method/episode records;
7. finite win, return, and length values;
8. binary win values;
9. checkpoint bytes/SHA-256 presence for every canonical seed;
10. SILG/RTFM source-pin presence.

It computes paired episode statistics for win, return, and episode length:

- seed-level mean, minimum, and maximum gap;
- fraction of seeds with positive gap;
- approximate 95% CI across seed cells;
- paired sign-randomization p-value;
- seed-cluster bootstrap 95% CI;
- exact McNemar test for win;
- correct-only, control-only, and tied episode counts.

## Classification rule

A payload may be structurally valid while still failing the complete reproduction contract.

- Missing fingerprints, seeds, coverage, checkpoints, or source pins: structural failure.
- Core matched methods present but `target_label_shuffle` or `outcome_shuffle` absent: structurally valid, but classified as `initial_reproduction_failure`.
- All structural and strict-control checks pass: `matched_episode_reproduced`.

This prevents the current five-method matched evaluator from being mislabeled as a complete public baseline reproduction.

## Validation

Executed locally with standard-library Python only:

```text
Ran 4 tests in 5.968s
OK
```

Covered cases:

- structurally valid payload with missing strict controls;
- complete strict-control payload;
- initial fingerprint mismatch;
- missing canonical seed and checkpoint.

## Current result

The current known RTFM matched-evaluation path provides:

- correct;
- random;
- language-blind;
- state-only;
- language-shuffle.

It does not yet emit:

- target-label shuffle;
- outcome shuffle.

Therefore the current formal classification remains:

`initial_reproduction_failure`

This does not invalidate the successful fixed-instance evaluation path. It means the complete R0 comparison contract and artifact join are not yet satisfied.

## Next minimum work

1. Add target-label and outcome/transition shuffle to the existing matched evaluator without changing the model.
2. Emit the native matched payload and artifact manifest from the same workflow run.
3. Join checkpoint, data, code, and raw-log checksums to every seed/method cell.
4. Run the native adapter and the artifact audit in CI; retain non-zero exit and JSON output on failure.

## Status

- Public capability baseline: not reproduced.
- New intelligence principle: not claimed.
- Capability progress: not claimed.
- High-school-level intelligence: not achieved.
