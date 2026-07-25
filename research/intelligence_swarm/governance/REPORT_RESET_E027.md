# RESET-E027 — R0 Research Reconstruction integration

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This integration adds no toy hypothesis, operation/goal mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, intervention ontology, branch, or PR chain. Existing stacked drafts remain negative-results archives only.

## Evidence checked

### R0.1 SILG/RTFM

Pinned evidence remains SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`, RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`, official `multi` recurrent, no pretrained language model, train `silg:rtfm_train_s1-v0`, test `silg:rtfm_test_s1-v0`, seeds `1/7/19`.

Accepted completed evidence remains the 32,768-requested-frame run:

- parameters: 4,916,915
- state-dict audit: 19,694,385 bytes
- maximum RSS: 505,600 KiB
- total three-seed training time: 1,033.885 s
- CPU forward audit: 6.911 ms/step
- Correct: 1/60 wins
- Random: 4/60 wins
- Language-blind / State-only / Language-shuffle: 1/60 each

Correct remains below Random. No verified completed 131,072-frame artifact or competent learned public baseline was found at the integration head. The current head has no registered combined commit status. Workflow-trigger edits and execution-path edits are not counted as capability progress.

### R0.2 Environment-first

The canonical R0.1 workflow now connects typed SILG trajectory export to the Gaddy-and-Klein-style typed comparison path and runs Environment-first, parameter-matched End-to-end, and State-only with seeds `1/7/19`, equal episode exposure and fixed epoch budgets. It records typed comparison outputs and runs the entity/dynamics/language-form holdout auditor.

This is execution-path integration only. The pinned RTFM generator still does not emit preregistered `entity_signature`, `dynamics_signature`, and `language_form_signature` sidecars, and no competent R0.1 source trajectories exist. Therefore online task success, typed next-state prediction, action accuracy, and genuine held-out transfer remain unqualified and unmeasured.

### Evaluation contract D023

D023 makes the semantic model-input leakage auditor mandatory in the canonical evaluation CI. It watches, compiles, and tests rejection of `future_state`, completed `rollout_context`, `target_action`, and related post-treatment/gold aliases. The auditor remains a companion CLI rather than direct composition inside `evaluation_contract.py`.

No real R0 prediction/data/resource bundle has passed D016–D023. Classification remains `initial_reproduction_failure`.

### Prior-art / RQ-001 C020

Li, Kaba, and Ravanbakhsh, AISTATS 2025, characterise the maximal causal abstraction identifiable from paired observations under unknown subset interventions as an intervention-induced quotient. Language that only names, predicts, or reconstructs that quotient adds no partition identifiability.

RQ-001 is narrowed to whether an externally anchored population language channel can strictly refine a residual quotient block and jointly identify raw-utterance equivalence with the refined intervention-target partition, after the strongest non-language quotient has been applied. The candidate remains not adopted.

Adoption requires a positive-measure language-law separation across residual-equivalent models, an anti-recoding external anchor, a strict-refinement theorem, an impossibility result without the anchor/information condition, direct quotient-label ablation, unseen form/composition/target/system splits, public baseline reproduction, and exactly one preregistered claim.

## Stage decision

No next stage is proposed. Transition remains blocked until all of the following exist:

1. at least one competent learned external public capability baseline;
2. immutable matched random/language-blind/state-only/shuffle controls;
3. complete three-seed prediction/artifact/leakage qualification;
4. qualified R0.2 online comparison with real entity/dynamics/language-form holdouts;
5. retained R0.3 rejection;
6. novelty matrix closed through relevant 2026 primary work and official code;
7. exactly one preregistered successor claim with theorem, counterexample, and stopping rule.

## Formal status

- public learned capability baseline: not reproduced
- R0.1 131,072-frame verified artifact: absent
- R0.2 formal reproduction: incomplete
- R0.3 hidden intervention-target empirical track: rejected
- broad RQ-001: rejected
- narrowed RQ candidate: not adopted
- evaluation classification: `initial_reproduction_failure`
- novelty: not established
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
