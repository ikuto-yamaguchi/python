# A005 — Official artifact status and community implementation admissibility

Date: 2026-07-29
Task: K3-A evidence audit
Classification: **小型化で要再設計 / official executable evidence remains unavailable**

## Scope

This run does not open a new K3 component and does not alter the PB1/CR1 experiment plan. It re-checks whether an author-maintained executable training implementation or released checkpoint has appeared since A001, and whether newly visible community implementations can be admitted as an official or author baseline.

## Primary-source status

### Author repository

Fixed official repository:

- `MoonshotAI/Attention-Residuals`
- fixed research commit: `85e22310fe5ee860b4a023de312d791de8a5a5e6`
- repository: https://github.com/MoonshotAI/Attention-Residuals

As checked on 2026-07-29, the repository still exposes the paper, README, figures, and PyTorch-style pseudocode. It does not expose the training entry point, dependency lock, immutable dataset/token manifest, evaluation harness, experiment checkpoint, or Kimi Linear AttnRes weights required for an author-executable reproduction.

The repository issue list still contains open requests for implementation code and model weights, including:

- issue #5, request to release the Kimi Linear AttnRes checkpoint: https://github.com/MoonshotAI/Attention-Residuals/issues/5
- issue #6, request for the experimental implementation: https://github.com/MoonshotAI/Attention-Residuals/issues/6
- issue #8, request to show/release code: https://github.com/MoonshotAI/Attention-Residuals/issues/8

No author reply, release artifact, linked checkpoint, or official implementation PR was found in those sources during this audit.

## Newly visible community implementation

Official issue #13 links a third-party Megatron-LM implementation:

- issue: https://github.com/MoonshotAI/Attention-Residuals/issues/13
- linked repository: https://github.com/Smu-Tan/Megatron-LM
- issue opened: 2026-04-27

The issue author describes it as an implementation based on Megatron-LM with a Llama 3 dense architecture and a 1,000-step pretraining run. The issue remains open and is not an author release, repository submodule, accepted pull request, tagged reference implementation, or checkpoint endorsed by the Attention Residuals authors.

A separate NVIDIA Megatron-LM feature request also remains open:

- https://github.com/NVIDIA/Megatron-LM/issues/4016

Therefore there is still no upstream Megatron-LM implementation that can be treated as a maintained canonical baseline.

## Admissibility decision

The community Megatron implementation is classified as:

> **independent reproduction lead / not an official baseline / not admissible for paper attribution without a separate code-semantic audit and preregistration**

It must not replace PB1 or CR1 during the current P0 cycle because:

1. the current single bottleneck is the preregistered C006 environment route;
2. changing framework and base architecture would introduce multiple simultaneous interventions;
3. the public claim covers only a short 1,000-step run, not the paper's scale or a fixed same-budget comparison;
4. author endorsement and checkpoint provenance are absent;
5. its block-boundary, partial-reset, source-identity, routing-bias, parameter-delta, and save/load semantics have not been audited against the paper.

## Small-model relevance

This audit adds no evidence that Block AttnRes works below the primary reported scale. It also adds no CPU, quantization, three-seed, quality, or memory result. A short community training run can show that code executes, but cannot establish a small-model efficiency principle unless all of the following are separately fixed and measured:

- paper-consistent residual semantics;
- one-change baseline/ablation identity;
- immutable token stream and equal token budget;
- exact parameter and active-compute accounting;
- multiple seeds;
- CPU latency and isolated RSS;
- raw logs, environment lock, commit, and artifact checksums.

## Handoff

### To C/D

No experiment manifest or implementation target changes. Continue only with C006 and the already selected PB1/CR1 route. Do not substitute the community Megatron implementation for the fixed candidate.

### To E

The official-artifact status remains unchanged: **author executable baseline unavailable**. The community Megatron route is a future fallback lead only, and may be considered only after the current P0 route is completed or formally stopped and after a new preregistration.

## Result

- Official executable training code: **not found**
- Official checkpoint/model weights: **not found**
- Author-maintained dependency/data/evaluation contract: **not found**
- Community Megatron implementation: **found, but not official and not currently admissible**
- Current classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- Current bottleneck: **C006 default-branch thin-dispatcher preregistration**
