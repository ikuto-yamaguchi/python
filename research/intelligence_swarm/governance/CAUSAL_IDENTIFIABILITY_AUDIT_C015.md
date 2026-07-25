# Causal Identifiability Audit C015

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **theorem/assumption comparison + identifiability counterexample**.

No new architecture, toy mechanism, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Disentangling Dynamical Systems: Causal Representation Learning Meets Local Sparse Attention

Baumgartner, Lei, Watson and Posner, CLeaR 2026.

Primary sources:

- https://proceedings.mlr.press/v323/baumgartner26a.html
- https://arxiv.org/abs/2603.14483

The paper studies nonlinear deterministic Markovian systems

`x_(t+1) = f(x_t, theta)`

where system parameters `theta` vary between trajectories. It gives a graphical identifiability criterion under which the parameter representation is recovered from raw trajectories up to permutation and element-wise diffeomorphism.

The theorem requires, in the paper's formulation, an invertible trajectory parametrisation, path connectivity, a mechanism-sparsity comparison, sufficient variation of the transition Jacobian with respect to the parameters, and the graphical criterion

`for every i: intersection over a in Ch_G(i) of Pa_G(a) = {i}`.

The empirical estimator uses sparsity-regularised attention to expose local state-dependent causal structure. The relevant point for RQ-001 is theoretical rather than architectural: explicit intervention-target labels or language are not required when trajectory-local causal signatures separate the varying system parameters.

No official implementation repository was found from the PMLR record or the authors' public project links during this audit. Therefore no public-code reproduction is claimed in this cycle.

## Consequence for RQ-001

The following additional headline is excluded from the admissible novelty region:

> raw language is needed to identify latent mechanism or intervention partitions whenever explicit intervention labels are absent.

This is too broad. Baumgartner et al. show that raw trajectory variation and local transition structure can identify varying latent system parameters without language or supplied intervention targets when their graphical and variation conditions hold.

Language can only be credited with an identifiability contribution after the strongest applicable trajectory-only criterion has been checked and shown to fail.

## Parameter-signature baseline

Before any language claim, define the trajectory-local signature of latent parameter `theta_i` by the state coordinates whose transition mechanisms depend on it, together with the variation of the relevant Jacobian columns over the reachable state space.

If these signatures satisfy the graphical separation criterion and sufficient-variation assumptions, trajectory-only recovery is already available up to permutation and element-wise diffeomorphism. A language model that merely predicts, names or paraphrases the recovered parameter does not further refine the causal equivalence class.

Accordingly, RQ-001 must now compare against three non-language limits:

1. general-environment mechanism-change identifiability;
2. intervention-family causal-abstraction identifiability;
3. trajectory-local parameter-signature identifiability.

## Identifiability counterexample: semantic naming does not remove the residual symmetry

Assume trajectory data identify parameters only up to

`theta'_i = h_i(theta_(pi(i)))`,

where `pi` is a permutation and every `h_i` is an invertible scalar map.

Suppose the utterance is generated as a description of the already recovered parameter value or its environment role:

`L = g(theta, X, E, epsilon)`.

For any observationally equivalent reparameterisation, define

`g'(theta', X, E, epsilon) = g(H^(-1)(theta'), X, E, epsilon)`,

where `H` denotes the permutation and component-wise diffeomorphism. Then the two models induce the same joint distribution over trajectories and raw utterances:

`p(X, E, L)`.

The language can attach human-readable names to one representative of the equivalence class, but without an externally anchored language-generation restriction it cannot select the ground-truth scaling, orientation or parameter identity. This remains true even when the utterances are fluent, compositional and predictive.

Therefore:

- parameter naming is not causal identification;
- language-conditioned prediction is not a proof of symmetry removal;
- correct-utterance versus shuffled-utterance performance is not sufficient;
- an externally anchored language channel or cross-system invariant is required to eliminate the residual reparameterisation.

## Failure of the trajectory graphical criterion is also not sufficient for language

If two latent parameters have indistinguishable local child/parent signatures, the trajectory criterion may fail. That failure creates room for additional information, but does not prove that raw language supplies the missing separator.

Language must expose a relation that is not invariant under the competing joint reparameterisation. If the language generator can be transformed together with the latent parameters, the joint model remains observationally equivalent.

Thus the required language condition is stronger than conditional mutual information. It must be a **symmetry-breaking anchor condition** tied to an independently observable referent or intervention effect.

## Refined theorem/assumption comparison

| Dimension | Trajectory-local parameter CRL | Previous general-environment / abstraction baselines | Remaining RQ-001 burden |
|---|---|---|---|
| Observations | Raw trajectories across varying system parameters | Environment-indexed distributions or before/after intervention pairs | State exactly what language observes that neither trajectory source observes |
| Target metadata | Not required | Often unknown or arbitrary subset | Unknown target labels alone are not novelty |
| Identifiability driver | Local transition graph, sparsity and Jacobian variation | Mechanism changes and intervention-family separation | Prove language breaks a residual symmetry after all non-language drivers |
| Guarantee | Parameters up to permutation and element-wise diffeomorphism | Latent model or finest supported abstraction | Show strict refinement beyond these residual equivalence classes |
| Language role | None | None | Must provide an externally anchored separator, not a renamed latent code |
| Failure mode | Non-separating graphical signatures or insufficient variation | Deficient mechanism/intervention coverage | Demonstrate a positive language theorem exactly in the deficient case |

## Updated admissible RQ

The remaining admissible formulation is now:

> Given a formally specified population grammar and an externally anchored language-to-mechanism channel, can raw utterances break a residual symmetry that remains after applying general-environment, intervention-abstraction and trajectory-local parameter-identifiability criteria, thereby strictly refining a stated causal abstraction on unseen utterance forms, unseen compositions and unseen systems?

This formulation is **not adopted**. It is a preregistration candidate only.

## Adoption conditions

Adoption now requires all of:

1. a formal non-language observation model and residual equivalence class;
2. explicit evaluation of the general-environment, intervention-abstraction and trajectory-local graphical criteria;
3. proof that the chosen non-language design violates the applicable separation or sufficient-variation assumptions;
4. an externally anchored language-generation restriction that cannot be transformed jointly with the latent representation;
5. a positive theorem showing strict reduction of the residual equivalence class;
6. a matched impossibility construction when the anchor condition is removed;
7. no utterance-ID, environment-ID, target-label, supplied-component, parameter-name or paraphrase-label shortcut;
8. population-level unseen-form, unseen-composition and unseen-system evaluation;
9. a consistent estimator or an explicit statement that only population identifiability is claimed;
10. public baseline reproduction and preregistration before any architecture experiment.

## Decision on RQ-001

### Decision: NARROWED TO EXTERNALLY ANCHORED SYMMETRY BREAKING AFTER TRAJECTORY-ONLY IDENTIFIABILITY — NOT ADOPTED

Absence of intervention-target labels is no longer an admissible reason by itself for language necessity. The candidate survives only where the best non-language trajectory and multi-environment criteria leave a stated residual symmetry and a constrained language channel provably removes that symmetry.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is theory and primary-literature audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: theorem/assumption comparison and reparameterisation counterexample
- language as parameter naming: rejected as identifiability evidence
- absence of explicit target labels as language-necessity argument: rejected
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
