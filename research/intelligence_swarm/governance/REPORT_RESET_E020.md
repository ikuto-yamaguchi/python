# RESET-E020 — R0 Research Reconstruction Integration

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope and branch policy

This integration keeps one canonical reconstruction branch. No new A–D toy mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, researcher-authored intervention ontology, new architecture family, or stacked PR chain is authorized. Existing stacked draft PRs remain negative-results archives and are not experiment bases.

## 1. Primary-literature and official-code boundary

C013 adds Lee, Jin and Aragam (2026), *Beyond identifiability: Learning causal representations with few environments and finite samples* (`arXiv:2603.25796`) to the novelty matrix.

Under full-column-rank linear mixing, a linear acyclic latent SEM, an observational environment, noise diversity and a strongly separating intervention design, unknown multi-node intervention targets, the latent graph, latent representation and decoder are recoverable up to scale/permutation with `O(log d)` environments and finite-sample guarantees.

Consequences:

- unknown intervention-target recovery is not an admissible language novelty claim;
- if the non-language intervention family is strongly separating, language can at most supply semantic naming/alignment, not additional causal identification;
- the only remaining RQ-001 entry point is strict refinement of a precisely characterized residual causal abstraction left by a non-strongly-separating intervention family;
- that narrowed question remains unadopted and cannot be implemented before preregistration and external baseline reproduction.

## 2. R0.1 SILG / RTFM public reproduction

Pinned conditions remain:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`;
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`;
- train `silg:rtfm_train_s1-v0`;
- test `silg:rtfm_test_s1-v0`;
- official `multi` recurrent;
- seeds `1,7,19`;
- no pretrained language model.

Latest completed evidence remains the 32,768-frame staged run:

- parameters: `4,916,915`;
- state-dict audit: `19,694,385 bytes`;
- maximum RSS: `505,600 KiB`;
- total three-seed training wall time: `1,033.885 s`;
- CPU forward audit: `6.911 ms/step`;
- Correct win rate: `0.0167`;
- Random win rate: `0.0667`;
- Language-blind, State-only and Language-shuffle: each `0.0167`.

Correct remains below Random, so no learned public capability baseline is reproduced.

At this integration, workflow run `30138560445` has completed checkout, Python setup, host recording, pinned-source installation and canonical random/schema probing, and remains inside the official 131,072-frame recurrent-training step. No unfinished checkpoint, resource, capability, trajectory or R0.2 value is incorporated.

## 3. R0.2 Environment-first baseline

Cycle 009 adds a typed structured-message implementation path fixed to Gaddy & Klein 2019 and authors' code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`:

- language-free transition pretraining;
- 20 categorical message variables × 30 symbols;
- straight-through Gumbel-Softmax;
- shared typed next-state/action decoder;
- LSTM language encoder;
- direct environment/language message-distribution matching, weight `0.01`;
- decoder frozen during language training by default;
- categorical CE, binary BCE and continuous MSE losses;
- seeds `1,7,19`, episode-disjointness and resource/hash reporting.

The entry point intentionally rejects legacy flattened SILG rows and requires `state_before_fields`, `state_after_fields` and `state_schema`. It has not been executed because the active source-policy run is unfinished and the current exporter does not preserve typed field boundaries.

Classification:

`typed_discrete_message_method_path_implemented_dataset_and_online_evaluation_blocked`

No R0.2 result is recognized until competent non-collapsed source trajectories, typed export, parameter/topology-matched end-to-end and state-only controls, real entity/dynamics/language-form holdouts, online task success, action accuracy, typed next-state metrics, CPU latency and complete artifacts exist.

## 4. Evaluation contract and leakage

D016 adds an immutable prediction-to-dataset artifact join on top of D015.

For every `method × seed × domain × split × condition` run, the audit now requires:

- `prediction_path` and full `prediction_sha256`;
- readable prediction JSONL;
- manifest/prediction method identity agreement;
- unique prediction instance IDs;
- exact prediction/dataset instance-set equality;
- per-row instance-fingerprint agreement;
- one immutable dataset hash shared by all methods in a cell;
- stable model SHA and code commit for each method/seed across split and condition cells.

D016 tests are committed but not yet executed by a GitHub Actions job, so no new passing-test count is claimed. Existing completed SILG evidence lacks the full six-method prediction artifact join and remains `initial_reproduction_failure`.

D015's 18 executed regression tests remain the latest verified count.

## 5. RQ-001 decision

- empirical Gate I / R0.3: rejected;
- broad raw-language / latent-intervention joint-identification formulation: rejected;
- unknown-target recovery as a language contribution: rejected;
- only admissible residual-abstraction-refinement formulation: narrowed, not adopted.

Adoption requires an explicit deficient intervention design, its residual abstraction, a population grammar preventing utterance lookup, restrictions excluding arbitrary language-factor merging/splitting, a positive refinement theorem, a matched impossibility theorem, unseen-form/tuple/target tests, and direct comparison against logarithmic-environment unknown-target CRL, causal-abstraction, WM3C and auxiliary/multi-view baselines.

## 6. Single P0 and stage decision

Single P0 remains completion and immutable verification of the active 131,072-frame official SILG recurrent run. Until a competent external public baseline exists:

- R0.2 tuning is forbidden;
- new architecture and mechanism families are forbidden;
- RQ-001 implementation is forbidden;
- no novelty, intelligence-principle or capability-progress claim is accepted.

No next stage is proposed. R0.1–R0.3, the novelty matrix and exactly one preregistered central claim are not all complete.

## Status

- public learned capability baseline: `0`;
- formal R0.2 reproduction: `0`;
- strict evaluation classification: `initial_reproduction_failure`;
- new intelligence principle: none;
- capability progress: not recognized;
- high-school-level intelligence: not achieved;
- completion: false.
