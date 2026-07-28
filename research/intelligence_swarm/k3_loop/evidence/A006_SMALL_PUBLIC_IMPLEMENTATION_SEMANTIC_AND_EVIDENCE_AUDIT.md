# A006 — Small public AttnRes implementation semantic and evidence audit

Date: 2026-07-29
Task: K3-A evidence audit
Classification: **小型化で要再設計 / public small-model code exists, but no admissible quality evidence**

## Scope

This run does not open a new K3 component and does not change PB1/CR1. It audits one previously unprocessed question for the same Block AttnRes mechanism: whether a compact public implementation provides a faithful small-model precedent that D could reuse.

Audited repository:

- repository: `kyegomez/attn_res`
- fixed commit: `b634f0d9bcc6a925f118f828e07f79679b70ed6f`
- implementation blob: `attn_res/main.py@c4191f3a6e9fb5185ff22bcbf2c345115d110108`
- status: explicitly unofficial, independent implementation

Primary reference remains:

- `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`

## Purpose and computation path

The public implementation supplies a compact decoder-only Transformer with:

- GQA attention;
- SwiGLU FFN;
- RoPE;
- standard, Full AttnRes and Block AttnRes modes;
- one zero-initialized pseudo-query per sublayer;
- parameter-free RMS normalization of routing keys.

For Block mode it stores the embedding, completed block sums and a current partial sum, stacks those sources, computes depth-wise softmax routing, then applies the selected attention/FFN sublayer.

This is useful as readable code and a smoke-test scaffold. It is not an official baseline, fixed training reproduction or quality result.

## Semantic audit against the paper

### 1. Boundary transition occurs after the layer output is computed

The implementation constructs sources and computes the current layer output first. Only afterward it checks:

```python
if i > 0 and i % block_size == 0 and partial_block is not None:
    blocks.append(partial_block)
    partial_block = None
```

It then begins the new partial block with the already-computed output.

The paper pseudocode closes and resets the preceding partial block at the boundary before computing the next block's layer input. Consequently, the first sublayer of each new block in this public implementation routes without the just-completed block being present in `blocks`. The completed representation becomes available one routing event late.

This is a semantic shift, not a harmless indexing convention.

### 2. Divisibility is not enforced

`block_size` is computed by integer division:

```python
return self.n_layers // self.n_blocks
```

The configuration checks only `n_blocks >= 1`. It does not reject:

- `n_layers % n_blocks != 0`;
- `n_blocks > n_layers`, which can produce `block_size == 0` and a modulo failure;
- geometry inconsistent with the paper's explicit equal block partition.

Therefore the implementation can silently change the requested block geometry or fail at runtime.

### 3. Final aggregation is not Attention Residual routing

After the sublayers, the implementation returns:

```python
return final_sources.sum(dim=0)
```

There is no learned final pseudo-query or softmax routing. The same issue exists in its Full AttnRes path, where all sources are summed for the output.

This changes the final residual path and parameter contract relative to the paper/PB1 contract. Results from this code cannot be attributed to canonical Block AttnRes without a separately preregistered correction.

### 4. The standard baseline is not a one-change paper comparison

The repository implements its own GQA/SwiGLU/RoPE Transformer. Using it in the current P0 would change:

- framework and model implementation;
- baseline architecture from the fixed Qwen3-derived B0;
- residual mechanism;
- final aggregation behavior.

It therefore cannot replace the current B0/PB1/CR1 single-change experiment.

## Cost and scale evidence

The repository demonstrates only that compact configurations can instantiate and execute forward/backward smoke tests. Its README examples include widths around 256–512 and short synthetic sequences, but no immutable training corpus, token budget, multi-seed comparison or convergence result is provided.

Accordingly:

- training-time cost: not measured under a controlled baseline;
- inference-time cost: example timing is a smoke-test output, not a reproducible CPU benchmark contract;
- required model scale: unknown;
- required data scale: unknown;
- quality effect: unknown;
- quantization tolerance: unknown;
- long-context behavior: unknown;
- routing collapse/stability: unknown.

The code does show that routing parameter count remains approximately one `d_model` pseudo-query per routed sublayer, but this does not establish favorable active compute, activation traffic, peak RSS or CPU generation speed.

## Existing small-model precedent classification

This repository is classified as:

> **small-model executable scaffold / semantic deviation present / no admissible efficiency or quality evidence**

It is not:

- an author or official implementation;
- a faithful PB1 reference without modification;
- an equal-budget trained baseline;
- evidence that Block AttnRes works at small scale.

## D handoff

Do not replace PB1/CR1 or the fixed candidate with this repository during P0.

If considered after the current P0 route is formally closed, D would first need a separate preregistration covering exactly these corrections:

1. close/reset a completed block before the first routing event of the next block;
2. reject non-divisible and zero block size;
3. add a paper-consistent final router and account for its parameters;
4. freeze a matching standard baseline in the same codebase;
5. save an ordered boundary/source-identity trace before any training.

Fixed implementation identity for any future audit:

- commit `b634f0d9bcc6a925f118f828e07f79679b70ed6f`
- `attn_res/main.py` blob `c4191f3a6e9fb5185ff22bcbf2c345115d110108`

No dependency environment is handed to D now because the implementation is not currently admissible and the sole bottleneck remains C007.

## Result

- Small public executable implementation: **found**
- Official/author status: **no**
- Paper-consistent block boundary: **no**
- Paper-consistent final router: **no**
- Equal block geometry validation: **no**
- Controlled small-model training evidence: **not found**
- Current classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- Current P0 plan: **unchanged**
- Single bottleneck: **C007 portable environment-gate preregistration**
