# RESET-E015 — R0 Research Reconstruction integration

Date: 2026-07-25  
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This integration accumulates only public benchmark reproduction, prior-art audit, evaluation-contract hardening, and the governance closure of empirical intervention-target work. It adds no toy mechanism, memory/replay/fast-weights/sleep/forgetting system, architecture family, hand-authored intervention ontology, stacked branch, or capability claim.

## Integrated evidence

### R0.1 SILG/RTFM

Pinned sources and protocol remain:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- seeds `1,7,19`
- official SILG `multi` recurrent baseline
- no pretrained language model

Corrected workflow run `30120620610` completed successfully. Each seed requested 32,768 frames and produced a checkpoint at 32,800 frames.

Resource audit:

| Seed | Training wall time | Peak RSS | Trained model bytes |
|---:|---:|---:|---:|
| 1 | 341.906 s | 480,076 KiB | 19,693,911 |
| 7 | 346.898 s | 505,600 KiB | 19,693,911 |
| 19 | 341.882 s | 483,056 KiB | 19,693,990 |

- parameters: `4,916,915`
- state-dict audit size: `19,694,385 bytes`
- CPU forward audit: `6.911 ms/step`
- total three-seed training time: `1,033.885 s`
- artifact digest: `662139632c73082f096154d819bef20f86f672d4e8f5b36f8667d754b6b751d2`

Matched fixed-initial-instance evaluation used 20 episodes per seed and method. Initial fingerprint streams matched across methods.

| Method | Win rate | Mean return | Mean episode length | CPU inference |
|---|---:|---:|---:|---:|
| Correct recurrent | 0.0167 | -1.8827 | 46.80 | 7.229 ms/step |
| Random valid action | 0.0667 | -1.1513 | 15.23 | 0.0081 ms/step |
| Language-blind | 0.0167 | -2.0417 | 54.75 | 4.424 ms/step |
| State-only | 0.0167 | -2.1963 | 62.48 | 4.103 ms/step |
| Language-shuffle | 0.0167 | -1.9347 | 49.40 | 7.252 ms/step |

Correct won 1/60 episodes and Random won 4/60. Correct did not separate from language-blind, state-only, or language-shuffle in aggregate win rate. This is insufficient policy competence and is not evidence that language is unnecessary.

Classification:

`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`

### R0.2 Environment-first

The previous trajectory comparison remains ineligible because the source policy produced almost no successful episodes and one seed collapsed to one action. The current implementation also remains a continuous Gaddy/Klein-style adaptation rather than a faithful reproduction of the authors' structured discrete-message default. Flat scalar MSE over mixed typed RTFM fields is not a valid next-state metric.

R0.2 remains blocked until a competent public source policy passes the existing success and anti-collapse gate. No Environment-first tuning is authorized before that point.

### Evaluation contract

The transition and SILG episode contracts now require independently readable raw-log, model, and immutable-data bytes; full 64-hex SHA-256 digests; full 40-hex code/source revisions; exact model-file size agreement; canonical seeds; finite resource values; immutable prediction fingerprints; complete Cartesian method/seed/domain/split coverage; leakage checks; paired statistics; and aggregate recomputation.

Ten regression tests pass. The current public run still lacks a complete joined manifest containing outcome/transition shuffle, either a valid non-oracle target-label shuffle or a formal inapplicability record, immutable serialized test-data checksum, and independently joined raw-log/model/data artifacts for every cell. Formal classification therefore remains `initial_reproduction_failure` under the strict contract.

### Prior art and RQ-001

C008 further narrowed the theory-only candidate. Treating language as an auxiliary variable, contrasting correct and shuffled language pairs, temporal-history identifiability, multimodal shared-latent recovery, and generic symmetry breaking are already covered by nonlinear ICA, temporal ICA, multimodal CRL, or environment-indexed invariance results.

- empirical Gate I / RQ-001-N5: rejected and closed
- RQ-001-T1: narrowed again, not adopted

A surviving theory claim would need a nontrivial equivalence remaining after complete non-language trajectories and after quotienting out every use of language as an auxiliary/environment index, plus a compositional language relation that strictly refines that equivalence and an intervention-supported semantics. No such positive construction or theorem currently exists.

## Integrated decision

1. Continue R0 Research Reconstruction.
2. Do not recognize a learned public capability baseline.
3. Do not start R0.2 model correction until the source public policy is competent and trajectory-eligible.
4. Keep empirical Gate I closed; do not add target/mechanism labels to SILG.
5. Keep RQ-001-T1 unadopted until formal equivalence, positive/negative constructions, novelty matrix, and preregistration are complete.
6. Do not recognize novelty, a new intelligence principle, or capability progress.
7. Do not propose the next stage.

## Single P0

Increase only the faithful official recurrent reproduction budget or correct an official reproduction-condition mismatch, retaining checkpoints and evaluating the same immutable matched protocol at staged budgets. Stop or classify resource insufficiency if competence does not emerge within the preregistered ceiling. Do not tune Environment-first against failed-policy trajectories.

## Status

- public environment/control path: reproduced
- official recurrent training path at 32,768 frames: reproduced
- corrected matched-evaluation path: reproduced
- learned public capability baseline: not reproduced
- R0.2 formal reproduction: not reproduced
- empirical Gate I: rejected
- RQ-001-T1: narrowed, not adopted
- novelty: not established
- new intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
