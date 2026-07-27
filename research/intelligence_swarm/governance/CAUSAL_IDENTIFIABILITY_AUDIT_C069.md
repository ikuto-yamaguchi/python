# Causal Identifiability Audit C069

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the declared observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes prior-art-matrix refinement, theorem/assumption comparison, public-code availability audit, and an identifiability boundary/counterexample.
- Numerical reproduction is not started.

## Decision-relevant question

C068 established that a paired three-view finite latent-class model can identify relative language–causal class coupling under conditional independence and Kruskal-rank conditions. It left a major concern:

> Interactive language and causal trajectories are sequentially dependent, so does temporal dependence itself place the problem outside existing identifiability theory?

The answer is no. Finite-state nonparametric hidden Markov models already provide identifiability results for dependent sequential observations under a different set of assumptions.

## Primary prior art

Élisabeth Gassiat, Alice Cleynen, and Stéphane Robin, **“Finite state space non parametric Hidden Markov Models are in general identifiable”**, *Statistics and Computing* 26, 2016, pp. 61–76.

Primary sources:

- Springer DOI: https://doi.org/10.1007/s11222-014-9523-8
- arXiv: https://arxiv.org/abs/1306.4657

The paper studies finite-state hidden Markov models whose emission distributions are not restricted to a parametric family. Under a full-rank transition matrix and linearly independent emission distributions, the model parameters are identifiable from a finite block of consecutive observations, up to permutation of the hidden-state labels. A related result under pairwise distinct emissions uses a longer observation block.

The key point for C069 is structural: consecutive observations need not be conditionally independent given one static episode class. Their dependence is represented by a latent Markov chain, and the transition/emission law can still be identifiable under explicit rank and separation conditions.

## RQ-001 interpretation

Let the hidden process `H_t` represent a time-varying joint grounded state, and let an observed symbol `O_t` contain a language event, intervention response, sensor result, or a grouped observation at time `t`.

A finite nonparametric HMM has:

- a finite hidden state set;
- a transition matrix `Q` for `H_t -> H_{t+1}`;
- one emission distribution for each hidden state;
- a stationary or otherwise specified initial law.

Under the theorem’s assumptions, the distribution of a sufficiently long observed block identifies the hidden transition law and emission distributions up to one common hidden-state permutation.

Therefore, the following are not intrinsically new:

- identifying a finite latent state sequence from dependent temporal observations;
- learning nonparametric state-specific language or sensor emissions;
- identifying a hidden transition matrix without observing state labels;
- using several consecutive time points instead of three conditionally independent simultaneous views;
- claiming that sequential dependence alone makes relative cross-view grounding non-identifiable.

## What the theorem can identify for a grounded sequence

If each hidden state corresponds exactly to a stable joint language–causal class, and the observed emission law contains enough information to distinguish those states, then an HMM theorem can identify:

- the number of states when separately known or consistently selected under an additional result;
- the transition probabilities between latent classes;
- the class-conditional distribution of raw language and causal observations included in each emission;
- temporal coupling of those classes across a sequence;

up to simultaneous hidden-state permutation.

This is a genuine extension beyond C068’s static latent-class comparison: temporal dependence is not merely tolerated but modeled as part of the identifying structure.

## Why this still does not solve the declared RQ

The HMM hidden state is whatever minimal predictive state makes the observed sequence Markovian under the model. It is not automatically the desired semantic equivalence class or intervention-target block.

The theorem does not by itself establish:

- that one hidden state equals one raw-language meaning class;
- that one hidden state equals one intervention target;
- that the language and causal portions of an emission arise from the same semantic factor rather than a larger episode state;
- that polysemy, synonymy, context, speaker policy, and environment state have been separated correctly;
- that the hidden-state count equals the ontology size;
- that external physical orientation or names are identified.

A model may be identifiable as an HMM while identifying an enlarged state such as `(target, context, policy mode, speaker strategy)` rather than `target` alone.

## Identifiability boundary 1: predictive-state refinement is not semantic equivalence

Suppose one semantic target `p` is expressed differently in two contexts `s_1` and `s_2`, and the future observation law differs by context even after conditioning on `p`.

An identifiable HMM may require two states:

- `h_1 = (p, s_1)`;
- `h_2 = (p, s_2)`.

The HMM can recover both states and their transition/emission laws perfectly. Nevertheless, raw utterances emitted from `h_1` and `h_2` may be semantically equivalent with respect to the intervention target.

Thus:

> HMM-state identifiability can over-refine raw-language equivalence and target partition.

Identifying the predictive state does not identify which recovered states must be quotiented together semantically.

## Identifiability boundary 2: state aliasing and rank failure

If two proposed target states have identical emission distributions and identical transition rows and columns as observed through the available process, they are observationally aliased.

Then the data cannot distinguish:

- one target state with synonymous utterances;
- two distinct semantic target states with duplicated transition and emission laws.

This is the sequential analogue of the merge/split boundary from C068. It appears as transition-rank failure, emission linear dependence, or duplicated predictive laws.

No increase in sequence length removes an exact aliasing that preserves the full process law.

## Identifiability boundary 3: language and causal components may remain internally recodable

Assume the complete HMM law is recovered up to hidden-state permutation. Within each state, let the observed emission be a joint pair `(L_t, C_t)`.

If the theorem is applied only to the joint emission distribution, it can identify that distribution state by state. It does not necessarily identify an internal factorization into:

- a raw-language equivalence component `Q`;
- a latent intervention-target component `P`;
- a denotation map `d`.

Two models may share the same state-specific joint emission and transition law while using different latent internal partitions, provided those partitions integrate to the same observable emission distribution.

Therefore:

> Identifiable sequential predictive states do not automatically imply identifiable internal semantic partitions.

## Identifiability boundary 4: context-dependent denotation

If the same utterance denotes different targets depending on history, a time-homogeneous mapping `d: Q -> P` is misspecified.

An HMM can represent the distinction by splitting hidden states according to history-relevant context, but then the recovered object is a contextual denotation such as:

`d(q, h_t) -> p`,

not the declared context-free map.

Conversely, forcing one context-free class may merge states that the observed transition law distinguishes. The RQ must therefore specify whether denotation is static, history-indexed, or policy-indexed before identifiability can be judged.

## Theorem/assumption comparison

| Setting | Dependence model | Main guarantee | Residual issue for RQ-001 |
|---|---|---|---|
| Three-view finite latent class | views conditionally independent given one static hidden class | class weights and view laws up to common permutation under Kruskal rank | unrealistic independence, static class, no contextual denotation |
| Finite nonparametric HMM | observations emitted from a finite latent Markov chain | transition and emission laws up to state permutation under rank/separation assumptions | hidden predictive state may over-refine semantics; internal `Q/P/d` factorization not guaranteed |
| Language dynamics/world models | arbitrary learned sequential predictor | predictive performance, not generally parameter identifiability | latent coordinates and semantic ontology may remain non-unique |
| Unknown-target CRL | multiple observational/interventional environments | causal coordinates or targets under intervention assumptions | language equivalence and sequential context coupling not automatically identified |

## Prior-art matrix refinement

C069 adds a new distinction to the matrix:

1. **Static multi-view identification**: dependence is removed by conditioning on one hidden class.
2. **Sequential latent-state identification**: temporal dependence is explained by a hidden Markov transition law.
3. **Semantic quotient identification**: recovered predictive states are grouped into raw-language and intervention-target equivalence classes.
4. **External semantic orientation**: recovered classes are tied to independently fixed physical meanings.

Items 1 and 2 have substantial classical identifiability theory. Items 3 and 4 do not follow automatically from either theorem family.

## Public-code availability audit

The primary paper is a theorem and statistical-method paper. The primary records inspected for C069 do not declare a paper-specific official GitHub repository. A GitHub repository-title search for the exact paper title returned no repository.

Classification:

> Primary theorem and proof are public; no paper-specific official implementation was identified for this run.

No unofficial HMM implementation or numerical experiment is started. Such work would be a faithful reimplementation or theorem-boundary control and requires explicit baseline selection and preregistration first.

## Decision

**NARROWED BEYOND FINITE NONPARAMETRIC HMM IDENTIFIABILITY — NOT ADOPTED.**

The candidate RQ is narrowed to:

> Beyond identifiable finite sequential predictive-state models, can one identify the semantic quotient that merges or separates recovered temporal states into raw-language equivalence classes and latent intervention-target blocks, while allowing context-dependent language, uncertain ontology size, intervention uncertainty, and non-HMM history dependence? The claim must distinguish identification of a predictive state process from identification of `Q`, `P`, and denotation `d`.

## Decision progress

C069 makes a material correction and narrowing rather than adding another generic relabeling example.

1. Sequential dependence alone is not an open identifiability problem; finite nonparametric HMMs provide established guarantees under rank and emission-separation assumptions.
2. The remaining issue is not merely dependent views. It is whether the identifiable predictive state admits an identifiable semantic quotient and language–target factorization.
3. The next admissible run should do at least one of:
   - find a theorem identifying state aggregation or minimal predictive-state quotients relevant to semantics;
   - audit a public sequential grounding baseline and test whether its hidden state is target-minimal or context-refined;
   - preregister a theorem-boundary HMM reproduction with direct state/target/utterance partition metrics;
   - construct a concrete countermodel where the full HMM is identifiable but two distinct semantic quotient maps remain observationally equivalent.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code availability audit: completed.
- Identifiability boundary/counterexample: completed.
- Finite nonparametric HMM identifiability: established prior art under rank/separation assumptions.
- Sequential dependence as a universal obstacle: rejected.
- Predictive-state-to-semantic-quotient identification: not established.
- External semantic orientation: not established.
- RQ-001: narrowed and not adopted.
- Public baseline reproduction: not started in this run.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
