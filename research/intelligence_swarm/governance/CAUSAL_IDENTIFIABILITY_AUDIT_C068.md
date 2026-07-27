# Causal Identifiability Audit C068

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the declared observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes prior-art-matrix refinement, theorem/assumption comparison, and an identifiability boundary/counterexample.
- Numerical reproduction is not started.

## Decision-relevant question

C067 established that unpaired marginal alignment and recovery of a shared component do not by themselves identify the class-level language-to-target coupling.

C068 asks the complementary question:

> Is class-level coupling already identifiable from a genuinely observed cross-system joint law, without target-indexed anchor IDs, when multiple conditionally independent views are paired through one hidden class?

The answer is yes in a classical finite latent-class regime, up to simultaneous latent-label permutation and outside an exceptional parameter set.

## Primary prior art

Elizabeth S. Allman, Catherine Matias, and John A. Rhodes, **“Identifiability of Parameters in Latent Structure Models with Many Observed Variables”**, *The Annals of Statistics* 37(6A), 2009, pp. 3099–3132.

Primary sources:

- Journal DOI: https://doi.org/10.1214/09-AOS689
- arXiv: https://arxiv.org/abs/0809.5032
- IMS/JSTOR record: https://www.jstor.org/stable/25662188

The paper studies latent-structure models in which observed variables are conditionally independent given a finite hidden class. Its central finite-state result applies Kruskal's tensor uniqueness theorem to three observed groups.

For an `r`-class, three-view latent-class model with positive mixing weights, let `M_1`, `M_2`, and `M_3` be the class-conditional probability matrices and let `I_j` be their Kruskal ranks. If

`I_1 + I_2 + I_3 >= 2r + 2`,

then the latent-class weights and the three class-conditional view distributions are identifiable up to one simultaneous permutation of the `r` latent classes. The paper further gives generic-identifiability results: failure remains possible on exceptional parameter subsets, but not generically under the stated dimension/rank conditions.

## RQ-001 interpretation

A finite RQ-001 instance can be embedded into the theorem as follows.

Let a hidden class `H in {1,...,r}` represent the joint language–causal class. Observe three paired views from the same episode or entity:

1. `L`: a raw-language observation or a language feature group;
2. `C`: an intervention-response or causal-trajectory feature group;
3. `V`: a third independently generated measurement group, such as a held-out sensor or consequence view.

Assume

`L independent C independent V | H`,

in the latent-class sense, with the three class-conditional matrices satisfying the Kruskal-rank condition.

Then the joint distribution of `(L,C,V)` generically identifies:

- the latent class mixture weights;
- the distribution of raw-language observations within each latent class;
- the distribution of causal/intervention observations within each latent class;
- the distribution of the third view within each latent class;
- the shared coupling of all three views to the same latent class;

all up to one common permutation of the latent-class index.

This is stronger than unpaired shared-component recovery. The observed cross-system tensor contains dependence information that is absent from separate marginals.

## What this removes from the novelty candidate

The following cannot be claimed as new in isolation:

- identifying a finite hidden class from three conditionally independent observed view groups;
- identifying the class-conditional language and causal distributions from their paired joint law;
- recovering a common class-level coupling without naming the latent classes;
- using third-order moments or tensor uniqueness to align language and intervention-response classes;
- claiming that class-level coupling is always non-identifiable unless an external target ID is supplied;
- treating simultaneous latent-label permutation as a failure of relative cross-view coupling recovery.

Under the theorem's assumptions, the relative coupling between language, causal response, and the third view is generically identified. Only the arbitrary names of the hidden classes remain free.

## Important distinction: relative denotation versus externally named denotation

The theorem identifies a common hidden-class decomposition up to simultaneous permutation.

If `Q`, `P`, and `d` are defined only relationally—namely, a language class and a causal target block are the components attached to the same hidden class—then their coupling is identified up to relabeling.

If the claim instead requires that a recovered class be externally named as a particular physical object, human concept, unit, direction, or simulator variable, the theorem does not supply that external name. An independently fixed physical semantics would still be required for externally oriented denotation.

Therefore C068 separates two claims that prior audits had partially conflated:

- **relative joint identification**: which language distribution and causal-response distribution belong to the same hidden class;
- **external semantic orientation**: what that hidden class is called or means outside the observed multi-view law.

The first is classical prior art under finite latent-class assumptions. The second is not delivered by latent-class tensor identifiability.

## Why this does not immediately solve the declared RQ

The theorem requires strong conditions that are not yet established for SILG/J-CRe3-style data:

- a known finite number `r` of hidden classes, or a separately justified model-selection result;
- paired observations of at least three view groups from the same hidden class;
- conditional independence of the grouped views given that class;
- enough state diversity and Kruskal rank in every view;
- stationary class-conditional laws;
- no hidden confounder that creates residual dependence between views after conditioning on `H`;
- no many-to-many, context-dependent, or polysemous denotation outside the finite-class model;
- no within-class merge/split structure invisible to all three views.

Raw language and causal trajectories are especially unlikely to be conditionally independent given only a coarse target class: context, policy, environment state, speaker strategy, and history can couple them directly. Grouping variables to manufacture conditional independence must not use gold semantics or target IDs.

## Identifiability boundary 1: two paired views are generally insufficient

With only paired language and causal views, the observed probability matrix has a factorization

`P(L,C) = M_L^T diag(pi) M_C`.

Matrix factorizations of this form are generally non-unique without additional restrictions. An invertible change of latent basis can be absorbed into the two factors while preserving the same joint matrix, subject to validity constraints.

Thus paired cross-system samples alone do not yield the three-view tensor uniqueness guarantee. The third independent view or an alternative identifying restriction is substantive, not cosmetic.

## Identifiability boundary 2: duplicated class-conditional rows

Suppose two latent classes `h_1` and `h_2` have identical conditional distributions in one or more view groups, causing the Kruskal-rank condition to fail. Their mixture weights can then be redistributed or the classes can be merged/split while preserving the complete observed joint law.

For example, if two target classes induce identical language, intervention-response, and third-view distributions, then:

- Model A may represent one target class with synonymous utterances;
- Model B may represent two distinct target classes with duplicated observable laws.

No amount of data from those same views distinguishes the models.

This preserves the earlier merge/split warning, but now locates it precisely in rank failure or observational duplication rather than treating it as universal.

## Identifiability boundary 3: conditional-independence violation

Let environment state `S` directly affect both the utterance form `L` and the response trajectory `C` after conditioning on target class `H`.

Then `L` and `C` need not be conditionally independent given `H`. Fitting a three-view latent-class tensor model may produce a statistically useful decomposition, but the Allman–Matias–Rhodes guarantee no longer applies to the intended semantic class.

Adding `S` to `H` can restore conditional independence only by expanding the hidden state. That expanded class may identify episode types rather than raw-language equivalence or target semantics. This must be audited rather than assumed.

## Prior-art matrix refinement

| Line of work | Observed relation | Main guarantee | Residual issue for RQ-001 |
|---|---|---|---|
| Separate language/causal marginals | unpaired marginal sample sets | at most marginal/shared-distribution structure under additional assumptions | class coupling is absent from the observed law |
| Unaligned Shared Component Analysis | unpaired modalities with a common linear shared source | shared component recovery under structural/distributional assumptions | discrete class coupling and ontology need not be identified |
| Three-view finite latent-class identifiability | paired joint samples; three conditionally independent view groups given a finite hidden class | generically identifies mixture weights and all class-conditional view laws up to one common permutation | requires finite classes, conditional independence, rank, pairing, and does not externally name classes |
| Unknown-target CRL | observational/interventional environments | causal coordinates or target sets up to declared transformations | language coupling is not automatically present |
| AP001 oracle control | target-indexed unique signature exposed to each language class | direct lookup of class-to-target mapping | supplies target identity and is not codebook-independent discovery |

## Public-code audit

The 2009 paper is a theorem paper and does not declare a paper-specific official software repository in the primary records audited for C068.

Classification:

> Primary theorem and proof are publicly available; no paper-specific official baseline implementation was identified for this run.

No unofficial implementation or numerical experiment is started. A future reproduction may use an independently preregistered latent-class tensor-decomposition implementation, but that would be a faithful reimplementation rather than reproduction of official paper code and must not precede baseline selection/preregistration.

## Decision

**NARROWED BEYOND GENERIC THREE-VIEW LATENT-CLASS COUPLING IDENTIFIABILITY — NOT ADOPTED.**

The candidate RQ is narrowed to:

> In realistic grounded-causal data where the finite three-view latent-class assumptions are not granted, can raw-language equivalence, latent intervention-target partition, and their coupling be identified under explicitly auditable dependence, context, intervention, and view-generation conditions? Any novelty claim must lie beyond classical generic identification of paired three-view latent classes up to simultaneous permutation, and must state whether it seeks only relative coupling or externally oriented semantics.

## Decision progress

C068 corrects an overbroad residual claim from C067.

1. Class-level cross-system coupling is not universally non-identifiable: a paired three-view joint law can generically identify it under conditional-independence and Kruskal-rank conditions.
2. The true remaining problem is to justify or replace those assumptions in interactive language/causal data, handle context dependence and unknown ontology size, and distinguish relative coupling from external semantic orientation.
3. The next admissible run should either:
   - test whether an existing public grounded-language benchmark can be partitioned into three non-leaking conditionally independent views;
   - reproduce a preregistered public tensor/latent-class baseline as a theorem-boundary control;
   - find a theorem covering dependent sequential views, unknown class count, polysemy, or intervention-index uncertainty;
   - construct a counterexample showing that a proposed realistic grouping fails conditional independence or rank.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Identifiability boundary/counterexample: completed.
- Generic paired three-view finite latent-class coupling: established prior art up to simultaneous permutation.
- External semantic orientation: not supplied by the theorem.
- Applicability to sequential interactive grounding data: not established.
- RQ-001: narrowed and not adopted.
- Public baseline reproduction: not started in this run.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
