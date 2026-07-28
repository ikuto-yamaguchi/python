# A003 — Block AttnRes paper-to-candidate deviation matrix

Date: 2026-07-29
Role: K3-A primary-source / public-code audit
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This audit compares the author-controlled Block Attention Residuals specification at:

- `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`

against the current independent reproduction candidate:

- `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- candidate blob `modeling_attnres.py`: `31faf5942b49470e857c0b7c688468ab5aa0751e`

The purpose is not to judge model quality. It is to determine whether D can treat the candidate as a faithful executable baseline for the paper-level Block AttnRes hypothesis.

## Primary-source contract

The official pseudocode defines:

1. values as completed block representations plus the current intra-block partial sum;
2. RMS-normalized keys;
3. one learned pseudo-query per sublayer;
4. softmax over the block/source axis;
5. standard residual accumulation inside a block;
6. at a block boundary, append the completed `partial_block` and reset it before starting the next block;
7. no recency-logit bias or additional residual/AttnRes mixing gate in the published pseudocode.

The official repository provides pseudocode and reported results, but no executable training implementation or checkpoint.

## Deviation matrix

| Item | Official author specification | Current candidate | Classification | Consequence |
|---|---|---|---|---|
| Depth score | `q_l^T RMSNorm(v_i)` | Same base score | aligned | Core depth-attention score is represented. |
| Depth normalization | Softmax over source/block dimension | Same | aligned | Core competition mechanism is represented. |
| Source materialization | Stack completed blocks plus current partial block | Same operator form | aligned at operator level | CPU traffic concern remains, but this is not itself a semantic deviation. |
| Intra-block residual accumulation | Standard additions inside each block | Candidate adds attention/MLP outputs to `partial_block` | partly aligned | Correct only if partial state is reset at every block transition. |
| Block transition | Append completed partial block, then reset `partial_block=None` before the next block begins | Appends `partial_block` after the MLP boundary but never resets it | **critical semantic deviation** | Later “blocks” are cumulative prefixes rather than disjoint block-level partial sums. The next block continues accumulating all earlier outputs. |
| Candidate source list after a boundary | Previous completed blocks + a fresh current partial block | Newly appended cumulative state remains in `blocks`, while the identical tensor also remains as `partial_block` | **critical duplication** | The just-completed state appears twice in the next routing event, changing its effective prior mass and routing gradients. |
| Initialization / routing prior | Learned pseudo-query; official pseudocode contains no source-specific logit bias | Adds a learnable recency bias to the current partial source, default config `3.0` | **unregistered algorithmic extension** | Softmax distribution, gradients, and initial equivalence differ from the published pseudocode. It cannot be attributed to Block AttnRes alone. |
| Optional mixing gates | Not part of official pseudocode | Supports sigmoid scalar, sigmoid vector, and learnable-alpha gates | unregistered extension, inactive only when `gate_type=bias` | Any non-default run becomes a compound intervention rather than a single Block AttnRes ablation. |
| Exact standard-model equivalence at initialization | Not claimed by the official pseudocode | Candidate comments claim recency bias makes output “exactly” standard Qwen3 | unsupported / mathematically inexact for finite bias | A finite bias such as 3 or 10 yields a probability near, not equal to, one. Earlier sources retain nonzero mass. |
| Number of blocks | Official large-scale evidence uses about 8 blocks | C001 uses 4 blocks for 12 layers | extrapolation | Valid as a small-scale test, but outside the principal author evidence and not a faithful hyperparameter reproduction. |
| Base architecture | Author scaling models and Kimi Linear configuration | Qwen3 dense decoder | intended transfer, not reproduction | Results test portability to Qwen3, not reproduction of the reported Kimi setup. |
| Systems optimization | Cache-based communication and two-phase computation are part of the practical low-overhead claim | Eager `stack`/RMSNorm/einsum/softmax/einsum | systems deviation | Candidate latency cannot validate the paper’s optimized-system overhead claim. |
| Executable provenance | No author executable baseline released | Independent implementation | independent reproduction | All numerical conclusions require explicit paper-to-code deviation controls. |

## Critical counterexample: missing block reset

Assume two transformer layers per block and write sublayer deltas as `a1, m1, a2, m2, ...` with embedding `e`.

The intended first completed block is approximately:

`b1 = e + a1 + m1 + a2 + m2`

After crossing the boundary, the next block should start from a fresh partial sum, so its block contribution is formed from later sublayer outputs rather than continuing the full prefix.

In the candidate, `b1` is appended to `blocks`, but `partial_block` remains `b1`. At the next routing event the source list therefore contains both:

- `blocks[-1] = b1`
- `partial_block = b1`

The same representation is duplicated. Subsequent residual updates then produce `b1 + a3 + m3 + ...`, so later stored block representations are cumulative prefixes. This is not the official block-partition semantics.

This deviation can make routing appear artificially recency-biased even without the explicit recency-bias parameter, because the newest cumulative state is duplicated at a boundary.

## Initialization claim audit

For `S` sources and finite recency bias `b`, with zero pseudo-query logits, the current-source weight is:

`exp(b) / (exp(b) + S - 1)`.

It is strictly less than one for finite `b` and `S>1`. Therefore the candidate’s comments that the model is “mathematically identical” to standard Qwen3 at initialization are not exact. For example, with five sources:

- `b=3`: current-source weight is about `0.834`;
- `b=10`: current-source weight is about `0.999818`.

The latter may be a close approximation, but neither is equality. Moreover, duplicated current/cumulative states alter the effective distribution further.

## Classification

Block AttnRes remains:

> **小型化で要再設計・追加検証・未採用**

The current candidate path is additionally classified as:

> **paper-semantics mismatch requiring a preregistered minimal correction before it can serve as the canonical Block AttnRes baseline**

This is not a rejection of Attention Residuals. It is a rejection of treating the present candidate unchanged as a faithful paper-level single-change ablation.

## Handoff to C

Before D performs exact model measurements, C must amend the semantic gate with two explicit variants:

1. **PAPER-BLOCK variant**
   - remove source-specific recency bias from the causal Block AttnRes comparison;
   - reset the intra-block partial state at the registered boundary according to the author pseudocode;
   - prohibit optional sigmoid/alpha gates;
   - preserve the same base Qwen3 attention, MLP, normalization, tokenizer-free synthetic input, and initialization outside the residual path.

2. **CANDIDATE-RAW diagnostic variant**
   - preserve the independent implementation unchanged;
   - use only to measure the published candidate artifact;
   - never attribute its result to paper Block AttnRes alone.

The preregistration must specify whether embedding is an initial completed source, how the first partial state is formed, exact boundary indexing in sublayer units, and source identities at every layer.

## Handoff to D

D003-GHA Stage 1 dependency/import work remains useful and should continue unchanged. Stage 2 must not report the raw candidate as a residual-only paper reproduction.

After the environment gate passes, D should first add a deterministic semantic trace using a tiny model and record for every routing event:

- layer and sublayer index;
- block-boundary decision;
- source count;
- source tensor identity/checksum;
- whether any source is duplicated;
- whether `partial_block` was reset;
- recency-bias value;
- source weights under zero-query initialization.

A canonical paper-level B0/A1 measurement is authorized only after the PAPER-BLOCK variant passes this trace.

## Handoff to E

Recommended next classification:

- Block AttnRes hypothesis: **追加検証・未採用**;
- unchanged `wdlctc` candidate as canonical paper reproduction: **狭義化 / not admissible without semantic correction**;
- D003-GHA environment stage: continue;
- full-model timing and learning stages: remain blocked until C registers the paper-semantics correction and D verifies the source trace.

## Evidence boundary

This audit establishes a code/specification mismatch. It does not establish whether the official mechanism improves or degrades quality, speed, memory, quantization behavior, or intelligence at small scale. No architecture, capability, or novelty claim is made.
