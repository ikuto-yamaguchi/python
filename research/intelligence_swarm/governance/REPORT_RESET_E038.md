# R0 Research Reconstruction — RESET-E038

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

This integration adds no toy mechanism, operation/goal hypothesis, memory, replay, fast weights, sleep, forgetting, architecture family, branch, or stacked PR. Existing stacked drafts remain negative-results archives and are not used as the base of new work.

The only cumulative tracks remain:

1. public benchmark reproduction;
2. primary-source and official-code prior-art audit;
3. evaluation/statistics/leakage qualification;
4. the retained rejection of an unsupported hidden intervention-target empirical track.

## 1. Primary literature and official-code overlap audit

C031 audits Chen et al., *Test-Time Learning of Causal Structure from Interventional Data* (ICML 2026 / arXiv:2602.19131).

Under causal sufficiency, Markovness/faithfulness, context exogeneity, complete randomized context, and generic-context assumptions, the work jointly infers an interventional graph equivalence-class representation and unknown intervention families from environment-indexed interventional data without language.

This removes the following from the novelty space:

- unknown intervention targets alone require language;
- test-time adaptation to intervention environments is a language-grounding principle;
- target-detection accuracy identifies raw-utterance equivalence;
- naming a JCI context or detected target supplies new identifiability when it only repeats the existing context statistic.

A paper-specific immutable official repository with pinned dependencies and reproduction commands was not verified. No public baseline experiment was started from this paper.

RQ-001 is therefore narrowed again to a residual partition not recoverable from the strongest non-language graph/context/target sufficient statistic, plus an externally fixed language law that removes every joint relabeling of target blocks, utterance classes, and context labels. It remains **not adopted**.

## 2. SILG / RTFM / J-CRe3 reproduction status

No new immutable R0.1 capability bundle has appeared.

The only 131,072-requested-frame run evidence remains run `30158106220`: fixed SILG/RTFM install, schema/random probe, official recurrent training for seeds `1,7,19`, and matched Correct/Random/Language-blind/State-only/Language-shuffle steps succeeded, but downstream R0.2 failure occurred before dependency freeze and artifact upload. Workflow artifacts were empty.

Therefore no checkpoint, performance value, model bytes, peak RSS, training wall time, CPU inference latency, raw log, or checksum from that run is accepted.

J-CRe3 remains unreproduced.

## 3. Controls and statistics

The canonical required method topology remains exactly:

- Correct;
- Random;
- Language-blind;
- State-only;
- Target-label shuffle;
- Outcome shuffle.

D032 adds one unified fail-closed acceptance command. A bundle is valid only when the same invocation passes:

1. dataset/schema and train/evaluation leakage contract;
2. prediction-payload leakage and valid-action contract;
3. same-instance paired statistics contract;
4. model/data/raw-log resource artifact contract;
5. prediction/statistics checksum and validity contract.

Any failed component classifies the whole bundle as `initial_reproduction_failure`, while preserving all component errors.

CI run `30173560733` passed for the unified acceptance-gate regression tests. Run `30173560729` passed the prediction-method-topology tests. These are audit-code regression results only. No real benchmark bundle has passed D015–D032.

## 4. Model, RSS, runtime, seed, and split

The canonical experiment requirements remain:

- seeds exactly `1,7,19` globally and in every observed evaluation cell;
- identical instances across all controls;
- immutable code/data/model/prediction/statistics/raw-log hashes;
- model bytes;
- peak RSS;
- training wall time;
- CPU inference latency;
- explicit domain, split, and condition;
- actual frame counters and checkpoint integrity.

No new accepted resource value was produced in this integration.

## 5. Leakage and provenance

D032 prevents partial qualification. A caller can no longer claim success from paired statistics while omitting prediction-payload leakage checks, or claim valid resources while using mutable prediction/statistics artifacts.

The existing checks remain in force: train/test utterance overlap, entity/dynamics leakage, gold action/after-state, reward/outcome/completed-trajectory/post-treatment leakage, semantic aliases, prediction coverage, same-instance topology, shuffle provenance and derangement, code/data identity, finite values, and checksums.

## 6. R0.2 fidelity status

The Gaddy–Klein author-code revision remains pinned to `kristyelee/environment-learning@98c0dc68926ee9535f15019922d2ca871b0ac0b5`.

A machine-audited component mapping now verifies the declared public-code-to-SILG transfer, including:

- before/after-state transition encoding;
- discrete Gumbel message construction;
- message-conditioned next-state/action decoding;
- recurrent language-to-message encoding;
- environment pretraining before language training;
- transition/decoder freezing during language training;
- End-to-end and State-only controls;
- Environment-first versus End-to-end inference-budget equality;
- same-instance online task evaluation and resource logging;
- RTFM S1 dynamics-only holdout boundary.

This closes the component-mapping-validator gap. It does not create a reproduction result. Native author-task execution, the language-data-efficiency curve, an immutable R0.1 source artifact, and qualified three-seed dynamics-holdout results remain missing.

## Formal decision

- R0.1 immutable 131,072-frame bundle: **0**
- accepted learned public capability baseline: **0**
- R0.2 formal reproduction: **0**
- real R0 bundle passing D015–D032: **0**
- R0.3 hidden intervention-target empirical track: **rejected**
- broad RQ-001: **rejected**
- narrowed RQ-001: **further narrowed, not adopted**
- novelty matrix: **incomplete**
- central proposition preregistration: **incomplete**
- evaluation classification: **`initial_reproduction_failure`**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
