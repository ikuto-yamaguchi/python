# RESET-E023 — R0 Research Reconstruction Integration

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This integration keeps one canonical active branch and accumulates only public benchmark reproduction, prior-art audit, evaluation qualification, and the already-closed hidden intervention-target track. It adds no toy mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, researcher-authored intervention ontology, or stacked PR chain. Existing stacked drafts remain negative-results archives and are not used as bases.

## 1. Primary literature and official-code boundary

C016 audited Lin, Morency and Ben-Michael, **Isolated Causal Effects of Natural Language** (ICML 2025), together with the official `torylin/isolated-text-effects` implementation.

The work identifies the effect of a predefined focal language intervention on an external outcome under fidelity, overlap and confounding-control assumptions. It does not recover raw-language equivalence classes or an unknown latent intervention-target partition. A non-zero, well-estimated language effect therefore does not imply latent partition identification.

The surviving RQ-001 candidate is narrowed to an externally anchored, injective family of language effects that strictly separates a formally specified residual causal abstraction after the strongest non-language criteria have been exhausted. It remains unadopted. A bridge theorem, exclusion, injectivity/separation, per-cell fidelity and overlap, anti-recoding assumptions, impossibility results, unseen-form/composition/system evaluation, public baseline reproduction and preregistration remain mandatory.

## 2. R0.1 public benchmark status

Accepted evidence remains the official SILG/RTFM `multi` recurrent path at 32,768 requested frames for seeds `1,7,19`, with no pretrained language model.

- parameters: `4,916,915`
- state-dict audit: `19,694,385 bytes`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind / State-only / Language-shuffle: each `0.0167`

Correct remains below Random, so this is not a reproduced public capability baseline. At canonical head `4020516ec26920a2ea664626346458dfe5b57e56`, no combined status or verified completed 131,072-frame artifact is present. Unfinished, cancelled and duplicate runs remain excluded.

The single R0.1 P0 remains: finish exactly one clean 131,072-frame official recurrent run and verify all three checkpoints, immutable matched controls, policy competence, action collapse, source/model/data/raw-log/prediction hashes, model bytes, RSS, wall time, CPU latency, seeds and splits.

## 3. R0.2 Environment-first baseline

Cycle 012 added a fail-closed matched-budget auditor for Environment-first, End-to-end and State-only.

It requires:

- canonical seed `1`, `7`, or `19`;
- non-empty train and test splits;
- immutable dataset SHA-256;
- identical total training-row exposure;
- exact Environment-first versus End-to-end inference-parameter-byte equality;
- separate accounting for transition-pretraining-only parameters;
- complete test prediction coverage;
- action accuracy and typed next-state loss;
- CPU inference latency, training wall-time components and peak RSS;
- checkpoint bytes and SHA-256.

For `N` train rows, environment epochs `E` and language epochs `L`, exposure is fixed as `N*E + N*L` for Environment-first and `N*(E+L)` for both End-to-end and State-only. Offline metrics are never substituted for independently generated online task success.

No qualified three-seed SILG trajectory bundle exists because R0.1 has not produced a competent source policy. Classification remains `matched_data_and_resource_audit_implemented_qualified_silg_execution_blocked`.

## 4. Evaluation contract and leakage

D019 added condition-scoped holdout integrity checks. Entity and dynamics leakage is now judged per `domain × split × condition × kind`, rather than from a split-wide union.

The auditor:

- compares each holdout cell against same-domain training signatures;
- allows expected training overlap in explicitly in-distribution cells;
- rejects missing entity/dynamics signatures;
- requires seeds `1,7,19` in every holdout cell;
- records overlap counts and hashed signature examples;
- fails closed on overlap, missing/extra seed, missing signature or absent training reference.

This prevents in-distribution rows sharing a test split from causing false holdout failures and identifies the exact leaking cell. The real R0 data/prediction/artifact bundle has not passed this audit. D016 prediction joins, D017 cell seed coverage, D018 semantic shuffle payload provenance and D019 holdout integrity therefore remain qualification requirements.

Formal evaluation classification remains `initial_reproduction_failure`.

## 5. RQ-001 decision

- broad/current RQ-001: rejected;
- unknown-target recovery, environment-label recovery, parameter naming and non-zero language effects as language-specific causal-identification evidence: rejected;
- empirical hidden intervention-target track / R0.3: rejected;
- surviving formulation: externally anchored, fidelity/overlap-verified and injective language-effect separation of a formally stated residual causal abstraction;
- adoption: not authorised; preregistration candidate only.

No implementation or architecture is authorised from C016.

## 6. Stage decision

No next stage is proposed. Transition remains blocked until all of the following exist:

1. at least one learned external public capability baseline;
2. immutable-instance random/language-blind/state-only/shuffle controls;
3. complete canonical three-seed prediction/artifact/leakage qualification;
4. qualified R0.2 online task-success comparison with typed next-state metrics and real entity/dynamics/language-form holdouts;
5. retained formal R0.3 rejection;
6. novelty matrix closed through relevant 2026 primary work;
7. exactly one preregistered successor claim with theorem/counterexample and stopping rule.

## Status

- public capability baseline: not reproduced
- R0.2 formal reproduction: incomplete
- evaluation qualification: `initial_reproduction_failure`
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
