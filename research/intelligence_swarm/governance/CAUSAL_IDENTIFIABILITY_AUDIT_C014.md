# Causal Identifiability Audit C014

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **theorem/assumption comparison + identifiability exclusion test**.

No new architecture, toy mechanism, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Causal representation learning from general environments

Ng, Xie, Dong, Spirtes and Zhang, *Causal Representation Learning from General Environments under Nonparametric Mixing*, AISTATS 2025.

Primary source and public software entry:

- https://proceedings.mlr.press/v258/ng25a.html
- software link exposed by the PMLR record

The work studies nonlinear latent causal models under nonparametric observation mixing and does not require the environments to be labelled as known single-node, coupled, or hard interventions. Under sufficient changes in causal mechanisms, expressed through derivative conditions, it identifies the latent DAG and latent variables up to the paper's residual indeterminacies.

### Causal abstraction under arbitrary intervention subsets

Li, Kaba and Ravanbakhsh, *On the Identifiability of Causal Abstractions*, AISTATS 2025.

Primary source:

- https://proceedings.mlr.press/v258/li25g.html

The work characterizes the finest causal abstraction identifiable from before/after contrastive pairs when interventions may affect arbitrary subsets. The attainable granularity is determined by the available intervention family rather than by the encoder architecture.

## Consequence for RQ-001

The following additional claim is excluded from the admissible novelty region:

> raw language is needed because non-language causal representation learning requires known intervention labels, single-node targets, linear mixing, or a parametric latent model.

This is false as a general headline. Ng et al. already provide identifiability under general environment changes, nonlinear latent causal models, and nonparametric mixing when the mechanism changes are sufficiently informative. Li et al. separately characterize the residual abstraction when the intervention family is not sufficiently separating.

Language can therefore be credited with a causal-identifiability contribution only if it supplies **new observable variation that is not already measurable from the environment-indexed transition distributions**. Merely predicting an environment ID, describing a domain, or correlating with an intervention family does not satisfy this requirement.

## Conditional-sufficiency exclusion

Let:

- `X` denote all non-language observations available to the estimator, including before/after states, actions and history;
- `E` denote the observed environment or domain index when present;
- `M` denote the latent mechanism/target partition to be identified;
- `L` denote the raw utterance.

If language is conditionally generated only from already observed non-language information,

`L ⟂ M | (X, E)`, 

then

`p(X,E,L | M) = p(L | X,E) p(X,E | M)`.

For any two candidate latent models `M1` and `M2` that are observationally equivalent under `(X,E)`, the language factor is identical and therefore cannot split their equivalence class. In information terms,

`I(M ; L | X,E) = 0`.

This remains true when `L` contains fluent paraphrases, long descriptions, compositional surface forms, or a recoverable environment label. Surface complexity is not an identifiability condition.

## Stronger rejection test

A proposed language benefit must now survive both of the following baselines:

1. **general-environment CRL baseline:** use all measurable distributional/mechanism changes in non-language data without assuming known target labels;
2. **causal-abstraction baseline:** compute the finest abstraction supported by the actual intervention family.

The candidate is rejected if language only:

- recovers `E` or an equivalent domain label;
- names a latent component already recovered up to permutation;
- improves finite-sample estimation without changing the population equivalence class;
- acts as an auxiliary view whose information is a deterministic/stochastic function of `(X,E)`;
- exploits utterance identity, target labels, paraphrase labels, or supplied language components.

Finite-sample efficiency may still be a useful engineering result, but it must not be called causal identifiability unless the population equivalence class is strictly reduced.

## Refined theorem/assumption comparison

| Dimension | General-environment CRL | Causal-abstraction result | Remaining RQ-001 burden |
|---|---|---|---|
| Environment metadata | Known target labels not required | Intervention family determines abstraction | Language must add a relation unavailable from environment distributions |
| Mixing | Nonparametric | Contrastive observable pairs | Nonlinearity/nonparametric mixing is not novelty by itself |
| Latent mechanisms | Nonlinear ANM/heteroscedastic families under sufficient change | Arbitrary subset interventions | Specify a deficient change/intervention design and residual equivalence class |
| Guarantee | Latent DAG and variables up to residual indeterminacies | Finest identifiable abstraction | Prove a strict language-induced refinement, not only better prediction |
| Language role | None | None | Must violate conditional sufficiency relative to all non-language observations |
| Empirical requirement | Measure mechanism changes | Measure intervention-family coverage | Hold out utterance forms/compositions and rule out environment-ID lookup |

## Updated admissible RQ

The only remaining admissible formulation is:

> Given a specified population grammar and a restricted language-to-mechanism channel, can raw utterances reveal an independently observable separating relation that is absent from all non-language general-environment change statistics, thereby strictly refining the causal abstraction induced by a specified deficient intervention family on unseen utterance forms and unseen intervention compositions?

This formulation is **not adopted**. It is a preregistration candidate only.

## Adoption conditions

Adoption requires all of:

1. a formal non-language observation model and its residual equivalence class;
2. proof that the intervention/environment family fails the sufficient-change or separation conditions;
3. a language channel satisfying `I(M;L | X,E) > 0` under the stated model;
4. a positive theorem that the added language relation strictly refines the abstraction;
5. a matching counterexample when the language-separation condition is removed;
6. no utterance-ID, environment-ID, target-label, supplied-component or paraphrase-label shortcut;
7. population-level unseen-form and unseen-composition generalization;
8. comparison against general-environment CRL and causal-abstraction baselines;
9. a consistent estimator or explicit finite-sample statement.

Note that `I(M;L | X,E) > 0` is necessary here but not sufficient: the information may still fail to remove the relevant symmetry.

## Decision on RQ-001

### Decision: NARROWED TO LANGUAGE-ADDED SEPARATION BEYOND GENERAL-ENVIRONMENT STATISTICS — NOT ADOPTED

Unknown intervention labels, nonlinear mixing, nonlinear latent mechanisms, and unspecified general environment changes are no longer admissible reasons for claiming that language is required. The candidate survives only if language contributes an independently observable separating relation that strictly reduces a formally stated residual causal abstraction.

No experiment or architecture is authorized before external baseline reproduction and a preregistration satisfying the conditions above.

## Resource accounting

This cycle is theory and primary-literature audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: theorem/assumption comparison and conditional-sufficiency exclusion
- language as environment-label recovery: rejected
- nonlinear/nonparametric setting as headline novelty: rejected
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
