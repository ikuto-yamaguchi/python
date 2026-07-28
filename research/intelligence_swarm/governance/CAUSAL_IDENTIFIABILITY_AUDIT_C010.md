# Causal Identifiability Audit C010

Date: 2026-07-25
Track: C — causal grounding / world identity / counterfactuals
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **theorem/assumption comparison + attempted positive-construction audit**.

No new architecture, toy operation/goal mechanism, hand-authored ontology, intervention target label, memory mechanism, pretrained language model, or branch was introduced.

## Question under audit

After C009 established that environment-index-reducible language cannot refine a latent intervention partition, does adding *relations among utterances* create a genuinely new identifiable setting?

The candidate RQ-001-T1 suggested that raw utterance relations not measurable from an environment index might break a trajectory-only causal equivalence class. This cycle tests whether that idea is already covered by grouping, weak supervision, auxiliary-variable nonlinear ICA, or multi-view identifiability.

## Candidate positive construction

Let `X` be the complete non-language trajectory and `E` the observed environment index. Suppose two latent causal models `M_1` and `M_2` are observationally equivalent under `(X,E)`.

For each episode, a raw utterance `L` is observed. In addition to the individual utterance, the dataset reveals a relation

\[
R(L_i,L_j)\in\{0,1\},
\]

where `R=1` means that the two utterances describe the same latent intervention component or the same mechanism-changing factor, despite differing surface forms and possibly occurring in different environments.

If the relation is independently generated from the true latent component identity, then it can rule out a competing model whose partition groups the episodes differently. This appears to provide a positive construction: `(X,E)` leaves two partitions equivalent, while `(X,E,L,R)` selects one.

However, the construction does **not** establish the proposed raw-language novelty.

## Why the construction is not yet a new result

### 1. The relation is weak supervision unless derived without semantic labels

If `R` is supplied by an annotator, paraphrase label, intervention label, shared class, or any oracle that already knows which utterances refer to the same factor, then the identifying information is the supplied grouping relation rather than raw language.

This reduces the proposal to weakly supervised representation learning. The scientific claim would be:

> a correct equivalence/group label can identify or help identify latent causal factors.

That is not the intended unsupervised joint-identification claim.

### 2. Grouping of observations already yields CRL identifiability

Morioka and Hyvärinen (ICML 2024) prove causal-representation identifiability from a suitable grouping of observational variables, without temporal structure, interventions, or weak supervision in their formal setup. Their guarantee relies on structural grouping in the observation process.

Primary source:

- https://proceedings.mlr.press/v235/morioka24a.html

Therefore a future theorem cannot claim novelty merely because language induces groups or because utterance components co-occur in grouped observational channels. It must show a language-specific relational condition that is not reducible to the paper's observational grouping assumption.

### 3. Auxiliary-variable nonlinear ICA already covers randomized pair discrimination

Hyvärinen, Sasaki, and Turner (AISTATS 2019) allow an arbitrary observed auxiliary variable and learn by discriminating correct `(x,u)` pairs from randomized pairs, with identifiability under conditional-independence and variability/rank assumptions.

Primary source:

- https://proceedings.mlr.press/v89/hyvarinen19a.html

Encoding an utterance relation, paraphrase cluster, dialogue act, or group identity as `u` is therefore already covered at the level of the broad construction. Correct-pair versus shuffled-pair success does not establish a distinct causal-language theorem.

### 4. Multi-view nonlinear ICA covers sufficiently distinct correlated views

Gresele et al. (UAI 2020) show identifiability of common independent sources from multiple sufficiently different noisy views under their component-wise corruption assumptions.

Primary source:

- https://proceedings.mlr.press/v115/gresele20a.html

If the utterance relation creates a second view of the latent factor, the burden is to show that the proposed guarantee lies outside this multi-view setting rather than simply instantiating it with text.

### 5. Weakly supervised causal representation learning already uses factor and graph supervision

Shen et al. (JMLR 2022) give a weakly supervised disentangled generative causal-representation method with an SCM prior and theoretical identifiability/asymptotic justification under suitable supervision about factors and causal structure.

Primary source:

- https://www.jmlr.org/papers/v23/21-0080.html

Thus a pair/group relation that encodes factor identity or causal structure cannot be presented as evidence that raw language itself jointly identifies the partition.

### 6. Mechanism sparsity and unknown-target interventions are existing identification routes

Lachapelle et al. (CLeaR 2022) establish identifiability from sparse latent mechanisms and a graph-connectivity criterion, including a special case leveraging unknown-target interventions.

Primary source:

- https://proceedings.mlr.press/v177/lachapelle22a.html

A relation that merely reveals sparse intervention support or shared target membership must be compared against this existing route.

## Assumption comparison

| Candidate information | Existing closest result | Existing guarantee | Remaining requirement for T1 |
|---|---|---|---|
| Utterance or group ID as auxiliary variable | Auxiliary-variable nonlinear ICA | Component recovery under conditional independence and variability/rank conditions | Language relation must not reduce to an observed auxiliary index |
| Correct pair vs shuffled pair | Generalized contrastive learning | Consistent identifiable representation under model assumptions | Shuffle success must eliminate a causal-model symmetry, not only detect pairing |
| Utterance pair/group labels | Weak supervision / DEAR | Causal-factor recovery under supplied supervision and SCM assumptions | Relation must be obtained without oracle factor or graph labels |
| Multiple text/trajectory views | Multi-view nonlinear ICA | Shared-source recovery under sufficiently different component-wise corruptions | Guarantee must use language relations outside ordinary multi-view assumptions |
| Grouped observational channels | Grouping-based CRL | Causal representation identifiability from observation grouping | Relation must not merely instantiate known grouping structure |
| Shared intervention support | Mechanism sparsity / unknown-target intervention CRL | Recovery up to stated equivalence under sparsity/connectivity assumptions | Language must resolve ambiguity not already resolved by support sparsity |

## Refined impossibility statement

Let `G` denote all pair, cluster, paraphrase, or relational metadata derived from language. If there exists a statistic `U` such that

\[
G \perp M \mid X,E,U
\]

and `U` is an observed or oracle-supplied auxiliary/group label, then any refinement of the causal equivalence class is attributable to `U`, not to raw-language semantics.

More strongly, if two causal models induce the same joint distribution

\[
p(X,E,U,G,L),
\]

then no estimator can select between their latent intervention partitions. Surface compositionality, a powerful language encoder, or successful relation prediction cannot overcome that equality.

Therefore a valid positive construction must exhibit two models that:

1. agree on the full non-language record `(X,E)`;
2. cannot be separated by any finite environment/group/class index available to the estimator;
3. disagree on a relation among raw utterances generated from independently defined intervention effects;
4. become distinguishable from the *joint relational structure* of utterances;
5. are not an instance of existing auxiliary-variable, grouping, multi-view, measurement-model, or weak-supervision identifiability.

No such construction has been established in the repository or in this audit.

## Consequence for RQ-001-T1

The attempted positive construction fails as a novelty witness because its identifying relation is either:

- an oracle grouping/weak-supervision label;
- an auxiliary variable;
- a second noisy view;
- an observational grouping assumption; or
- intervention-support information already covered by existing CRL theory.

### Decision: NARROWED TO A FINAL THEORY TEST — NOT ADOPTED

Retained candidate:

> Determine whether relational constraints derived from raw utterance form alone, without oracle paraphrase, target, environment, group, or graph labels, can eliminate a causal-model symmetry that survives complete non-language trajectories and every finite auxiliary-index representation; otherwise reject RQ-001-T1 as subsumed or non-identifiable.

This candidate remains unadopted because:

- the exact negative construction from C009 remains valid;
- the first positive construction reduces to existing weak supervision/grouping;
- no language-specific sufficient condition has been proved;
- no theorem separates the candidate from auxiliary-variable nonlinear ICA, multi-view nonlinear ICA, grouping-based CRL, mechanism-sparsity CRL, or heterogeneous measurement identifiability;
- empirical Gate I remains rejected;
- R0 public capability baseline remains unreproduced.

## Required next C-cycle

Allowed work:

- formalize the equivalence relation over causal models when arbitrary finite auxiliary indices are quotiented out;
- attempt one final positive construction using only observable raw-string relations and independently measured intervention effects;
- compare that construction against grouping-based CRL and weakly supervised causal representation learning theorem assumptions;
- reject RQ-001-T1 if the construction again requires oracle semantic equivalence or reduces to an auxiliary/group variable.

Forbidden work:

- new architecture;
- synthetic operation/goal benchmark implementation;
- hand-authored paraphrase, target, mechanism, or semantic slots;
- adding intervention labels to SILG or J-CRe3;
- treating language-shuffle performance, clustering quality, compression, or representation visualization as identifiability.

## Resource accounting

This cycle is theorem/prior-art audit only; no model experiment was started. Therefore model bytes, peak RSS, training wall time, CPU inference latency, and three-seed experimental reporting are not applicable in this cycle. They remain mandatory immediately when an experiment begins.

## Status

- Public capability baseline reproduced: no
- Empirical Gate I: rejected
- RQ-001-T1: narrowed to final theory test, not adopted
- Completed this cycle: theorem/assumption comparison and failed positive-construction audit
- New architecture: none
- Novelty: not established
- Intelligence principle: not discovered
- Capability progress: not recognized
- High-school-level intelligence: not achieved
