# A004 — Block AttnRes indexing and block-geometry audit

Date: 2026-07-29  
Role: K3-A evidence audit  
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This run audits one unresolved paper-to-executable boundary for Block Attention Residuals:

> Which index space defines a block boundary, and what exact relation must hold among Transformer blocks, Attention/MLP sublayers, block count `N`, and block size `S`?

No model execution, architecture invention, dataset access, training, or capability claim is performed.

## Primary artifacts

- Kimi Team, *Attention Residuals*, arXiv:2603.15031v1, 2026-03-16.
- `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`, `README.md` PyTorch-style pseudocode.

The official repository still contains pseudocode rather than an executable author training implementation.

## Primary-source facts

### 1. The mathematical layer index is a 1-based sublayer index

The report defines `l ∈ {1, ..., L}` and explicitly treats each self-attention or MLP module as an individual layer. Therefore one Transformer block contributes two mathematical layers.

Consequences:

- the paper's `L` is the number of Attention/MLP sublayers;
- a model with 12 Transformer blocks has `L = 24` paper layers;
- boundary semantics must be defined over sublayers, even if an implementation stores one integer per Transformer block.

### 2. The repository pseudocode uses a Transformer-block counter

The pseudocode checks:

```python
if self.layer_number % (self.block_size // 2) == 0:
    blocks.append(partial_block)
    partial_block = None
```

and comments that `block_size` counts Attention + MLP while each Transformer layer has two.

This translation is only well-defined when all of the following are explicit:

1. `self.layer_number` is 1-based;
2. `block_size` is an even positive number of sublayers;
3. `self.block_size // 2` is the exact number of Transformer blocks per AttnRes block;
4. the boundary check happens before the first Attention of the next block, after the previous block's MLP output has completed its partial sum.

### 3. Zero-based execution creates an initial false boundary

If `self.layer_number == 0` for the first Transformer block, the modulo condition is true for every legal divisor. The pseudocode then appends the initial `partial_block` before any Attention or MLP transformation and resets it.

Because `blocks` already includes the token embedding, this can create two embedding-equivalent sources:

- the preregistered embedding source already in `blocks`;
- the just-appended initial `partial_block`.

This is observationally similar to the duplicate-source defect identified in A003, but has a different cause: index-origin ambiguity rather than failure to reset a completed block.

Therefore a semantic trace can pass reset checks yet still be wrong unless it also verifies that no boundary occurs before the first completed group of `S` sublayers.

### 4. Odd `block_size` is not a valid silent input

The use of integer division `block_size // 2` silently changes the requested geometry when `block_size` is odd. For example, `S=5` becomes two Transformer blocks, i.e. four executed sublayers per block, not five.

The canonical PAPER-BLOCK path must reject odd `S`; it must not round or truncate.

### 5. `N` and `S` are distinct quantities

The paper uses:

- `N`: number of completed Block AttnRes blocks retained as depth-wise sources;
- `S`: number of Attention/MLP sublayers per block.

For an exactly divisible model:

```text
L_sub = 2 * L_transformer
N = L_sub / S
S = L_sub / N
```

The final Kimi Linear experiment uses 54 sublayers and `S=6`, producing 9 completed blocks plus the token embedding, i.e. 10 depth-wise sources.

For the current 12-Transformer-block PB1 proposal:

```text
L_transformer = 12
L_sub = 24
N = 4
S = 6 sublayers/block = 3 Transformer blocks/block
expected completed boundaries after Transformer blocks 3, 6, 9, 12
```

Thus the earlier shorthand `N=4` is not an executable boundary rule by itself. PB1 must register both `N=4` and `S=6`, plus the exact boundary sequence.

### 6. Final-output aggregation must be counted separately

The report states that the final output layer aggregates all `N` completed block representations. The final router is not an additional completed block and must not increment `N`.

This matters for:

- exact source-count traces;
- parameter attribution;
- CPU routing-event counts;
- save/load event-structure comparison.

## Failure counterexample

Consider the current PB1 shape: 12 Transformer blocks, `N=4`, `S=6` sublayers.

A zero-based implementation checks boundaries at Transformer indices `0, 3, 6, 9`. It therefore:

1. creates a false boundary before the first Attention;
2. fails to close the final intended block after Transformer block 12 unless a separate finalization rule exists;
3. can still report four boundary events, masking the off-by-one error if only the count is checked.

Hence equality of boundary count is insufficient. The ordered boundary positions and source creation events must match the preregistration.

## Classification

**Small-scale classification: `小型化で要再設計`**

Rationale:

- the underlying mechanism is not shown to fail at small scale;
- however, its executable semantics require an explicit sublayer-index adapter, exact block geometry, and trace assertions that are absent from the released pseudocode;
- a superficially faithful implementation can change the source set while preserving parameter count and nominal block count.

This does not establish quality improvement, CPU efficiency, quantization robustness, or adoption.

## Required C amendment

C should amend PB1 without changing the mechanism:

```yaml
paper_layer_index_origin: 1
transformer_block_index_origin: explicitly declared
transformer_blocks: 12
sublayers_per_transformer_block: 2
L_sub: 24
N_completed_blocks: 4
S_sublayers_per_block: 6
transformer_blocks_per_attnres_block: 3
boundary_after_transformer_blocks: [3, 6, 9, 12]
embedding_source_count: 1
final_router_adds_completed_block: false
odd_S: reject
nondivisible_L_sub_by_S: reject
```

The implementation may use zero-based arrays internally, but the trace must emit canonical 1-based semantic positions.

## Required D trace additions

Before CR1/PB1 full-model resource measurement, record:

- runtime Transformer index and its declared origin;
- canonical sublayer indices for Attention and MLP;
- boundary position in both index spaces;
- number of completed sublayers since the previous boundary;
- source creation event and checksum;
- whether a boundary occurred before any transformed output;
- expected versus actual ordered boundary sequence;
- completed-block count before the final router;
- final-router source count, with embedding reported separately.

PB1 semantic STOP conditions must include:

- boundary before the first transformed sublayer;
- boundary sequence not exactly `[3, 6, 9, 12]` for the registered 12-block geometry;
- any block containing other than six sublayers;
- odd or silently truncated `S`;
- missing final completed block;
- final router incorrectly counted as a completed block.

## Hand-off

- **C:** add the explicit `L_sub/N/S` geometry and ordered boundary positions to the next PB1 amendment.
- **D:** extend the deterministic semantic trace with index-origin and ordered-boundary assertions.
- **E:** do not accept PB1 semantic PASS from reset/duplicate checks alone; require exact boundary-position PASS.

## Decision boundary

Block AttnRes remains:

> `小型化で要再設計・追加検証・未採用 / Path-WARN`

PAPER-BLOCK remains the canonical paper candidate, but its semantic contract is incomplete until the index-origin and block-geometry assertions above are preregistered and executed.
