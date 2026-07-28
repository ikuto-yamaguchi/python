# RESET-E014 — R0 integration

Date: 2026-07-25
Stage: R0 Research Reconstruction

## Scope

This integration consolidates the latest causal-identifiability decision and reproduction-contract hardening. It does not add a toy mechanism, model architecture, memory mechanism, hand-authored ontology, external LLM, RAG component or branch.

## Integrated evidence

### C007 — empirical Gate I closure

The audited public benchmarks do not jointly provide episode-aligned raw language, interactive trajectories, independently defined mechanism changes, held-out mechanism ground truth and permutation-aware evaluation.

Consequently:

- the empirical joint-identification claim RQ-001-N5 is rejected under the current public-benchmark and no-researcher-ontology constraints;
- hidden-intervention-target ablations on SILG are prohibited;
- adding target or mechanism labels to SILG would violate the reconstruction rules;
- RQ-001-T1 survives only as a theory-only candidate and is not adopted.

The closure is a benchmark and claim-qualification result, not a universal impossibility theorem.

### D011 — provenance and aggregate consistency

The SILG episode contract now additionally rejects:

- duplicate method/seed runs;
- invalid or missing wall time and CPU latency;
- run aggregates that cannot be reproduced from episode records;
- top-level aggregates that cannot be reproduced from runs;
- malformed checkpoint hashes or source pins;
- invalid model size, RSS or total wall time;
- missing explicit declarations that answer leakage and pretrained language models are absent.

Seven regression tests pass. The formal classification remains `initial_reproduction_failure` because Target-label shuffle or a formal non-oracle inapplicability record, Outcome shuffle, immutable test-data checksum and independent raw-log artifact joining remain absent.

## Current public reproduction status

- public environment control: reproduced;
- official recurrent training/checkpoint path: reproduced as staged engineering runs;
- fixed-initial-instance matched evaluation path: reproduced as an engineering smoke;
- learned public capability baseline: zero;
- formal R0.2 reproduction: zero;
- empirical R0.3/Gate I: formally rejected;
- J-CRe3 external Japanese audit: not reproduced.

The corrected 32,768-frame SILG workflow run `30120620610` is in progress at integration time. No unfinished result is incorporated.

## Decision

1. Continue R0 without stage transition.
2. Keep active mechanism families empty.
3. Keep all new toy mechanisms, memory work, stacked branches and R0.2 tuning frozen.
4. Make the corrected 32,768-frame artifact and competence/trajectory audit the only P0.
5. Close empirical Gate I and reject RQ-001-N5.
6. Keep RQ-001-T1 unadopted until formalization, novelty comparison and preregistration.
7. Do not recognize novelty, a new intelligence principle or capability progress.

## Stage-transition status

Blocked. A next stage still requires:

- at least one learned public capability baseline;
- immutable-instance random/language-blind/state-only/shuffle controls;
- complete three-seed provenance and leakage contract;
- qualified R0.2 online and typed-metric comparison;
- completed novelty matrix through relevant 2026 work;
- exactly one preregistered successor claim.

## Status

- High-school-level intelligence: not achieved
- Native Japanese communication: not achieved
- Weak-smartphone verification: not achieved
- Novelty: not established
- New intelligence principle: not discovered
- Capability progress: not recognized
- Completion: false
