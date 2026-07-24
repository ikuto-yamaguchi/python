# RESET-E018 — R0 Research Reconstruction Integration

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This integration preserves one canonical reconstruction branch. It adds no toy mechanism, memory/replay/fast-weights/sleep/forgetting component, architecture family, researcher-authored intervention ontology, synthetic benchmark, or stacked PR chain. Existing stacked drafts remain negative-results archives.

## 1. Primary-work and official-code overlap audit

C011 completed an identifiability counterexample and theorem/assumption comparison. The current RQ-001-T1 formulation is rejected because every utterance and deterministic raw-string relation observed on a finite benchmark can be represented losslessly by a finite auxiliary index such as `U=index(L)`.

The remaining literature boundary includes unknown and uncoupled intervention-target recovery, intervention-induced causal abstractions, finite-sample unknown-target CRL, auxiliary-variable and multi-view identifiability, grouping/weak supervision and mechanism-sparsity results. Therefore unknown targets, language pairing, shuffle negatives, utterance grouping or multiple views do not establish novelty by themselves.

Only one reformulation remains admissible for later preregistration: an explicit population grammar, a restricted auxiliary family unable to copy utterance identity, unseen utterance forms and refinement of a specified residual causal abstraction. It is not adopted and no implementation is authorized.

## 2. Public benchmark reproduction

Pinned R0.1 remains SILG/RTFM with official source commits, `rtfm_train_s1-v0` / `rtfm_test_s1-v0`, seeds `1,7,19`, official `multi` recurrent and no pretrained language model.

Latest completed evidence remains the 32,768-frame staged run:

- parameters: `4,916,915`
- state-dict audit: `19,694,385 bytes`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind / State-only / Language-shuffle win rate: `0.0167`

Correct underperforms Random, so this is not a public capability reproduction.

At integration time, head workflow run `30133481693` remains in the official 131,072-frame recurrent training step. No unfinished result or resource value is recognized.

J-CRe3 remains an unexecuted external Japanese realism audit and is not combined with SILG.

## 3. Controls

Required same-instance controls remain Correct, Random, Language-blind, State-only, environment-ID-only, language shuffle, transition/outcome shuffle, and target-label shuffle only if a non-oracle benchmark target exists. Otherwise target-label shuffle requires a formal inapplicability record.

The completed 32,768-frame matched evaluation only qualifies the execution path, not capability.

## 4. Resources, seeds and splits

Canonical seeds remain `1,7,19`. All future accepted runs require exact source/code pins, immutable split/data checksum, model bytes, peak RSS, training wall time, CPU inference latency and readable raw logs. No incomplete or favorable-seed result may be integrated.

## 5. Evaluation and leakage

D014 remains active with 15 passing regression tests. It requires complete `method × seed × domain × split × condition` prediction and artifact coverage, immutable fingerprints, utterance/entity/dynamics overlap checks, gold-after/action and completed-trajectory leakage checks, paired statistics, exact McNemar, hierarchical bootstrap CI, aggregate recomputation, full hashes and shuffle donor provenance.

Real outcome/transition-shuffle predictions, formal target-label inapplicability or real predictions, immutable serialized test checksum and complete artifact joins remain missing. Classification remains `initial_reproduction_failure`.

## 6. RQ-001 decision

- Gate L: continued, not passed.
- Gate I empirical track: rejected.
- RQ-001-N5: rejected.
- RQ-001-T1 current formulation: rejected by finite-index collapse.
- Population-level restricted-auxiliary reformulation: allowed only as a future preregistration candidate, not adopted.

## R0.2 and R0.3

R0.2 remains blocked because the existing source trajectories fail success and action-diversity gates, and the current adaptation is not the official Gaddy & Klein default baseline. No tuning is authorized until R0.1 policy competence and trajectory eligibility pass.

R0.3 empirical hidden-intervention-target ablation remains formally rejected because the audited public benchmarks do not provide the required independent target/mechanism ground truth and researcher-authored ontology is forbidden.

## Integrated decision

- Stage remains R0.
- Public learned capability baselines reproduced: `0`.
- Formal R0.2 reproductions: `0`.
- New mechanism family: none.
- New architecture: none.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not recognized.
- High-school-level intelligence: not achieved.
- Next-stage proposal: blocked.

## Single P0

Complete and fully verify the active official SILG recurrent run under the immutable matched protocol. Only after policy competence, artifact integrity and trajectory eligibility pass may R0.2 proceed. No new architecture or RQ implementation is authorized before public baseline reproduction and preregistration.
