# RESET-E022 — R0 Research Reconstruction integration

Date: 2026-07-25

## Scope

This integration keeps all active work on `research/intelligence-swarm-reconstruction-001`. No new toy mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, intervention ontology, stacked branch, or PR chain is introduced. Existing stacked drafts remain negative-results archives only.

## Integrated evidence

### R0.1 public benchmark reproduction

The latest accepted evidence remains the completed 32,768-frame SILG/RTFM official `multi` recurrent run for seeds `1,7,19` with no pretrained language model.

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total training wall time: `1,033.885 s`
- CPU forward: `6.911 ms/step`
- Correct: `1/60`, win rate `0.0167`
- Random: `4/60`, win rate `0.0667`
- Language-blind / State-only / Language-shuffle: each `0.0167`

Correct remains below Random. This is not a competent public capability reproduction.

At the pre-integration head `5dfa423808c2348a774eae1d64ddd8186cecf9be`, the connector found no associated workflow run or combined status. Therefore no 131,072-frame checkpoint, resource number, trajectory, or capability result is incorporated.

### R0.2 Environment-first baseline

Cycle 011 adds a matched typed comparison harness for:

- Environment-first
- parameter-matched End-to-end
- State-only

The harness requires identical typed data, seed and split, and exact Environment-first/End-to-end inference parameter-byte equality. It stores action accuracy, typed next-state loss, real entity/dynamics/language-form holdouts, independently produced online task success when present, CPU latency, training wall time, peak RSS, checkpoint bytes/hash and dataset hash. Offline accuracy is not substituted for task success.

The harness has not run on qualified public SILG trajectories because no competent three-seed source policy exists.

Classification: `matched_typed_offline_comparison_harness_implemented_execution_on_qualified_silg_data_blocked`.

### Evaluation contract

D018 closes a semantic-shuffle loophole. A structurally valid donor permutation is no longer sufficient.

- `target_label_shuffle` must apply `replace_gold_action_from_donor`.
- `outcome_shuffle` must apply `replace_gold_state_after_from_donor`.
- donor payload hash and applied payload hash must agree.
- assignment must remain inside the same seed/domain/split/condition cell.
- bijection, derangement and no self-shuffle remain mandatory.
- every cell must contain at least one actual semantic value change.

Four local regression tests passed. GitHub Actions completion is not claimed. Real semantic shuffle bundles, immutable test serialization, complete artifact joins and a competent baseline remain absent.

Classification remains `initial_reproduction_failure`.

### Prior-art and RQ-001

C015 adds Baumgartner et al., CLeaR 2026, to the novelty boundary. Under local transition-graph, sparsity, Jacobian-variation and graphical-separation assumptions, varying system parameters can be identified from trajectories without language or explicit intervention-target labels, up to permutation and element-wise diffeomorphism.

If the trajectory representation is transformed as `theta'_i = h_i(theta_(pi(i)))`, a language generator can be transformed jointly as `g'(theta',X,E,epsilon)=g(H^-1(theta'),X,E,epsilon)`, preserving `p(X,E,L)`. Consequently parameter naming, language-conditioned prediction, fluent descriptions and shuffle degradation do not by themselves remove the residual symmetry.

RQ-001 is narrowed to externally anchored symmetry breaking after general-environment, intervention-abstraction and trajectory-local identifiability criteria are exhausted. The candidate remains unadopted and requires a formal residual equivalence class, a non-jointly-transformable language anchor, a positive refinement theorem, a matched impossibility result without the anchor, anti-lookup grammar, unseen-form/composition/system evaluation, an estimator claim, public baseline reproduction and preregistration.

## Decision

- learned public capability baseline: `0`
- formal R0.2 reproduction: `0`
- R0.3 empirical track: rejected
- broad RQ-001: rejected
- externally anchored residual-symmetry formulation: narrowed, not adopted
- new architecture: forbidden
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved

## Single P0

Launch and finish exactly one clean 131,072-frame official recurrent run from the stable canonical workflow head. Verify three checkpoints, immutable matched controls, policy competence, action collapse, source/model/data/raw-log/prediction hashes, model bytes, RSS, wall time, CPU latency, seeds and splits before any R0.2 execution or successor claim.

## Stage transition

No next stage is proposed. Transition remains blocked until R0.1–R0.3 governance, novelty matrix through relevant 2026 primary work, complete evaluation artifacts, qualified R0.2 online metrics and exactly one preregistered successor claim are complete.
