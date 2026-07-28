# RESET-E031 — R0 Research Reconstruction Integration

Date: 2026-07-25

## Scope

This integration keeps all active work on `research/intelligence-swarm-reconstruction-001`. No new toy mechanism, memory/replay/fast-weights/sleep/forgetting path, architecture family, branch, or PR chain is introduced. Existing stacked drafts remain negative-results archives.

## 1. Primary literature and official-code boundary

C023 adds state-dependent local-dynamics identifiability: trajectory and local sparse dependency structure can identify changing system parameters without language under explicit assumptions. Naming those recovered parameters with language is not joint identification.

C024 adds isolated causal effects of natural language: the causal effect of a predefined linguistic attribute on an external outcome may be identifiable after non-focal-language adjustment, while raw utterance equivalence and a latent intervention-target partition remain non-identifiable. The official public implementation was located, but no reproduction is claimed in this integration.

RQ-001 is therefore further narrowed beyond non-language dynamics identifiability, interactive behavioural transfer, and isolated-language-effect estimation. It remains not adopted.

## 2. R0.1 reproduction

Accepted capability evidence has not changed: the 32,768-requested-frame official SILG `multi` recurrent run remains below Random (`1/60` versus `4/60`).

Run `30158106220` has completed host setup, pinned installation, generator-signature tests, and canonical random/schema probing. Its official 131,072-frame × 3 seed recurrent training step is in progress. No checkpoint, matched-control result, final artifact, or new capability value is accepted yet.

A workflow defect was identified: because the PR cumulative diff contains benchmark files, every unrelated PR synchronization could enqueue another five-hour reproduction. The workflow now starts only from benchmark-code/run-request pushes or manual dispatch. Governance and prior-art commits no longer enqueue duplicate runs. Active work is not cancelled.

## 3. Controls

Required immutable comparisons remain:

- Correct recurrent
- Random valid action
- Language-blind
- State-only
- within-environment language shuffle
- target-label shuffle only when a non-oracle label exists
- outcome/transition shuffle

No new matched-control result is accepted in this integration.

## 4. Resources, seeds and splits

Required reporting remains model bytes, peak RSS, training wall time, CPU inference latency, raw logs, full commit, checksums, canonical seeds `1,7,19`, and explicit train/test/domain/condition topology.

D026 adds fail-closed canonical seed/domain topology checks globally and within every observed `domain × split × condition` cell.

## 5. Leakage and evaluation contract

The unified contract covers utterance overlap, entity/dynamics split leakage, gold action/after-state leakage, completed-trajectory/post-treatment leakage, semantic aliases, prediction coverage, shuffle provenance, sparse cell topology, paired and episode-cluster statistics, and immutable resource/artifact binding.

No real R0 bundle has passed the contract. Formal classification remains `initial_reproduction_failure`.

## 6. RQ-001 decision

Decision: **NARROWED BEYOND LOCAL-DYNAMICS IDENTIFIABILITY AND ISOLATED LANGUAGE EFFECTS — NOT ADOPTED**.

Adoption still requires an explicit residual countermodel pair, an external non-recodable language anchor, strict joint-identification and impossibility results, a finite-sample or consistency guarantee, dependency-pinned public baseline reproduction, and exactly one preregistered successor claim with stopping rules.

## Stage decision

No next stage is proposed.

- R0.1 public capability baseline: not reproduced
- R0.2 formal reproduction: incomplete
- R0.3: rejected
- novelty matrix: incomplete
- central claim preregistration: incomplete
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
