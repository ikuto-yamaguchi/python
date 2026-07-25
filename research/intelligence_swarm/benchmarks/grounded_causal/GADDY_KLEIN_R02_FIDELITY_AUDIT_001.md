# R0.2 Gaddy--Klein public-code fidelity audit 001

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`
Status: primary-code revision pin completed; public baseline reproduction and R0.2 reproduction remain incomplete

## Scope

This audit does not introduce an operation/goal toy hypothesis, a new mechanism family, or a new architecture. It checks whether the existing SILG/RTFM R0.2 harness is entitled to call itself a faithful transfer of Gaddy and Klein (ACL 2019), using the primary paper record and the authors' public implementation.

## Primary sources checked

1. David Gaddy and Dan Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019, ACL Anthology P19-1188.
2. Public repository currently resolved as `kristyelee/environment-learning` (historically referenced as `dgaddy/environment-learning`).

The ACL record describes a two-stage method: language-free state transitions are used first to induce a latent representation of actions, and language supervision is connected afterward. The public repository README exposes separate pretraining (`pretrain.py`) and language-learning/evaluation (`evaluate.py`) paths, plus a no-pretraining baseline (`--baseline`). It also states Python 3, PyTorch 1.0 or later, and `absl-py` as its requirements.

## Immutable public-code reference

The inspected author-code snapshot is now pinned in:

`GADDY_KLEIN_PUBLIC_REFERENCE_MANIFEST.json`

Pinned revision:

- repository: `kristyelee/environment-learning`
- branch: `master`
- commit: `98c0dc68926ee9535f15019922d2ca871b0ac0b5`
- commit message: `folder`

The manifest records Git blob SHAs for `README.md`, `pretrain.py`, `evaluate.py`, `model.py`, `baseline_model.py`, `message_flags.py`, and `discrete_util.py`. It also records the public-code entrypoints, the `--baseline` control, the default 500,000 pretraining iterations, and the default 20-by-30 discrete message space.

This closes the previous “author-code commit is not pinned” gap. It does not establish native-task execution or SILG/RTFM reproduction.

## What the current SILG port matches

The current canonical R0.2 code preserves the central experimental separation:

- environment-first path trains from language-free transition rows before fitting the language encoder;
- the environment transition encoder and decoder are frozen during the language-matching phase;
- a no-environment-pretraining end-to-end comparison is trained from the same typed rows;
- the environment-first and end-to-end inference parameter budgets are checked for equality;
- state-only is retained as a diagnostic control;
- offline next-state prediction and action accuracy are separated from online task success;
- RTFM S1 transfer is restricted to generator-backed dynamics holdout; entity and language-form holdouts are not fabricated.

These properties are consistent with the high-level two-stage design in the paper and public README.

## Fidelity gaps that still block a reproduction claim

### 1. The port is a task adaptation, not a numerical reproduction

The author code targets SHRDLURN block stacking and regular-expression string manipulation. RTFM S1 has a different observation/action schema and recurrent source policy. Consequently, R0.2 can be called a faithful *method transfer* only after a documented component mapping and matched ablations; it cannot use the paper's published numbers as an expected numerical target.

### 2. Component-level mapping is not yet machine-audited

The current implementation documents the conceptual mapping in prose and code, but no fail-closed manifest checks that every claimed author-code component has a declared SILG counterpart. The minimum manifest must distinguish:

- transition-to-message encoder;
- message-conditioned state-transition decoder;
- language-to-message encoder;
- representation matching objective;
- discrete versus continuous message setting;
- decoder freezing or training schedule;
- no-pretraining baseline;
- inference-time parameter budget.

### 3. Data-efficiency axis is not reproduced

The paper's central empirical claim concerns improvement when instructional data are limited. The current R0.2 run uses one fixed trajectory quantity and compares methods at that quantity. This can test an environment-first baseline, but it does not reproduce the paper's data-efficiency curve. No data-efficiency claim is permitted until preregistered language-data fractions are evaluated with identical environment-transition pretraining data, seeds, and splits.

### 4. Public code has not been executed in its native task

The authors' code has not been run on its original public tasks in this branch. Therefore compatibility with the pinned implementation and expected qualitative ablations remains unverified. This is a public-baseline reproduction gap, not evidence against the method.

## Current classification

- Gaddy--Klein primary-source audit: completed
- exact author-code revision and reference-file blob pin: completed
- native public-code reproduction: not completed
- machine-audited author-to-SILG component mapping: not completed
- SILG/RTFM method transfer: implemented, immutable execution result not yet accepted
- numerical reproduction of ACL 2019 results: inapplicable to RTFM and not claimed
- new architecture: none
- novelty or intelligence-principle claim: prohibited
- capability progress: not recognized
- failure classification until immutable three-seed bundles exist: `initial_reproduction_failure`

## Next minimum actions

1. Add a fail-closed author-code-to-SILG component-mapping manifest and validator without changing the model family.
2. Preserve the currently requested split-job run artifacts before any further long run is triggered.
3. If the split-job run fails, use its R0.2 artifact/log to correct only the first reproducible failure.
4. Do not add data-efficiency sweeps until the single-budget, three-seed R0.1/R0.2 reproduction is complete.
