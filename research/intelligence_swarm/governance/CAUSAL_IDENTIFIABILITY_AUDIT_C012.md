# Causal Identifiability Audit C012

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix precision + theorem/assumption comparison + identifiability counterexample**.

No new architecture, toy mechanism, benchmark, hand-authored intervention ontology, memory mechanism, or branch was introduced.

## Primary work newly audited

### WM3C — language-guided composable causal components

Wang and Huang, *Modeling Unseen Environments with Language-guided Composable Causal Components in Reinforcement Learning*, ICLR 2025.

Primary sources:

- paper: https://openreview.net/forum?id=XMgpnZ2ET7
- proceedings: https://proceedings.iclr.cc/paper_files/paper/2025/hash/79d86433c2acd12b6fa98553435d226e-Abstract-Conference.html
- arXiv: https://arxiv.org/abs/2505.08361
- project page: https://www.charonwangg.com/project/wm3c/

The project page links the paper but, as inspected on 2026-07-25, does not expose an official implementation repository. Therefore this cycle audits the theorem and observation model, not code reproducibility.

## WM3C theorem assumptions

WM3C assumes a latent state

\[
\mathbf{s}_t=(\mathbf{c}_{1,t},\ldots,\mathbf{c}_{m,t})
\]

that is already uniquely partitioned into disjoint components, with one provided language component `l_i` controlling each block `c_i` through

\[
p(\mathbf{c}_{i,t}\mid l_i,\mathbf{s}_{t-1},a_{t-1}).
\]

Its block-wise identifiability theorem requires, among other conditions:

1. smooth invertible observation/reward mixing;
2. positive support almost everywhere;
3. differentiable conditional densities;
4. conditional independence of current latent coordinates given language component, previous state and action;
5. at least `dim(c_i)+1` sufficiently diverse values of each supplied language component, with an invertible derivative-difference matrix.

The guarantee is block-wise: each true language-controlled block is recovered up to an invertible transformation internal to that block.

## Direct overlap with RQ-001

WM3C already establishes a positive identifiability result for the following broad claim:

> multiple language controls can identify corresponding composable latent causal/dynamical blocks and support unseen recombinations.

Therefore none of the following can be claimed as novel by RQ-001:

- language-conditioned decomposition of latent dynamics;
- block-wise rather than coordinate-wise identifiability;
- separate language controls attached to separate latent components;
- compositional recombination of previously seen language values;
- using language to reduce the number of environment changes needed for block recovery;
- world-model or RL transfer based on language-controlled causal components.

## What WM3C assumes rather than identifies

WM3C does **not** jointly infer the two objects named in RQ-001.

It assumes:

- the utterance is already decomposed into language components `l_1,...,l_m`;
- the number of components is available;
- each language component controls one disjoint latent block;
- the latent state admits that unique partition;
- sufficient component-wise language variation is observed;
- the relevant conditional independences and smooth invertible mixing hold.

Thus WM3C identifies latent blocks **conditional on a supplied language factorization**. It does not identify raw-language equivalence classes, discover a tokenizer/grammar-level decomposition, or recover an unknown intervention-target partition jointly with that decomposition.

## Re-encoding counterexample

The remaining RQ must confront a symmetry absent from WM3C's observation model.

Let raw utterances be generated from two hidden language factors `(u,v)` and let the latent state have two corresponding blocks `(c_u,c_v)`. Suppose the learner observes only the complete raw string `L`, trajectories and actions, but is not given the decomposition into `u` and `v`.

For any bijection

\[
\psi:\mathcal U\times\mathcal V\rightarrow\mathcal W,
\]

define a single hidden factor `w=psi(u,v)` and a competing model with one language component `w` controlling the combined block `(c_u,c_v)`. The two models induce exactly the same joint distribution over raw strings, observations, actions and rewards if the surface generator is correspondingly reparameterized.

Conversely, an arbitrary finite utterance ID can be factorized into multiple pseudo-components by an invertible code. Without restrictions on the population grammar and on how language components may act on latent dynamics, the number of language equivalence classes and the latent intervention partition are not jointly identifiable.

This ambiguity is stronger than a permutation: competing explanations can have different numbers and sizes of language-controlled blocks.

## Consequence

WM3C supplies a valid positive construction only after the language decomposition and disjoint block-control structure are assumed. Removing those assumptions restores the re-encoding ambiguity above.

Therefore the current evidence supports this boundary:

- **supplied language components -> latent block identification:** substantially covered by WM3C;
- **raw strings -> joint discovery of language equivalence and unknown latent intervention partition:** not solved by WM3C, but not identifiable without additional grammar/action assumptions;
- **finite benchmark success:** cannot distinguish true compositional structure from an invertible utterance code or lookup table.

## Updated theorem/assumption matrix

| Question | WM3C status | RQ-001 implication |
|---|---|---|
| Are language-controlled latent dynamics block-identifiable? | Yes, under supplied language components, disjoint control, smooth invertible mixing, conditional independence and sufficient variation | Broad positive claim is not novel |
| Are raw utterance equivalence classes identified? | No; component decomposition is input/assumption | Remains open only under an explicit population grammar |
| Is the number of language/latent blocks identified? | No; fixed by the model | Must be preregistered or proven identifiable |
| Are intervention targets unknown? | Not in the RQ-001 sense; each `l_i` is associated with its block in the generative model | Unknown-target contribution must survive re-encoding symmetry |
| Does unseen composition prove joint identification? | No; recombination occurs over provided component values | Require unseen-form tests that prevent utterance-ID coding |
| Is official code reproducible? | No official repository was linked on the inspected project/paper pages | No public-baseline reproduction claim in this cycle |

## Decision on RQ-001

### Decision: NARROWED AGAIN — NOT ADOPTED

The remaining admissible question is:

> Under a specified population grammar and a restricted class of language-to-dynamics mechanisms, can raw utterance observations jointly identify (i) a non-lookup equivalence/factorization of utterances and (ii) a refinement of an intervention-induced latent causal abstraction, when neither the language components nor their target blocks are supplied?

This is narrower than WM3C because it removes the supplied component factorization and target-block assignment. It is also currently unsupported.

The candidate must be rejected unless a preregistration supplies:

1. a population grammar with explicit equivalence under unseen forms;
2. restrictions that rule out bijective utterance-ID recoding and arbitrary component splitting/merging;
3. an exact intervention-induced causal abstraction remaining after non-language data;
4. a positive identifiability theorem for joint language-factor and latent-block recovery;
5. a matched impossibility result when any key assumption is removed;
6. a benchmark split where utterance identity, component tuples and target blocks cannot be memorized;
7. explicit comparison to WM3C and auxiliary-variable/multi-view CRL.

No experiment or architecture is authorized before external baseline reproduction and this preregistration.

## Resource accounting

This cycle is theory and primary-literature audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art precision, theorem comparison and re-encoding counterexample
- WM3C overlap: broad language-controlled block-identifiability claim covered
- raw-language/unknown-partition joint identification: unresolved but presently unidentifiable without stronger assumptions
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
