# R0.1 exact one-step resume qualification — run 30300067389

## Scope

This record audits the official SILG learner update path only. It does not claim asynchronous actor-queue continuation, public-baseline reproduction, task competence, R0.2 progress, novelty, or a new intelligence principle.

Canonical branch: `research/intelligence-swarm-reconstruction-001`

Execution commit: `4f2329b21c3308434f6a5ef51789a915250658d3`

Workflow run: `30300067389`

Artifact:

- ID: `8666312079`
- name: `r01-silg-official-checkpoint-resume-30300067389`
- size: `157,643,235 bytes`
- digest: `sha256:34f02c802f6db15b55336a0547e3914846aad6d74783ebfc371d12ca6ac08115`

## Fixed public execution contract

- environment: SILG RTFM train/test S1
- model: official `multi`
- stateful: `false`
- actors: `30`
- learner threads: `4`
- batch size: `24`
- unroll length: `80`
- frames per learner update: `1,920`
- learning rate: `0.0005`
- entropy cost: `0.05`
- optimizer and scheduler: pinned public SILG implementation
- global gradient clip norm: `40`
- CPU replay parity: `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`

No model, optimizer, split, seed topology, environment semantics, or capability metric was changed.

## Registered learner update

The instrumentation captured the real third learner update consumed inside the original learner lock.

- pre-update frame boundary: `3,840`
- post-update frame boundary: `5,760`
- exact batch SHA-256: `8c11d4ec88163723b6aabd4324e9f0c1c85b0ccb2bd4af0bd53a5292caa52e59`
- exact initial agent-state SHA-256: `4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2`
- pre-model SHA-256: `b6f353b435879bec94fdd461fb59015cbc4890cf4f1418efcdd1768d11ea809a`
- post-model SHA-256: `0cdc13d43980c351707febf069fcc40a9fce0aa0c1a986b66de21576bf5a4e88`
- post-gradient SHA-256: `61ef4f89d7dd3a2903419f692904d88de3baafa69d59c64ed2d2209dbbdaea71`

## Exact replay result

The captured pre-update payload was restored into a separate model, actor model, optimizer, and scheduler. The same exact learner batch and recurrent state were replayed through the pinned public learner update.

All fail-closed checks passed:

- learner model tensors: exact
- actor model tensors: exact
- optimizer state and parameter groups: exact
- scheduler state: exact
- clipped parameter gradients: exact
- Python / NumPy / Torch RNG states: exact
- loss and reported learner statistics: exact
- pre/post frame boundaries: exact

Formal classification: `exact_one_step_resume_equivalence`

Qualification status: `accepted`

## Checkpoint evidence

- official `job.tar` bytes: `39,266,613`
- official `job.tar` SHA-256: `ac74816ee6ea2ca14893fb6f22b9b7fe97c3b83b17938dd1b11d2a446b76eab6`
- checkpoint frame counter after the short official-profile run: `11,520`
- checkpoint required-key omissions: none
- pre-update payload: `61,183,781 bytes`
- post-update payload: `102,988,204 bytes`

## Resource evidence

Official-profile short run command reached `5,760` requested frames and completed successfully.

- wall time: `205.66 s`
- user CPU time: `464.80 s`
- system CPU time: `29.22 s`
- maximum RSS: `8,187,952 KiB`
- exit status: `0`

These values qualify the one-step replay path only and must not be extrapolated as a completed R0.1 capability result.

## Interpretation boundary

This result closes the previously recorded learner-update resume instrumentation gap. It proves that one actually consumed official learner update is exactly reproducible when the exact batch, recurrent state, model, optimizer, scheduler, gradients, frame boundary, and RNG state are preserved.

It does **not** prove:

- bitwise continuation of the asynchronous 30-actor queue;
- successful 100M-frame public SILG reproduction;
- instruction-following competence;
- R0.2 Environment-first superiority;
- held-out entity, dynamics, or language-form transfer;
- novelty or a new intelligence principle.

## Next gate

Proceed only to the preregistered official 100M-frame, three-seed R0.1 reproduction and its fixed task-success qualification. R0.2 Environment-first and matched end-to-end comparison remain blocked until that public baseline is reproduced or a formally documented, resource-bounded stopping rule is reached.
