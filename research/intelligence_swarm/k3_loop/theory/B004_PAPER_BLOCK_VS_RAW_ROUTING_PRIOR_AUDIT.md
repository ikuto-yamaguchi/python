# B004 — PAPER-BLOCK vs CANDIDATE-RAW routing-prior and small-scale identifiability audit

Date: 2026-07-29
Role: K3-B theory / assumption / scaling audit
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A003 established that the fixed independent implementation differs from the author pseudocode in two coupled ways:

1. a completed `partial_block` is appended but not reset, so the same cumulative prefix can appear both as a completed source and as the current partial source at the next routing event;
2. the current partial source receives a learned recency-logit bias absent from the author pseudocode.

This audit determines whether the unchanged candidate can be treated as a noisy implementation of the same mechanism, or whether it constitutes a different intervention whose quality/resource results are not identifiable as paper Block AttnRes effects.

No new architecture is proposed. The purpose is to define the minimal PAPER-BLOCK contract for C and the semantic/resource measurements required from D.

## Result summary

The unchanged candidate is not merely an implementation approximation. Source duplication and current-source bias jointly change the normalized routing prior, the gradient allocation, and the effective depth diversity. Their effects cannot be separated from paper Block AttnRes by a B0-vs-CANDIDATE-RAW comparison.

Therefore:

- **PAPER-BLOCK** is the only admissible causal A1 variant for a paper-level single-change ablation;
- **CANDIDATE-RAW** remains useful only as an artifact diagnostic;
- raw-candidate quality, stability, or speed must not be attributed to Block AttnRes alone;
- the canonical PAPER-BLOCK parameter increment is provisionally `25,600`, not raw-candidate `25,625`, subject to executable state-dict confirmation.

Classification remains:

> **Block AttnRes: 小型化で要再設計・追加検証・未採用**

## 1. Routing distributions are different interventions

Let a routing event contain `m` older completed sources and one intended current partial source. Let all pseudo-query scores initially be zero.

### PAPER-BLOCK

With no source-specific bias, the initial distribution is uniform over `m+1` sources:

`w_i = 1 / (m + 1)`.

This does not guarantee that uniform routing is optimal; it only states the author-pseudocode intervention being tested.

### CANDIDATE-RAW after a boundary

If the completed cumulative prefix `c` is appended to `blocks` but remains as `partial_block`, the source list contains two identical copies of `c`. If the partial copy additionally receives recency bias `b`, the combined normalized probability mass assigned to the identical representation is:

`W_dup(b,m) = (1 + exp(b)) / (m + 1 + exp(b))`.

Each nonduplicated older source receives:

`W_old(b,m) = 1 / (m + 1 + exp(b))`.

For the C001 maximum source regime corresponding to five intended sources, take four older sources and one duplicated current/completed representation. The raw source list then has six entries. With the candidate default `b=3`:

- duplicated representation total mass: `(1+exp(3))/(5+exp(3)) ≈ 0.8007`;
- each older source mass: `1/(5+exp(3)) ≈ 0.0399`.

Without duplication but with the same bias, current-source mass would be `exp(3)/(4+exp(3)) ≈ 0.8340`. Duplication therefore does not simply strengthen or weaken a scalar recency preference; it changes both the source multiplicity and gradient paths. The two defects cannot be represented as one harmless initialization approximation.

At `b=0`, duplicated identical sources still receive combined mass `2/(m+2)`, twice the mass of each distinct source. Thus removing recency bias alone does not recover paper semantics.

## 2. Gradient non-identifiability

For a softmax mixture, the score gradient for source `j` is proportional to

`w_j <g, v_j - y>`

where `g` is the upstream gradient, `v_j` the source value, and `y` the weighted mixture.

When the same tensor appears twice:

- it receives two score-gradient paths;
- one path includes the source-specific bias parameter and one does not;
- both value paths accumulate into the same upstream prefix graph;
- the normalization denominator differs from the paper mechanism.

Consequently, even if the two duplicated value tensors are bitwise identical, the parameter and graph gradients are not equivalent to a single source with their summed probability. Training can learn a different routing policy and different residual credit assignment.

A downstream loss difference between B0 and CANDIDATE-RAW is therefore compatible with at least three explanations:

1. depth attention over completed block representations;
2. duplicated-prefix prior and duplicated gradient paths;
3. explicit recency-logit bias.

The paper Block AttnRes effect is not identifiable from that comparison.

## 3. Effective depth diversity can collapse at small scale

The stated benefit of AttnRes depends on retaining useful alternatives from different depths. At small depth and only four blocks, that benefit can disappear if routing mass concentrates on a duplicated latest cumulative prefix.

Define effective source count by inverse Simpson concentration:

`N_eff = 1 / sum_i w_i^2`.

Using the example above (`m=4`, duplicated prefix, `b=3`), treating the two identical copies as one semantic source gives approximately:

- latest-prefix semantic mass `0.8007`;
- four older masses `0.0399` each;
- `N_eff ≈ 1.55` semantic sources.

The nominal source count is five, but the effective semantic diversity is close to one. This creates a small-scale failure mode:

> the model pays stack, normalization, softmax, mixing, and dispatch overhead while routing almost entirely through the latest cumulative prefix, approximating an expensive residual bypass rather than exploiting depth alternatives.

This failure can occur even if training loss is stable and all routing gradients are finite.

## 4. Parameter and memory contract

The raw candidate count fixed by D002 is:

- B0: `115,554,304` parameters;
- CANDIDATE-RAW: `115,579,929` parameters;
- raw increment: `25,625`.

The raw increment consists provisionally of:

- pseudo-query and routing-RMSNorm vectors: `25 × (512 + 512) = 25,600` parameters across 24 sublayer routing events plus the final router;
- one scalar recency-bias parameter per routing event: `25` parameters.

Under the PAPER-BLOCK contract, source-specific recency biases and optional mixing gates are absent. Therefore the provisional canonical count is:

- PAPER-BLOCK: `115,579,904` parameters;
- increment over B0: `25,600`;
- relative increment: approximately `0.02215%`;
- FP32 parameter bytes: `462,319,616`;
- BF16 parameter bytes: `231,159,808`.

These figures must be verified from the exact executable state dict. They are not evidence of CPU efficiency: activation traffic and operator fragmentation remain unchanged or nearly unchanged.

KV-cache/state-memory conclusion:

- neither variant adds sequence KV cache directly;
- both require access to multiple block/source activations during the forward pass;
- PAPER-BLOCK reset should bound source semantics to completed block representations plus a fresh partial state;
- CANDIDATE-RAW cumulative prefixes can preserve redundant information and duplicate references, increasing effective traffic without adding useful source diversity.

## 5. FLOPs, communication, and parallelism

The asymptotic routing arithmetic remains `O(T d S)` for sequence length `T`, width `d`, and source count `S`. However, the raw mismatch changes constants and source usefulness:

- duplicated sources increase `S` at affected events;
- source stacking/materialization can copy identical data twice;
- softmax and weighted mixing operate over an enlarged axis;
- two gradient paths target the same cumulative prefix;
- optimized paper-system communication claims cannot be validated by eager candidate execution.

For tensor/sequence parallel execution, duplication also risks communicating or materializing the same logical representation twice. The theoretical communication order may be unchanged, but useful information per transferred byte falls.

Thus CANDIDATE-RAW cannot be used to estimate the paper mechanism's compute or communication Pareto.

## 6. Quantization implications

Weight-only INT8/INT4 removes little of the routing overhead because the dominant routing values and softmax state are activations. The 25 recency-bias scalars are negligible in bytes but can strongly control routing probabilities.

Two distinct quantization risks must be separated:

### PAPER-BLOCK

- pseudo-query and RMSNorm quantization may perturb close source scores;
- source-order flips are possible when logits are near tied;
- activation precision can affect normalization and mixture stability.

### CANDIDATE-RAW

- a large recency bias may mask score perturbations and make routing look stable;
- duplicated sources can preserve the same semantic prefix even if probability swaps between its two copies;
- apparent top-source agreement can therefore overstate semantic routing robustness.

Required future metric: report both tensor-index routing agreement and checksum-collapsed semantic-source agreement. Raw top-index agreement alone is insufficient.

No quantization experiment is authorized before the semantic variant gate and baseline reproduction.

## 7. Minimum-scale and benefit conditions

Primary evidence begins around 194M active parameters and substantially larger token budgets than C001. No theorem fixes a minimum width, depth, or data amount.

For a small model, Block AttnRes can only yield a favorable Pareto if all of the following hold:

1. multiple depth sources contain nonredundant predictive information;
2. learned routing uses more than an effectively single latest source;
3. quality gain exceeds the opportunity cost of routing operations and activation traffic;
4. optimization remains stable without an unregistered recency prior;
5. the benefit survives equal-token and equal-active-compute comparison;
6. CPU/fused implementation does not require systems machinery unavailable on the target device.

A necessary empirical diversity gate is proposed for preregistration, not as an adoption claim:

- checksum-collapsed effective semantic source count must exceed `1.5` for a material fraction of evaluated routing events after training;
- no single semantic source should dominate solely because it is duplicated;
- results must also be reported without converting this exploratory diagnostic into a post-hoc success criterion.

The exact threshold for adoption remains E's decision after baseline data; it must not be retrofitted from observed results.

## 8. Counterexample / failure condition

Consider a 12-layer model partitioned into four blocks where adjacent hidden states are highly correlated. Suppose PAPER-BLOCK learns nearly all mass on the latest partial source. Then validation NLL is unchanged relative to B0, while CPU decode incurs extra RMSNorm, score, softmax, source mixing, and dispatch at each routing event.

This yields:

- parameter overhead near zero;
- no direct KV-cache growth;
- finite gradients and stable training;
- no quality improvement;
- strictly worse latency and activation traffic.

Therefore successful execution and stable optimization are insufficient. Adoption requires a quality/resource Pareto improvement under equal token and active-compute controls.

CANDIDATE-RAW introduces an additional misleading case: duplicated latest prefixes and recency bias can produce stable low-entropy routing and possibly easier optimization, but that result identifies the compound raw mechanism, not paper Block AttnRes.

## 9. Handoff to C

C004 should register two noninterchangeable variants.

### PAPER-BLOCK — canonical causal variant

- reset `partial_block` at each registered boundary;
- define boundaries in sublayer units, not ambiguous layer comments;
- identify whether embedding is an initial completed source;
- record the exact first partial-state rule;
- no source-specific recency-logit bias;
- no sigmoid scalar/vector or alpha mixing gate;
- provisional total parameters `115,579,904`, delta `25,600`;
- preserve base Qwen3 attention, MLP, norms, initialization, input, and output head;
- source identity trace is a hard precondition for full-model timing.

### CANDIDATE-RAW — artifact diagnostic

- preserve commit behavior unchanged;
- report raw total `115,579,929` and delta `25,625`;
- record duplicated checksum groups and recency bias;
- never pool its metrics with PAPER-BLOCK;
- never attribute its quality/resource result to the paper mechanism.

The variants must use separate IDs, output directories, manifests, and decision labels.

## 10. Handoff to D

After D003-GHA environment PASS, run a tiny deterministic semantic trace before any 115M full-model measurement.

For every routing event record:

- variant ID;
- layer and sublayer index;
- block boundary before/after state;
- source role and checksum;
- checksum-collapsed semantic source count;
- duplicate group sizes;
- raw source probabilities;
- probabilities collapsed by checksum identity;
- entropy over raw indices;
- entropy and `N_eff` over semantic sources;
- recency-bias presence/value;
- whether `partial_block` was reset.

Hard semantic PASS for PAPER-BLOCK:

- no unintended duplicate checksum at a boundary;
- reset occurs at every registered boundary;
- no recency-bias parameter in state dict;
- no optional gate parameter;
- source identities match the preregistered trace;
- exact parameter delta is explained.

If this requires changing attention, MLP, normalization, shape, or initialization outside the residual-path implementation, classify the current implementation path as STOP rather than silently patching it.

## 11. Handoff to E

Recommended classification:

- Block AttnRes hypothesis: **追加検証・未採用**;
- PAPER-BLOCK: **canonical candidate pending C004 and semantic trace**;
- CANDIDATE-RAW: **狭義化 — artifact diagnostic only**;
- raw-vs-B0 quality/resource evidence: **inadmissible for paper-level adoption**;
- new K3 components: remain frozen until P0 semantic/resource gate is resolved.

Adoption requires later evidence across quality, model bytes, active compute, peak RSS, learning time, CPU generation speed, quantization tolerance, and 3-seed stability. None is established here.

## Evidence boundary

This audit completes a theorem/assumption and scaling comparison for the paper/raw semantic split. It does not show that PAPER-BLOCK improves quality or efficiency, does not establish a minimum successful model size, and does not claim novelty, intelligence principles, capability progress, or achievement of the 1GB target.