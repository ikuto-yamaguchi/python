# R0.2 Gaddy--Klein public-code fidelity audit 001

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`
Status: audit completed; public baseline reproduction and R0.2 reproduction remain incomplete

## Scope

This audit does not introduce an operation/goal toy hypothesis, a new mechanism family, or a new architecture. It checks whether the existing SILG/RTFM R0.2 harness is entitled to call itself a faithful transfer of Gaddy and Klein (ACL 2019), using the primary paper record and the authors' public implementation.

## Primary sources checked

1. David Gaddy and Dan Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019, ACL Anthology P19-1188.
2. Authors' public repository: `dgaddy/environment-learning`, titled “Code for Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following”.

The ACL record describes a two-stage method: language-free state transitions are used first to induce a latent representation of actions, and language supervision is connected afterward. The public repository README exposes separate pretraining (`pretrain.py`) and language-learning/evaluation (`evaluate.py`) paths, plus a no-pretraining baseline (`--baseline`). It also states Python 3, PyTorch 1.0 or later, and `absl-py` as its requirements.

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

## Fidelity gaps that block a reproduction claim

### 1. Author-code commit is not pinned

The canonical repository pins SILG and RTFM commits, but it does not pin a commit SHA for `dgaddy/environment-learning`. `METHOD_REFERENCE_COMMIT` in `r02_typed_comparison.py` refers to the local port history, not an immutable author-code revision. Therefore the exact public implementation inspected cannot yet be reconstructed from the R0.2 artifact bundle.

Required minimum correction: record the author repository commit SHA and hashes of the specific reference files used (`README.md`, `pretrain.py`, `evaluate.py`, `model.py`, `baseline_model.py`, and relevant discrete-message utilities). Do not import its task-specific SHRDLURN/regex data pipeline into SILG.

### 2. The port is a task adaptation, not a numerical reproduction

The author code targets SHRDLURN block stacking and regular-expression string manipulation. RTFM S1 has a different observation/action schema and recurrent source policy. Consequently, R0.2 can be called a faithful *method transfer* only after a documented component mapping and matched ablations; it cannot use the paper's published numbers as an expected numerical target.

### 3. Component-level mapping is not yet machine-audited

The current implementation documents the conceptual mapping in prose and code, but no fail-closed manifest checks that every claimed author-code component has a declared SILG counterpart. The minimum manifest should distinguish:

- transition-to-message encoder;
- message-conditioned state-transition decoder;
- language-to-message encoder;
- representation matching objective;
- discrete versus continuous message setting;
- decoder freezing or training schedule;
- no-pretraining baseline;
- inference-time parameter budget.

### 4. Data-efficiency axis is not reproduced

The paper's central empirical claim concerns improvement when instructional data are limited. The current R0.2 run uses one fixed trajectory quantity and compares methods at that quantity. This can test an environment-first baseline, but it does not reproduce the paper's data-efficiency curve. No data-efficiency claim is permitted until preregistered language-data fractions are evaluated with identical environment-transition pretraining data, seeds, and splits.

### 5. Public code has not been executed in its native task

The authors' code has not been run on its original public tasks in this branch. Therefore compatibility with the inspected implementation and expected qualitative ablations remains unverified. This is a public-baseline reproduction gap, not evidence against the method.

## Current classification

- Gaddy--Klein primary-source audit: completed for the paper record and public README
- exact author-code revision pin: missing
- native public-code reproduction: not completed
- SILG/RTFM method transfer: implemented, execution result not yet accepted
- numerical reproduction of ACL 2019 results: inapplicable to RTFM and not claimed
- new architecture: none
- novelty or intelligence-principle claim: prohibited
- capability progress: not recognized
- failure classification until immutable three-seed bundles exist: `initial_reproduction_failure`

## Next minimum actions

1. Pin and hash the authors' public-code revision without modifying the R0.2 model family.
2. Add a component-mapping manifest that fails closed when the local port or reference hashes drift.
3. Preserve the currently requested split-job run artifacts before any further long run is triggered.
4. If the split-job run fails, use its R0.2 artifact/log to correct only the first reproducible failure.
5. Do not add data-efficiency sweeps until the single-budget, three-seed R0.1/R0.2 reproduction is complete.
