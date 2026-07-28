# R0D Cycle 015 — Concrete SILG schema and split-identity leakage audit

## Scope

This cycle changes only the R0 evaluation/reproducibility contract on the single canonical reconstruction branch. It adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, or PR chain.

## Defect found

The public SILG trajectory exporter writes the concrete fields:

- `text_tokens`
- `state_before`
- `state_after`
- `action`
- `episode_id`
- `episode_seed`
- `observation_fingerprint`
- `reward`
- `done`

The evaluation contract claimed SILG support but previously adapted only `action -> gold_action` and `state_after -> gold_state_after`. It still required `utterance`, so a raw exporter row could not pass the canonical schema without an external undocumented rewrite. This also meant train/test language overlap was not being computed directly from the actual token sequence.

## Changes

`evaluation_contract.py` now:

1. maps SILG `text_tokens` directly to canonical `utterance`;
2. records `utterance_source = text_tokens`;
3. maps `action -> gold_action` and `state_after -> gold_state_after`;
4. builds an explicit default `model_input` from prospective fields only;
5. excludes `reward`, `done`, `episode_return`, `episode_success`, action labels and after-state labels from default model inputs;
6. fingerprints episode identity and the raw observation fingerprint in addition to state/language/cell identity;
7. rejects any `episode_id`, `episode_seed`, or `observation_fingerprint` shared across train and evaluation splits;
8. reports coverage for required methods even when a method is completely absent.

The existing audits remain in force:

- normalized train/test utterance overlap;
- entity and dynamics holdout overlap;
- gold action/after-state and completed-trajectory leakage;
- full instance fingerprint matching;
- random, language-blind, state-only, target-label shuffle and outcome shuffle coverage;
- within-cell shuffle donor provenance, bijection and derangement;
- `method × seed × domain × split × condition` cells;
- mean and minimum cell gaps;
- cell confidence intervals, paired randomization, exact McNemar and clustered bootstrap;
- model bytes, peak RSS, training wall time, CPU latency, raw logs, full checksums and full code commit.

## Tests

The original 15 regression cases plus three concrete SILG-schema cases were executed locally against the updated file:

```text
Ran 18 tests in 2.775s
OK
```

The new cases verify:

- raw SILG exporter rows adapt without putting `reward` or `done` into model inputs;
- an episode seed reused across train/test is rejected;
- an identical observation fingerprint across train/test is rejected.

A separate repository regression file, `test_evaluation_contract_silg_schema.py`, preserves these concrete checks.

## Result classification

The stricter result remains:

`initial_reproduction_failure`

This cycle repairs the audit path; it does not create a successful baseline result. The following remain absent:

- real target-label-shuffle predictions, or a formal non-applicability record where SILG has no target label;
- real outcome-shuffle predictions and donor provenance;
- a complete readable artifact join for every required method, seed, domain, split and condition;
- an immutable serialized test dataset joined to predictions and raw logs;
- a competent learned public baseline.

No novelty, intelligence principle, capability progress, or high-school-level intelligence is claimed.
