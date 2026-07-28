# RESET-E030 — Verified R0 Research Reconstruction integration

Date: 2026-07-25
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope guard

- No new toy mechanism, operation/goal hypothesis, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, branch, or PR chain was created.
- Existing stacked draft PRs remain negative-results archives and are not active bases.
- Only public benchmark reproduction, prior-art boundary, evaluation qualification, and the rejected hidden intervention-target track are integrated.

## 1. Latest primary-work and official-code overlap boundary

C022 adds the behavioural-interactive-transfer boundary: OpenLock-style prospective causal transfer can evaluate action efficiency and transfer, but identical interaction policies and outcomes do not uniquely identify raw-language equivalence classes or an internal latent intervention-target partition. The surviving RQ must condition on the full interaction history and still demonstrate a strict reduction of a residual causal equivalence class through a non-recodable external language anchor.

A fresh 2026 primary-work check also identified Markham et al., *Intervening to learn and compose causally disentangled representations* (CLeaR 2026). It learns causally disentangled and compositional representations using supplied concept/context information and proves an identifiability result for that setting. Therefore concept-conditioned compositional disentanglement, intervention-like context modules, and out-of-distribution concept composition are not admissible novelty claims for RQ-001. This work does not establish joint identification of raw utterance equivalence and unknown latent intervention-target partitions, so it narrows rather than resolves the candidate RQ.

No new architecture is authorised from this audit.

## 2. R0.1 public reproduction

Verified accepted evidence remains the completed 32,768-requested-frame SILG/RTFM official `multi` recurrent path for seeds `1,7,19`:

- parameters: `4,916,915`
- state-dict audit: `19,694,385 bytes`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167` (`1/60`)
- Random win rate: `0.0667` (`4/60`)
- Language-blind / State-only / Language-shuffle: each `0.0167`

Correct remains below Random. This is an incompetent-policy result, not public capability reproduction and not evidence of language irrelevance.

At the verified pre-integration head `830b1d13b39f9ab450271a1cf286aeee7f38bf25`, no completed 131,072-frame artifact or registered combined status was available. Workflow edits, trigger files, and run requests are not capability progress.

## 3. R0.2 Environment-first

Verified infrastructure remains:

- Gaddy & Klein faithful typed Environment-first path
- parameter-matched End-to-end and State-only paths
- pinned-generator signature export
- typed trajectory export
- offline next-state/action comparison
- online same-initial-instance evaluator implementation

Formal execution remains unqualified because the generator-side signature sidecar is not immutably joined to the typed trajectory in the verified branch state, the holdout auditor therefore cannot certify the real dynamics split, the online evaluator is not verified as executed, and no competent qualified R0.1 source-policy trajectory exists.

RTFM S1 supports a real dynamics split only. Entity and language-form transfer are formally inapplicable on S1 and must not be fabricated.

## 4. Controls, statistics, resources, and leakage

Required matched methods remain Correct, Random, Language-blind, State-only, within-environment language shuffle, and transition/outcome shuffle. Target-label shuffle is only applicable when a non-oracle target label exists; otherwise a formal inapplicability record is required.

D016–D025 jointly require immutable prediction/data/model/log joins, exact seeds `1,7,19`, identical observed `domain × split × condition` topology for every method, shuffle donor provenance and derangement, gold action/after-state and completed-trajectory leakage rejection, semantic alias rejection, prediction coverage, paired cell statistics, episode-cluster bootstrap/sign-flip statistics, model bytes, peak RSS, training wall time, CPU latency, raw logs, full commit IDs, and checksums.

No real R0 bundle has passed the complete contract. Classification remains `initial_reproduction_failure`.

## 5. RQ-001 decision

Broad RQ-001 remains rejected. The only surviving candidate is further narrowed to:

> After conditioning on the strongest applicable non-language estimator and the complete prospective interaction history, can an externally fixed, non-recodable population language contrast supply a missing separation that strictly reduces a residual causal equivalence class and jointly identifies raw-utterance equivalence with a refined intervention-target partition, with finite-sample or consistency guarantees?

Status: **not adopted**.

Adoption still requires an explicit residual countermodel pair, positive-measure language-law separation, an anti-recoding external anchor, a strict equivalence-class-reduction theorem, an anchor-removal impossibility result, a finite-sample/consistent estimator, direct non-language and behavioural-transfer baselines, unseen form/composition/target/system splits, public baseline reproduction, and exactly one preregistered claim with a stopping rule.

## 6. Stage decision

No next stage is proposed.

- R0.1 competent external baseline: absent
- R0.2 qualified online comparison: absent
- R0.3: rejected
- novelty matrix: open
- central preregistered proposition: absent
- new intelligence principle: none
- capability progress: not recognised
- high-school-level intelligence: not achieved
- completion: false
