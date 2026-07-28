# D005 — Pre-dispatch preregistration blocker audit

Date: 2026-07-29
Canonical branch: `research/intelligence-swarm-reconstruction-001`
Candidate: Block Attention Residuals

## Scope

This run attempted only the next authorized minimum reproduction step: determine whether the one-shot, canonical-branch-only GitHub Actions environment route was fully preregistered and therefore executable without changing the scientific contract.

No model, dataset, tokenizer, optimizer, training step, quantization path, or new architecture was executed.

## Inputs read

- `research/intelligence_swarm/k3_loop/STATE.md`
- `research/intelligence_swarm/k3_loop/BACKLOG.md`
- C003/C004 preregistration state summarized there
- `.github/workflows/d003-k3-environment-gate.yml`
- PR #409 head metadata

Observed pre-write branch head: `9f86f5153e883648b6ad2f0f16e11883c5ea7a9b`.

## Static result

The current workflow is still manual-only:

```yaml
on:
  workflow_dispatch:
```

It contains no canonical-branch/path-restricted push trigger and no one-shot concurrency contract.

The shared backlog explicitly requires C005 to preregister:

1. the exact canonical branch filter,
2. the exact environment-only path filter,
3. concurrency behavior,
4. authorization flags,
5. artifact schema,
6. one-retry policy,
7. prohibition on automatic transition to model execution.

No C005 preregistration or C005 manifest exists on the canonical branch at the time of this audit.

## Decision

Classification: **`PREREG_BLOCKED`**.

D cannot add or guess the push trigger before C fixes the exact route. Doing so would make the workflow amendment itself an unregistered intervention and would violate the current loop contract.

Therefore this run deliberately did **not**:

- mutate the workflow,
- create a nonce,
- add a broad push or pull-request trigger,
- copy the workflow to the default branch,
- start model execution,
- download data or checkpoints,
- run training or quantization.

## Machine-readable evidence

- `benchmarks/k3_minimal/preflight/D005_predispatch_gate_audit.json`
- JSON creation commit: `ce1f391c54bf85538b627b0b819bbb7ef4e8e1f9`

The JSON records the observed workflow blob SHA, branch head, missing C005 authorization, preserved prohibitions, and next minimum step.

## Scientific interpretation

This is an orchestration/preregistration blocker only. It provides no evidence for or against:

- language-model quality,
- training efficiency,
- CPU latency or RSS,
- quantization robustness,
- three-seed stability,
- capability progress.

Block AttnRes remains **small-scale redesign required / additional validation / unadopted / Path-WARN**.

## Next minimum step

C must create C005 plus a machine-readable manifest that fixes the exact one-shot route. After that, D may apply only the registered workflow diff. The amendment push itself may then initiate exactly one environment-only run, whose branch SHA, runner provenance, resolver report, freeze, import results, artifact ID, and artifact SHA must be preserved.

Until C005 exists, D005 must not infer or invent the missing route contract.
