# RESET-E041 — R0 Research Reconstruction Integration

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

This integration keeps the canonical reconstruction branch as the only active work base. It adds no toy mechanism, operation/goal hypothesis, memory, replay, fast weights, sleep, forgetting, architecture family, branch, or stacked PR chain. Existing stacked drafts remain negative-results archives.

## 1. Latest primary literature and official-code overlap audit

C034 is integrated.

Varıcı et al., *Score-based Causal Representation Learning: Linear and General Transformations* (JMLR 2025), gives constructive score-based identifiability results for latent causal variables, DAG structure, and intervention targets under explicit assumptions. Relevant cases include one stochastic hard intervention per node for linear observation transformations and two distinct stochastic hard interventions per node for general nonlinear transformations, without requiring the learner to know which environments target the same node.

The JMLR page links the author-controlled consolidated repository `acarturk-e/score-based-crl`, covering LSCALE-I, GSCALE-I, and UMNI-CRL families. The repository is verified as official public code, but no immutable R0 reproduction has been performed. An exact commit, environment, selected command, raw output, and checksums remain required.

Novelty boundary:

- unknown environment-to-target correspondence alone does not require language;
- general nonlinear observation maps alone do not require language;
- score/density differences can identify causal variables and targets under explicit assumptions;
- naming a recovered node, target, or environment does not establish raw-language equivalence or semantic joint identification.

RQ-001 is narrowed to a residual partition that remains after the strongest applicable score-based CRL quotient and that can be separated only by a preregistered, externally fixed, non-recodable denotation law.

Decision:

> **NARROWED BEYOND SCORE-BASED IDENTIFIABILITY AND ACHIEVABILITY — NOT ADOPTED**

## 2. SILG / J-CRe3 reproduction progress

No new accepted public capability result exists.

- immutable 131,072-frame R0.1 bundle: 0
- accepted learned public capability baseline: 0
- formal R0.2 reproduction: 0
- J-CRe3 reproduction: not completed

Run `30158106220` remains non-acceptable evidence: three-seed training and matched controls ran, but the downstream failure occurred before artifact upload and the artifact count was zero.

## 3. Matched controls

The required registry remains:

- Correct
- Random
- Language-blind
- State-only
- Target-label shuffle
- Outcome shuffle

All methods must use identical evaluation instances and the same observed sparse `domain × seed × split × condition` topology. No new real bundle has passed this requirement.

## 4. Resource and provenance requirements

No new accepted values were added. Every accepted run must preserve:

- model/checkpoint bytes;
- peak RSS;
- training wall time;
- CPU inference latency;
- seeds `1,7,19`;
- split and condition;
- raw logs;
- source, model, data, prediction, and statistics checksums.

## 5. Leakage and evaluation contract

D035 is integrated.

The alias-normalized leakage auditor already rejected variants such as `goldStateAfter`, `gold-action`, `completedTrajectory`, `terminalObservation`, and `episodeReturn`. The defect was that the official unified acceptance command did not require that auditor.

`audit_r0_acceptance_bundle.py` now invokes, in one fail-closed path:

1. dataset/evaluation contract;
2. alias-normalized schema leakage audit;
3. prediction payload leakage audit;
4. paired statistics and same-instance coverage;
5. model/data/raw-log/resource audit;
6. prediction/statistics checksum audit.

Any component failure preserves the component errors and classifies the bundle as `initial_reproduction_failure`.

Current-head regression runs:

- unified acceptance gate `30179464716`: success;
- prediction method topology `30179464653`: success.

These are audit-code tests only. Real accepted R0 bundles remain zero.

## 6. RQ-001 adoption, narrowing, or rejection conditions

Broad RQ-001 remains rejected. The narrowed RQ remains not adopted.

Adoption still requires all of the following before architecture work:

1. mapping SILG episodes to observational/interventional environments;
2. explicit audit of hard/soft, single/multi-node, score-estimation, smoothness, invertibility, and intervention-diversity assumptions;
3. immutable reproduction of the strongest applicable official score-based baseline;
4. a concrete countermodel pair that remains indistinguishable after score-based recovery;
5. language information unavailable from environment identity, states, actions, rewards, outcomes, scores, targets, and completed trajectories;
6. an external denotation anchor fixed before fitting;
7. proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
8. direct residual-partition and utterance-class recovery metrics;
9. preregistration of exactly one claim, counterexample, and stopping rule.

## Stage decision

No next stage is proposed. R0.1–R0.3, the novelty matrix, and the central preregistration are incomplete.

## Formal status

- evaluation classification: `initial_reproduction_failure`
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
