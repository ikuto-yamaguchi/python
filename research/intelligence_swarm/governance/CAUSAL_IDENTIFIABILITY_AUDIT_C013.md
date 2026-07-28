# Causal Identifiability Audit C013

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix precision + theorem/assumption comparison**.

No new architecture, toy mechanism, benchmark, hand-authored intervention ontology, memory mechanism, or branch was introduced.

## Primary work newly audited

### Beyond identifiability: finite-sample unknown-target CRL

Lee, Jin and Aragam, *Beyond identifiability: Learning causal representations with few environments and finite samples*, arXiv:2603.25796, 2026.

Primary source:

- https://arxiv.org/abs/2603.25796

The paper studies a high-dimensional linear observation model `X = BZ` with an unknown linear latent SEM, unknown multi-node intervention targets, and multiple environments. It supplies both an identifiability statement and finite-sample recovery guarantees.

Its central boundary is stronger than the older asymptotic unknown-target literature in one direction: under a strongly separating intervention design, an observational environment, full-column-rank linear mixing, and a noise-diversity condition, only `O(log d)` unknown multi-node intervention environments are sufficient to identify:

1. the latent causal graph, up to label permutation;
2. the latent representations, up to scale and label permutation;
3. the decoder/mixing matrix, up to scale and label permutation;
4. the unknown intervention target set in every environment, up to label permutation.

The paper further moves beyond population identifiability by constructing an estimator with explicit non-asymptotic error guarantees.

## Consequence for RQ-001

The following claim is now excluded from the admissible novelty region:

> raw language is needed to discover unknown intervention targets because non-language multi-environment data cannot recover them with practical sample guarantees.

That claim is false in the audited linear setting. Unknown targets, latent representations and the latent graph can all be recovered without language, with a logarithmic number of sufficiently separating environments and finite samples.

Language can therefore contribute to RQ-001 only after the non-language intervention family has been characterized. The research question must distinguish two cases.

### Case A — intervention family is strongly separating

If the intervention family separates every latent-variable pair in both directions and the remaining model assumptions hold, non-language data already identify the targets and representation up to the theorem's residual scale/permutation symmetry. Language cannot be credited with target discovery. At most it may attach human-readable semantics to already identified components, which is semantic alignment rather than causal identifiability.

### Case B — intervention family is not strongly separating

If some latent variables are never separated by the available environments, the non-language data generally identify only a coarser causal abstraction or equivalence class. This is the only admissible place for a language contribution: language observations would need to provably refine a specific residual abstraction that is induced by the deficient intervention family.

The burden is not to show that language correlates with targets. It is to show that, under a specified population grammar and restricted language-to-dynamics mechanism, language adds a separating relation absent from the intervention design while avoiding utterance-ID lookup and arbitrary factor recoding.

## Theorem/assumption comparison

| Dimension | Lee–Jin–Aragam 2026 | RQ-001 implication |
|---|---|---|
| Observation model | Linear full-column-rank mixing `X=BZ` | A language claim must state whether it exceeds only this linear regime or also nonlinear CRL |
| Latent dynamics | Linear acyclic SEM | Nonlinearity alone is not a novelty claim; it changes assumptions and proof burden |
| Intervention targets | Unknown, multi-node | Unknown-target recovery itself is already covered |
| Environment count | `O(log d)` under a strongly separating system | “Language reduces many required environments” needs a lower bound and comparison against logarithmic non-language designs |
| Statistical guarantee | Explicit finite-sample consistency/error analysis | A benchmark-only language gain without sample guarantees cannot be presented as an identifiability result |
| Residual ambiguity | Scale and label permutation | Language that merely names recovered factors resolves semantics, not causal structure |
| Failure mode | Coverage/separation assumptions fail | This residual non-separation is the only clean entry point for RQ-001 |

## Refined prior-art boundary

The accumulated literature now partitions the problem as follows.

1. **Unknown single- or multi-node target recovery from non-language environments:** substantially covered under multiple linear/nonlinear assumptions.
2. **Recovery under arbitrary subset interventions:** identifiable only up to an intervention-induced causal abstraction when the intervention family lacks sufficient separation.
3. **Direct learning of coarsened causal graphs with unknown targets:** covered by 2026 causal-abstraction work.
4. **Language-conditioned latent block recovery with supplied language components:** covered by WM3C.
5. **Raw language factorization jointly with refinement of a residual intervention-induced abstraction:** not covered by the audited papers, but still not identifiable without explicit grammar/mechanism restrictions.

Thus language is not an alternative to good intervention design. A valid theorem must define exactly which pairwise separations are absent from the intervention family and which observable language relations replace them.

## Updated admissible RQ

The only remaining admissible formulation is:

> Given a specified population grammar, a restricted non-lookup language-to-dynamics mechanism, and a known non-strongly-separating intervention family that identifies only a stated causal abstraction, can raw utterances provide the missing separating relations required to identify a strict refinement of that abstraction on unseen utterance forms and unseen intervention compositions?

This formulation is **not adopted**. It is a preregistration candidate only.

## Required rejection and adoption tests

Reject the candidate if any of the following holds:

1. the non-language intervention family is already strongly separating;
2. the claimed improvement is only naming/permutation alignment;
3. utterance identity or environment identity can reproduce the result;
4. language components or target blocks are supplied as labels;
5. the language relation does not generalize to unseen forms and tuples;
6. the result is merely a special case of auxiliary-variable, multi-view or WM3C identifiability;
7. no finite-sample or at least consistent estimator accompanies the population theorem.

Adoption would require all of:

1. an explicit deficient intervention design and its residual causal abstraction;
2. a population grammar that prevents finite utterance lookup;
3. restrictions excluding arbitrary merging/splitting/re-encoding of language factors;
4. a positive theorem showing language strictly refines the abstraction;
5. a matching impossibility theorem when the language-separation condition is removed;
6. held-out utterance-form, component-tuple and intervention-target tests;
7. direct comparison with logarithmic-environment unknown-target CRL and causal-abstraction baselines.

## Decision on RQ-001

### Decision: NARROWED TO RESIDUAL-ABSTRACTION REFINEMENT — NOT ADOPTED

Unknown intervention-target recovery is no longer an admissible headline contribution. The only remaining theoretical possibility is refinement of a precisely characterized abstraction left by a deliberately non-separating intervention family.

No experiment or architecture is authorized before external baseline reproduction and a preregistration satisfying the conditions above.

## Resource accounting

This cycle is theory and primary-literature audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art matrix precision and theorem/assumption comparison
- unknown-target recovery as language contribution: rejected
- residual-abstraction refinement formulation: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
