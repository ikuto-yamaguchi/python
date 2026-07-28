# RESET-E029 — R0 Research Reconstruction Integration

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`
Stage: R0 public capability reproduction and benchmark qualification

## Decision

Continue R0 on the single canonical branch. Do not authorise new toy mechanisms, operation/goal hypotheses, memory/replay/fast-weights/sleep/forgetting work, researcher-created intervention ontologies, architecture families, or stacked PR chains.

Existing stacked drafts remain negative-results archives and are not valid experiment bases.

## Evidence integrated since RESET-E028

### 1. R0.1 public capability reproduction

No new accepted capability evidence exists.

Accepted evidence remains the official SILG `multi` recurrent staged run at 32,768 requested frames for seeds `1,7,19`:

- parameters: `4,916,915`
- state-dict audit: `19,694,385 bytes`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct: `1/60` wins (`0.0167`)
- Random: `4/60` wins (`0.0667`)
- Language-blind / State-only / Language-shuffle: each `1/60`

Correct remains below Random. The policy is not competent and the result is not evidence that language is unnecessary.

The current canonical head has no registered combined status and no verified completed 131,072-frame artifact, checkpoint bundle, or new performance result. Workflow edits and run requests are not capability progress.

### 2. R0.2 Environment-first baseline

The following non-novel baseline infrastructure now exists:

- Gaddy & Klein-faithful typed Environment-first baseline
- parameter-matched End-to-end and State-only controls
- typed SILG trajectory export
- pinned-generator signature export
- online SILG evaluator for equal initial-instance streams
- model/checkpoint bytes, RSS, wall time, CPU inference, raw-log and checksum fields

The generator signature exporter derives episode metadata before observing action outcomes or completed trajectories. The pinned RTFM S1 split supports a real **dynamics** holdout through train/dev assignment separation.

RTFM S1 does not separate the entity ontology or language-generation family. Therefore it cannot support real entity or language-form transfer claims. These conditions must be recorded as formally inapplicable for S1, not fabricated.

The formal R0.2 reproduction remains incomplete because:

1. generator signature sidecars are not immutably joined to typed trajectories;
2. the holdout auditor still receives unjoined trajectory rows;
3. the online SILG evaluator is implemented but not invoked by the canonical workflow;
4. no competent qualified R0.1 source-policy trajectory exists;
5. no three-seed online task-success, typed next-state, action-accuracy or real dynamics-transfer result exists.

Classification:

`generator_signature_and_online_evaluator_implemented_but_join_execution_and_qualified_source_policy_absent`

### 3. Evaluation contract

D024 remains the end-to-end immutable bundle gate: dataset contract, semantic alias/value leakage, artifact integrity, exact prediction coverage, shuffle provenance, paired statistics and episode-cluster statistics execute together.

The post-D024 correction integrated here is designated **D025**:

- derive the evaluation topology from observed `domain × split × condition` combinations;
- require the exact same topology for every method and seed;
- do not demand nonexistent Cartesian-product cells;
- continue rejecting method-specific or seed-specific omissions.

This removes false failures for valid sparse designs without weakening coverage requirements.

No real R0 bundle has passed D016–D025.

Formal classification remains:

`initial_reproduction_failure`

### 4. Prior-art and RQ-001 boundary

C021 added Lee, Jin, and Aragam 2026, `Beyond identifiability: Learning causal representations with few environments and finite samples` (`arXiv:2603.25796`). In a meaningful linear class with unknown mixing, unknown latent SEM and unknown multi-node intervention targets, strongly separating environments permit finite-sample recovery of the graph, representation, decoder and targets with logarithmically many environments.

Therefore the following are not admissible novelty claims in that class:

- unknown multi-node target recovery requires language;
- many individually targeted environments are necessary;
- target names or descriptions create identifiability;
- language that restates a recoverable intervention-incidence signature shrinks the causal equivalence class.

The latest adjacent 2026 primary-work check also records:

- `LeGIT: LLM Guided Intervention Targeting for Online Causal Discovery`: uses LLM knowledge to choose interventions; it does not jointly identify raw-language equivalence and a latent intervention partition.
- `Sequential Causal Discovery with Noisy Language Model Priors`: integrates noisy LM expert knowledge into sequential PAG discovery; it is not latent intervention-partition identification.
- `Coarsening Causal DAG Models`: learns causal abstractions from unknown-target interventional data over a partition-refinement lattice; it strengthens the non-language abstraction/refinement baseline that must be exhausted first.

The surviving RQ is narrowed to:

> After applying the strongest applicable non-language estimator, can an externally fixed language contrast that is not recoverable from environment identity, intervention incidence, observations, actions, outcomes or completed trajectories supply a missing separation and jointly identify raw-utterance equivalence with a residual intervention-target partition, with an estimator and finite-sample guarantee?

Decision: **not adopted**.

Adoption still requires an explicit residual countermodel, positive-measure language-law separation, anti-recoding anchor, strict equivalence-class reduction theorem, impossibility result when the contrast is removed, finite-sample estimator, direct separating/non-separating comparisons, unseen-form/composition/target/system splits, public baseline reproduction, and exactly one preregistered claim.

### 5. R0.3 and hidden intervention-target ablation

R0.3 remains rejected. SILG/RTFM does not expose a ground-truth latent intervention family, target partition, mechanism operator or causal abstraction. No researcher-authored ontology may be added to manufacture the target.

## Single P0

Finish and verify exactly one clean 131,072-frame official recurrent run from a stable canonical head. Require all three checkpoints, matched immutable controls, policy competence, action-collapse audit, source/model/data/raw-log/prediction checksums, model bytes, RSS, training wall time, CPU inference latency, seeds and splits.

Until this passes:

- do not tune R0.2 on failed-policy trajectories;
- do not implement RQ-001;
- do not create a new architecture family;
- do not claim novelty, an intelligence principle or capability progress.

## Stage transition

Do not propose the next stage until all exist:

1. at least one competent learned external public capability baseline;
2. immutable random/language-blind/state-only/shuffle controls;
3. complete three-seed prediction/artifact/leakage qualification;
4. qualified R0.2 online comparison with real dynamics holdout and a valid boundary for entity/language-form transfer;
5. retained R0.3 rejection;
6. novelty matrix closed through relevant 2026 primary work and official code;
7. exactly one preregistered successor claim with theorem, counterexample and stopping rule.

## Formal status

- public capability baseline: not reproduced
- verified 131,072-frame artifact: none
- R0.2 formal reproduction: incomplete
- R0.3: rejected
- broad RQ-001: rejected
- narrow RQ: not adopted
- evaluation: `initial_reproduction_failure`
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognised
- high-school-level intelligence: not achieved
- completion: false
