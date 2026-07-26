# RESET-E043 — R0 Research Reconstruction

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This iteration preserves one canonical reconstruction branch and does not authorize new toy hypotheses, mechanism families, or stacked branches. Existing stacked draft PRs remain a negative-results archive and are not used as the base for new work.

Allowed accumulation remains limited to:

- public benchmark reproduction;
- prior-art and official-code overlap audit;
- frozen evaluation contract application;
- hidden intervention-target ablation status.

## Change in research operation

A failed experiment may not terminate an iteration by itself. A failed run is incomplete until all of the following are recorded:

1. failure class;
2. evidence-backed root-cause candidate;
3. one-variable minimal correction;
4. same-budget rerun;
5. improvement, refutation, or preregistered stopping decision.

Every failed iteration must also define the next run's changed variable, fixed variables, falsification condition, and stopping condition. Documentation-only completion is prohibited.

## Primary literature and official-code overlap audit

### SILG / RTFM

The 2021 SILG primary paper and official benchmark implementation remain the canonical public reference. This iteration found no verified official successor that replaces the current SILG/RTFM reproduction target.

### J-CRe3

The following public references are now fixed:

- Ueda et al., J-CRe3, LREC-COLING 2024;
- peer-reviewed Journal of Natural Language Processing 2024 version;
- official repository `riken-grp/J-CRe3`.

J-CRe3 is a Japanese real-world multimodal reference-resolution benchmark. It does not replace SILG interactive policy competence. The two are maintained as separate external baselines.

Exact repository commit, dataset checksum, official evaluation command, dependency lock, and immutable numerical reproduction remain incomplete.

## Reproduction status

- SILG public environment control: 1
- immutable 131,072-frame R0.1 competence bundle: 0
- learned public capability baseline: 0
- J-CRe3 numerical baseline reproduction: 0
- qualified R0.2 result: 0
- real bundle passing the frozen evaluation contract: 0

The existing 32,768-frame SILG evidence remains:

- parameters: 4,916,915
- state-dict: 19,694,385 bytes
- maximum RSS: 505,600 KiB
- three-seed training wall time: 1,033.885 s
- CPU forward: 6.911 ms/step
- Correct: 1/60
- Random: 4/60
- Language-blind / State-only / Language-shuffle: 1/60 each

This is policy incompetence, not public-baseline reproduction.

## Controls and provenance

Every accepted run must preserve:

- random, language-blind, state-only, and applicable shuffle controls;
- identical initial instances;
- model and checkpoint bytes;
- peak RSS;
- training runtime and CPU latency;
- seed, split, and actual frame count;
- exact config and commit;
- raw logs and checksums;
- leakage findings.

For J-CRe3, applicable controls are to be preregistered as random, text-only, vision-only, mention-shuffle, and frame/object-shuffle without changing the task definition.

## Evaluation contract

D015–D035 remain frozen. No new auditor is authorized unless a preserved real bundle exposes a concrete false pass or false failure. Audit CI, queued runs, document updates, and workflow edits are not capability progress.

## R0.3

The hidden intervention-target empirical track remains rejected because SILG/RTFM lacks ground-truth latent intervention families, targets, mechanism operators, and causal abstractions. No researcher-authored ontology is authorized to reopen it.

## RQ-001 decision

- broad RQ-001: rejected;
- narrow RQ-001: narrowed and not adopted.

Adoption still requires the strongest applicable non-language baseline reproduction, a residual countermodel pair, an externally fixed anti-recoding law, and exactly one preregistered claim/counterexample/stopping rule.

## Stage transition

No next stage is proposed. Transition remains blocked until all of R0.1–R0.3 status requirements, the novelty matrix, and the central-claim preregistration are complete.

## Formal status

- evaluation class: `initial_reproduction_failure`
- new mechanism family: not recognized
- new intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
