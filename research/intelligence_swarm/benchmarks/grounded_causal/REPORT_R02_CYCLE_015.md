# R0.2 Cycle 015 — preregistered generator-metadata holdout construction

## Scope

This cycle does not introduce a new operation/goal toy hypothesis, memory mechanism, or model family. It closes one dataset-construction gap that blocked the faithful Environment-first versus End-to-end comparison on the pinned SILG/RTFM environment.

## Primary-source boundary

Gaddy and Klein (ACL 2019) learn an environment representation from language-free state transitions before connecting language to that representation. RTFM procedurally generates environment dynamics and corresponding language descriptions, and SILG exposes the pinned `silg:rtfm_train_s1-v0` and `silg:rtfm_test_s1-v0` environments. Therefore entity, dynamics, and language-form transfer assignments must be derived from generator-side episode metadata or a preregistered split specification, not from policy outcomes or learned representations.

Pinned sources remain:

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Gaddy & Klein 2019: ACL Anthology `P19-1188`

## Added implementation

`build_r02_preregistered_holdout_manifest.py` builds the episode-level immutable manifest consumed by `attach_r02_holdout_manifest.py`.

Inputs:

1. one generator-metadata row per episode, keyed by `domain × split × seed × episode_seed`;
2. a versioned preregistration JSON containing explicit held-out entity, dynamics, and language-form signature sets.

The builder refuses to read or accept action, reward, done, episode return, task success, prediction, action accuracy, or next-state loss fields. It therefore cannot assign holdouts from model behavior or evaluation outcomes.

It additionally requires:

- canonical seeds `1 / 7 / 19` only;
- unique episode keys;
- non-empty entity, dynamics, and language-form signatures;
- every preregistered signature to occur in test generator metadata;
- every holdout family to cover all three canonical seeds;
- train episodes never to be marked held out;
- SHA-256 for generator metadata, preregistration specification, and final manifest.

The output is deterministic and sorted by the complete episode key.

## Regression coverage

`test_build_r02_preregistered_holdout_manifest.py` fixes five cases:

1. valid three-seed manifest construction;
2. rejection of model/outcome fields in generator metadata;
3. rejection of preregistered signatures absent from test metadata;
4. rejection when one holdout lacks three-seed coverage;
5. rejection of duplicate episode metadata keys.

The lightweight R0.2 workflow now includes these tests. GitHub Actions completion has not yet been observed, so no CI pass count is claimed in this report.

## Remaining blocker

The official pinned RTFM generator still needs to emit the three signatures as episode metadata before rollout evaluation:

- `entity_signature`
- `dynamics_signature`
- `language_form_signature`

Those signatures must be defined from generator/configuration state, not reconstructed from rewards, completed trajectories, model predictions, or downstream metrics. Until this sidecar exists for seeds `1 / 7 / 19`, the real SILG comparison remains blocked.

After that sidecar is frozen, the existing path is:

1. build preregistered manifest;
2. attach it to typed trajectories;
3. pass holdout-assignment and matched-budget audits;
4. run Environment-first, parameter-matched End-to-end, and State-only;
5. measure online task success, typed next-state prediction, action accuracy, and all three transfers;
6. record checkpoint bytes/hash, peak RSS, wall time, CPU inference latency, dependencies, and raw logs.

## Classification

`preregistered_holdout_manifest_builder_implemented_generator_signature_sidecar_and_qualified_silg_execution_blocked`

No novelty, intelligence principle, or capability progress is claimed.
