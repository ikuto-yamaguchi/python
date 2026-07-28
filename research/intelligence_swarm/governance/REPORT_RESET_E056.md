# RESET-E056 — Active entropy screening and C036 prior-art boundary

Date: 2026-07-26

## Scope

This integration stays on canonical branch `research/intelligence-swarm-reconstruction-001`.

- No new toy hypothesis.
- No new branch or stacked PR base.
- No new mechanism family.
- Existing stacked draft PRs remain a negative-results archive.
- Work is limited to public benchmark reproduction, prior-art audit, the frozen evaluation contract, and the rejected hidden intervention-target track.

## R0.1 execution status

R01-SCREEN-002 is running as GitHub Actions workflow run `30208660095` at head `3648f10c44ceab68891a08d5cf9ca174d739dd74`.

At the time of this audit:

- checkout: success
- Python setup: success
- immutable host provenance: success
- pinned SILG/RTFM installation: success
- generator schema verification: success
- canonical random control and schema probe: success
- official `multi` recurrent 131,072-frame training: in progress

The sole changed factor is `entropy_cost: 0.05 -> 0.005`. Architecture, source pins, frame budget, seeds `1/7/19`, split, actors, batch, unroll, and matched instances remain fixed.

No duplicate dispatch was issued while the identical screening was active. The iteration remains open until the run conclusion, artifact, qualification, matched controls, diagnostics, resources, checksums, and leakage results are inspected.

## Required post-run decision

The entropy-only explanation is rejected if Correct remains at zero success or does not exceed Random in win rate and return. Failure does not close the cycle. The next single-cause contract must then test official evaluation/default parity before recurrent/optimizer, learning-rate/gradient, capacity allocation, or fusion-position changes.

## Evaluation contract

D015–D035 remain frozen. No new auditor was added.

Every accepted or failed bundle must retain:

- Random / Language-blind / State-only / applicable shuffle controls
- identical instances
- model and checkpoint bytes
- peak RSS
- training runtime and CPU latency
- seed, split, and actual frames
- source/dependency/raw-log provenance
- predictions, statistics, and SHA-256 manifests
- answer/schema/prediction leakage findings
- action, entropy, valid-action, recurrent, gradient, and loss diagnostics

## Prior-art audit: C036

Liang et al., CVPR 2026, **Multimodal Causality-Driven Representation Learning for Generalizable Medical Image Segmentation**, introduces a VLM-based medical segmentation framework using text prompts to form a domain-confounder dictionary and a causal intervention network to suppress domain-specific variation while retaining anatomical structure.

The following are therefore treated as prior-art boundaries rather than RQ-001 novelty:

- text-defined confounder dictionaries
- multimodal causal intervention for representation learning
- removal of domain-specific confounding
- OOD segmentation generalization obtained from those interventions

This work is domain-generalized medical image segmentation, not a direct reproduction target for hidden intervention-target grounding or interactive policy competence. The primary CVPR paper is verified. Author-official code, exact commit, dependencies, dataset command, raw outputs, and immutable numerical reproduction remain unresolved.

## RQ-001 decision

RQ-001 remains narrowed and not adopted. Adoption still requires all applicable external baselines to be reproduced and a residual countermodel pair that is separated by language-specific information under an externally fixed, non-recodable denotation law, together with a preregistered claim, counterexample, and stopping rule.

## Formal status

- immutable R0.1 bundle: 1, failed qualification
- active entropy screening: in progress
- competent external baseline reproduction: 0
- J-CRe3 numerical reproduction: 0
- qualified R0.2: 0
- R0.3: rejected and retained closed
- novelty matrix: incomplete
- central proposition preregistration: incomplete
- new mechanism family: not recognized
- new intelligence principle: not found
- capability progress: not recognized
- high-school-level intelligence: not achieved
- next stage: not proposed
