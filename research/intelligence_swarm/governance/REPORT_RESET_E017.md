# RESET-E017 — R0 Research Reconstruction Integration

Date: 2026-07-25

## Decision

Continue **R0 Research Reconstruction** without a stage transition. Do not create a new toy hypothesis, mechanism family, memory mechanism, branch, or PR chain. Continue accumulating only public benchmark reproduction, prior-art audit, evaluation-contract enforcement, and the formally permitted negative/identifiability analyses on the canonical branch.

## 1. Public benchmark reproduction

The latest incorporated completed capability evidence remains the corrected SILG/RTFM `32,768 frames/seed` run for seeds `1,7,19`.

- official SILG `multi` recurrent;
- no pretrained language model;
- parameters: `4,916,915`;
- maximum RSS: `505,600 KiB`;
- total three-seed training wall time: `1,033.885 s`;
- CPU forward audit: `6.911 ms/step`;
- Correct win rate: `0.0167`;
- Random win rate: `0.0667`;
- Language-blind, State-only, Language-shuffle win rates: `0.0167` each;
- all initial-instance fingerprint streams matched.

This is a reproduced training/evaluation path, not a reproduced public capability baseline.

The first `131,072 frames/seed` attempt was stopped by the reconstruction harness's fixed 1,200-second subprocess timeout, not by a model exception. The timeout was changed to a frame-scaled limit while preserving the official model, data, split, seed, schema, optimizer and loss. Corrected workflow run `30129717438` is currently in progress in the official recurrent training step. No unfinished capability or resource values are incorporated.

## 2. R0.2 Environment-first status

R0.2 remains blocked by source-policy competence and trajectory eligibility. The old public trajectories remain comparison-ineligible because of zero/near-zero success and action collapse. The current implementation remains a continuous two-stage adaptation rather than a faithful reproduction of the Gaddy & Klein structured discrete-message default, and its flat mixed-type state MSE remains invalid as a formal next-state metric.

No Environment-first tuning is authorized until every source-policy seed passes the preregistered anti-collapse and success gates.

## 3. Evaluation contract integration

Integrate D014.

The required scoring and artifact cell is now:

`method × seed × domain × split × condition`

The contract now requires:

- split-preserving score cells;
- condition-indexed artifact runs;
- complete Cartesian prediction and artifact coverage;
- cluster bootstrap over `seed × domain × split × condition`;
- existing utterance, entity, dynamics, gold-action, after-state, reward, done and completed-trajectory leakage checks;
- immutable instance fingerprints;
- shuffle donor provenance and fixed-point-free within-cell derangements;
- full source/model/data/log hashes and readable artifacts;
- model bytes, RSS, training time and CPU latency audits.

Fifteen regression tests pass. The strict classification remains `initial_reproduction_failure` because real target-label/outcome-shuffle outputs, immutable test serialization, complete artifact joins, and a competent public baseline are still absent.

## 4. Prior-art and RQ-001 integration

Integrate C010.

The attempted positive construction based on utterance pairing, grouping or relation labels does not establish a new raw-language identifiability result. When such relations come from paraphrase, target, factor, class, graph or semantic-equivalence labels, the identifying information is weak supervision. When they are used as auxiliary indices, contrastive pair labels or a second view, the construction remains within existing auxiliary-variable nonlinear ICA, grouping-based CRL, multi-view ICA, weak supervision or mechanism-sparsity boundaries.

RQ-001-T1 is therefore narrowed to a final theory test and remains **not adopted**:

> Determine whether observable formal/relational structure among raw utterances, without oracle paraphrase, target, environment, group or graph labels, can remove a causal-model symmetry that remains after conditioning on complete non-language trajectories and quotienting out every finite auxiliary index.

Current status:

- empirical Gate I: rejected;
- RQ-001-N5: rejected;
- RQ-001-T1: narrowed, not adopted;
- negative construction: present;
- first positive construction: rejected as weak supervision/grouping/auxiliary-view reduction;
- nontrivial positive construction: absent;
- sufficient-condition theorem: absent;
- implementation authorization: none.

## 5. Stage transition

Do not propose the next stage. R0.1 public capability reproduction, R0.2 matched online reproduction with typed metrics and real holdouts, full novelty matrix, and exactly one preregistered central claim are not complete.

## Single P0

Complete and verify corrected workflow run `30129717438`. Apply the same immutable matched protocol and full artifact/leakage contract. If competence remains absent, modify only a verified official reproduction-condition mismatch or classify resource/budget insufficiency at the preregistered ceiling.

## Status

- learned external public capability baseline: **0**;
- R0.2 formal reproduction: **0**;
- novelty: **not established**;
- capability progress: **not recognized**;
- new intelligence principle: **not discovered**;
- high-school-level intelligence: **not achieved**;
- completion: **false**.
