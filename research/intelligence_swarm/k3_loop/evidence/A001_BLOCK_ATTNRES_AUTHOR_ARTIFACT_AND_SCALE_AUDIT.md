# A001 — Block Attention Residuals: author artifact and primary-scale audit

Date: 2026-07-28
Branch: `research/intelligence-swarm-reconstruction-001`
Role: K3-A primary evidence audit
Status: completed
Classification: **小型化で要再設計**

## Scope

E001 restricted A to one evidence delta for the current Block AttnRes bottleneck:

1. determine whether an author-controlled executable implementation or checkpoint exists beyond the official documentation repository;
2. extract the exact primary-report scale, depth, block, token and compute conditions needed to interpret C001;
3. do not open another K3 component.

Primary sources inspected:

- Kimi Team, *Attention Residuals*, arXiv:2603.15031v1, 2026-03-16.
- `MoonshotAI/Attention-Residuals`, official repository, pinned at commit `85e22310fe5ee860b4a023de312d791de8a5a5e6`.
- Open issues in the official repository concerning code and checkpoint release, inspected 2026-07-28.

## Author-controlled artifact finding

At the pinned official commit, the repository contains the paper PDF, README, figures and PyTorch-style pseudocode. It does **not** contain an executable training entry point, package metadata, environment lock, dataset manifest, evaluation harness, checkpoint index or released model weights.

The repository history contains four commits through the pinned head. The official README describes the mechanism and gives pseudocode, but not the actual large-scale implementation used for the paper.

Open issue evidence is consistent with this negative finding:

- issue #6 asks the authors to provide experiment code and remains open;
- issue #5 asks for the Kimi Linear AttnRes weights and remains open;
- issue #8 explicitly asks for code and remains open.

No author response, release, tag, GitHub package, or author-controlled Hugging Face checkpoint was located in the official repository or linked artifacts during this audit.

**Conclusion:** no author-controlled executable baseline or checkpoint was found as of 2026-07-28. The current D path must continue to be labeled an independent reproduction of an unofficial implementation. This is an absence finding, not proof that no private or unlinked implementation exists.

## Exact primary scaling-law conditions

The primary report sweeps five MoE model sizes. “Activated parameters” exclude embeddings. Each condition compares PreNorm baseline, Full AttnRes and Block AttnRes with approximately eight blocks, using identical within-size hyperparameters selected for the baseline.

All scaling-law runs use:

- context length: `8192` tokens;
- schedule: cosine learning-rate schedule;
- Block AttnRes: `N = 8` in Table 2 / approximately eight blocks in text;
- model family: Kimi Linear-style MoE, interleaving KDA and MLA in a `3:1` ratio, each followed by MoE;
- zero initialization for every pseudo-query;
- compute measured in PFLOP/s-days.

| Activated params | Training tokens | Transformer blocks `Lb` | Depth-wise layers `L=2Lb` | Attention heads `H` | `d_model` | reported `d_ff` | LR | batch-size field | Baseline loss | Block loss | Full loss |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 194M | 38.7B | 12 | 24 | 12 | 896 | 400 | 2.99e-3 | 192 | 1.931 | 1.909 | 1.899 |
| 241M | 45.4B | 13 | 26 | 13 | 960 | 432 | 2.80e-3 | 256 | 1.895 | 1.875 | 1.874 |
| 296M | 62.1B | 14 | 28 | 14 | 1024 | 464 | 2.50e-3 | 320 | 1.829 | 1.809 | 1.804 |
| 436M | 87.9B | 16 | 32 | 16 | 1168 | 528 | 2.20e-3 | 384 | 1.766 | 1.746 | 1.737 |
| 528M | 119.0B | 17 | 34 | 17 | 1264 | 560 | 2.02e-3 | 432 | 1.719 | 1.693 | 1.692 |

The paper reports fitted laws:

- baseline: `L = 1.891 * C^-0.057`;
- Block AttnRes: `L = 1.870 * C^-0.058`;
- Full AttnRes: `L = 1.865 * C^-0.057`.

At the cited comparison point, Block AttnRes reaches loss `1.692` versus baseline `1.714`, described as a `1.25x` compute advantage. This is a fitted scaling-law statement, not a directly reproduced small-model result.

## Largest primary run

The final reported Kimi Linear experiment uses:

- `48B` total parameters;
- `3B` activated parameters;
- `27` Transformer blocks / `54` depth-wise layers;
- `8` of `256` routed experts plus `1` shared expert;
- Block AttnRes block size: `6` depth-wise layers;
- `9` blocks plus token embedding = `10` depth-wise sources;
- `4096` context during main pre-training;
- Muon optimizer;
- WSD schedule;
- global batch: `8M` tokens;
- `1T` WSD pre-training tokens;
- approximately `400B` high-quality mid-training tokens;
- subsequent progressive context extension to `32K`.

These conditions are far outside the sub-1GB target and cannot establish CPU or smartphone efficiency.

## Infrastructure dependence

The paper's claimed low overhead is not from the mathematical operator alone. It depends on:

- cached block representations across pipeline stages;
- a two-phase computation schedule;
- batched inter-block queries within each block;
- online-softmax merging;
- kernel fusion with surrounding operations;
- sequence sharding and tensor-parallel communication for long prefill.

For the paper's typical inference accounting (`L=128`, `N=8`, `S=16`), residual-side I/O is reported as:

- standard residual: `3d` per token per layer;
- Block AttnRes: `5.5d`;
- Full AttnRes: `24d`.

Thus even the optimized Block mechanism has approximately `1.83x` the residual-stream I/O of a standard residual under the paper's own typical accounting. The reported under-2% end-to-end latency is a system-level result on typical large-model inference workloads, where the residual path is a small fraction of total compute. It must not be transferred to an eager 100M CPU implementation.

## Comparison with C001

C001 differs materially from the lowest primary scaling point:

| Field | C001 | Lowest primary point |
|---|---:|---:|
| total/active parameters | about 115.6M dense | 194M activated MoE, embeddings excluded |
| Transformer blocks | 12 | 12 |
| depth-wise layers | 24 | 24 |
| width | 512 | 896 |
| attention heads | 8 | 12 |
| Block sources target | N=4 | N=8 |
| context | 2048 | 8192 |
| intended tokens | staged, initially smoke/pilot | 38.7B |
| architecture | Qwen3-style dense | Kimi Linear MoE + KDA/MLA |
| runtime target | weak CPU / eventual smartphone | large-scale accelerator system |

The useful controlled similarity is depth: both have 12 Transformer blocks / 24 sublayers. Nearly every other scale and systems condition differs. Therefore C001 tests transferability below the primary evidence range; it is not a direct reproduction of Table 2.

## Small-model efficiency classification

Classification: **小型化で要再設計**.

Reasoning:

- The core routing parameterization is small and zero-initializable, so it is not intrinsically giant-scale-only.
- Primary evidence begins at 194M activated MoE parameters and tens of billions of tokens; no author evidence covers approximately 100M dense models or weak CPUs.
- The favorable latency claim relies on a two-phase fused implementation that is absent from the official repository and from the currently audited unofficial eager path.
- A small dense CPU model may spend a much larger fraction of wall time on stacking, normalization, einsum/softmax and memory traffic.

This classification does not adopt or reject Block AttnRes. It authorizes only the already-preregistered D002 executable preflight.

## Handoff to D

Author-controlled executable baseline: **not found**.

Pinned official documentary source:

- repository: `MoonshotAI/Attention-Residuals`
- commit: `85e22310fe5ee860b4a023de312d791de8a5a5e6`
- branch observed: `master`
- available implementation material: README pseudocode only

Current executable candidate remains:

- `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- classification: unofficial independent implementation

D002 must not claim reproduction of the paper's optimized inference system. It should explicitly report eager implementation overhead and preserve the source/config checksums already required by E001.

## Remaining evidence gap

Before S2, A must still record a source-level paper-to-candidate deviation matrix, including:

- N=4 versus primary N=8;
- dense Qwen3-style model versus Kimi Linear MoE/KDA/MLA;
- eager per-layer stack/einsum path versus two-phase fused schedule;
- context and token-budget differences;
- whether the unofficial implementation exactly follows block-boundary semantics and zero initialization.

That work is not required to unblock D002 and is therefore left pending.
