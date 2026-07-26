# Causal Identifiability Audit C055

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + assumption/observation/guarantee comparison + official-code availability audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Language in a (Search) Box: Grounding Language Learning in Real-World Human-Machine Interaction

Federico Bianchi, Ciro Greco, and Jacopo Tagliabue. NAACL 2021.

Primary records:

- ACL Anthology: https://aclanthology.org/2021.naacl-main.348/
- DOI: https://doi.org/10.18653/v1/2021.naacl-main.348
- arXiv: https://arxiv.org/abs/2104.08874
- paper-declared repository: https://github.com/coveooss/naacl-2021-grounded-semantics

The work learns a language-independent product grounding space from shopping sessions, maps queries or lexical items to regions in that space using click behavior, and learns compositional functions over the resulting dense denotations. It is one of the closest prior-art examples to the interactive-language component of RQ-001 because the cross-system link is induced by real user-machine interaction rather than by a manually supplied semantic label.

## Observations, assumptions, and guarantees

Let:

- `U` be a raw query or lexical expression;
- `O` be a product or product embedding;
- `C` be an observed click or behavioral interaction;
- `Q` be the unknown raw-language equivalence relation required by RQ-001;
- `P` be the unknown latent intervention-target partition;
- `d: U/Q -> P` be the target denotation map.

### Observations available in the audited work

The learner receives:

- product co-occurrence in shopping sessions;
- queries issued to a search engine;
- ranked result pages produced by the search system;
- user clicks and other behavioral interactions;
- a product catalog and a fixed product inventory;
- query-level aggregate click sets or weighted product embeddings.

The learner does not observe a latent causal SCM over intervention targets, controlled interventions on latent variables, or an independently verified semantic ontology.

### Assumptions embedded in the interaction channel

The grounding interpretation depends on several assumptions:

1. the product embedding space is a meaningful language-independent grounding domain;
2. clicked products are informative about the intended denotation of the query;
3. the search engine exposure policy does not erase or arbitrarily distort the relevant denotation;
4. position, ranking, popularity, merchandising, availability, and interface effects are either negligible or acceptable as noise;
5. the aggregation from clicked products to a DeepSet preserves the semantic distinction of interest;
6. query compositionality is adequately represented by the chosen additive or matrix composition family;
7. the catalog ontology is sufficiently stable during the sampled period.

These are empirical grounding assumptions, not a theorem establishing joint semantic-causal identifiability.

### Guarantees actually established

The paper establishes an empirical result: interaction-derived dense denotations support compositional and zero-shot product-retrieval behavior better than the compared non-grounded baselines on the reported tasks.

It does not prove:

- unique recovery of raw-query equivalence classes;
- unique recovery of a latent intervention-target partition;
- uniqueness of the query-to-target denotation;
- elimination of ranking-policy or exposure confounding;
- recovery under arbitrary user-choice mechanisms;
- identifiability beyond transformations preserving the click law and product-space geometry;
- equivalence between click-denotation and causal intervention equivalence.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- using real user-machine interaction as weak supervision for lexical grounding;
- treating clicks as noisy pointing signals from language to extra-linguistic entities;
- constructing a language-independent dense grounding domain from behavioral sessions;
- learning lexical denotation as an aggregate over clicked object embeddings;
- learning compositional phrase denotations over a dense object domain;
- demonstrating zero-shot compositional generalization from interaction-derived denotations;
- claiming that no explicit human semantic labels are necessary for useful domain grounding;
- treating a search engine or recommendation system as a teacher-learner grounding environment.

Therefore, RQ-001 cannot claim novelty merely from replacing gold semantic labels with click, selection, or trajectory behavior.

## Boundary between weak supervision and identification

The phrase “without explicit labelling” does not imply “without semantic supervision.” The interaction channel is informative precisely because the deployed ranking and interface expose objects and users select among them.

The cross-system signal can contain:

- search-engine ranking priors;
- catalog taxonomy;
- product metadata;
- popularity and availability;
- position and presentation bias;
- user goals unrelated to literal query denotation;
- previously learned retrieval semantics embedded in the serving system.

If those components already encode the language-to-object mapping, the learned denotation is inherited supervision rather than discovery of a latent semantic partition.

For RQ-001, every such component must be classified as either:

1. legitimate observable interaction;
2. external denotational anchor;
3. nuisance/confounder;
4. semantic leakage.

## Identifiability counterexample A: exposure-policy recoding

Consider a query class set `Q = {q1,...,qm}` and product-target blocks `P = {p1,...,pm}`. Let a serving policy `S` map each query and context to a ranked exposure set, and let a user-choice law `K` map exposures and latent intent to clicks.

Model A uses denotation:

`d_A(q_i) = p_i`.

For a non-identity permutation `sigma`, construct Model B with:

`d_B(q_i) = p_{sigma(i)}`.

Simultaneously transform:

- the query-indexed serving policy;
- the product-block labels;
- the user-choice interface;
- the downstream retrieval decoder;
- all target-indexed evaluation bookkeeping.

The two models can preserve:

- every observed query distribution;
- every ranked exposure distribution;
- every click distribution;
- every query-click co-occurrence matrix;
- every product-session co-occurrence matrix;
- every DeepSet denotation vector up to the corresponding product-space recoding;
- every compositional retrieval metric;
- every zero-shot ranking metric;
- every task-success statistic computed through the same interface.

Yet the same raw query class is assigned a different external target meaning.

Therefore:

> Perfect prediction of clicks and perfect compositional retrieval do not uniquely identify denotation when the serving policy, object interface, and target labels admit a simultaneous recoding.

## Identifiability counterexample B: identical click law, different semantic equivalence

Let raw queries `u1` and `u2` induce identical exposure and click distributions in every observed context.

Construct Model A:

- `u1` and `u2` are synonyms;
- both denote one target block `p`.

Construct Model B:

- `u1` and `u2` have different intended meanings;
- they denote different latent target blocks `p1` and `p2`;
- the catalog, serving system, and admissible user interactions make `p1` and `p2` observationally indistinguishable.

Both models preserve:

- all query frequencies;
- all exposures and clicks;
- all product embeddings;
- all aggregate denotation vectors;
- all phrase-composition outputs;
- all retrieval and zero-shot metrics.

Nevertheless:

`Q_A != Q_B` and `P_A != P_B`.

Thus click-equivalent queries need not be semantically equivalent, and interaction-equivalent product targets need not be one semantic target.

## Identifiability counterexample C: selection rather than intervention

A click is an observed selection under an exposure policy, not generally an intervention on a latent causal target.

Two causal models can agree on the full observational law:

`p(U, exposure, click, product, outcome)`

while disagreeing on counterfactual responses under actions never exposed by the serving policy. In one model, two query meanings cause distinct target interventions; in another, they differ only through a latent user preference or ranking mechanism. If the available interaction never separates those alternatives, the click law does not identify the latent intervention partition.

Consequently:

> An interaction-correlated denotation is not automatically a causally identified denotation.

Controlled or otherwise identifiable interventions are required to distinguish selection effects from target effects.

## Consequence for interactive language grounding

The audit establishes a positive prior-art boundary and a negative identifiability boundary.

Positive boundary:

- real interaction can provide useful weak semantic supervision;
- a language-independent object domain plus click behavior can yield compositional denotations;
- explicit manual labels are not required for useful empirical grounding.

Negative boundary:

- weak supervision does not establish uniqueness of `Q`, `P`, or `d`;
- clicks can inherit semantics from the ranking system and catalog;
- observational user choice can be confounded by exposure and preference;
- product-space and query-space recodings can preserve all reported metrics;
- interaction-equivalent blocks remain semantically ambiguous.

## Mandatory controls introduced by C055

Before RQ adoption, a baseline or benchmark using behavioral interaction must include:

1. a language-only baseline;
2. a language-blind interaction/causal baseline;
3. a logged-policy baseline using exposure without language;
4. inverse-propensity or randomized-exposure analysis when justified;
5. a serving-policy permutation control;
6. a product-target permutation control;
7. a simultaneous query/target/interface permutation control;
8. direct evaluation of raw-language equivalence, target partition, and denotation separately;
9. held-out interventions that alter target response while preserving superficial click correlations;
10. disclosure of catalog taxonomy, ranking model, metadata, and parser leakage;
11. preregistration of which interaction breaks which residual automorphism;
12. rejection if the claimed grounding is already encoded by the serving policy or target metadata.

## Official public-code audit

The paper states that code and a curated dataset were released at:

https://github.com/coveooss/naacl-2021-grounded-semantics

At the time of C055, that repository was not retrievable through the connected GitHub API and returned `404 Not Found`. The ACL and arXiv primary records remain available, and the arXiv text explicitly names the repository.

C055 therefore records:

- paper-declared official code: yes;
- currently retrievable official repository: no through the connected GitHub API;
- immutable commit: unavailable;
- dependency lock: unavailable;
- dataset checksum: unavailable;
- canonical run manifest: unavailable;
- raw logs and seed manifest: unavailable;
- public baseline reproduction: not started.

No unofficial reconstruction was started because baseline selection and preregistration are not complete.

## Decision

**NARROWED BEYOND INTERACTION-DERIVED CLICK DENOTATION — NOT ADOPTED**

Reason:

- interaction-derived dense lexical denotation and compositional grounding are established prior art;
- the interaction channel is weak supervision and may inherit semantics from serving, catalog, and exposure mechanisms;
- observational click prediction does not identify latent intervention effects;
- click-equivalent utterances and targets can support different semantic ontologies;
- simultaneous query/target/interface recoding preserves the complete observed interaction law and reported task metrics.

## Surviving candidate after C055

> After recovering the finest raw-expression equivalence available from legitimate language-only observations, the finest target partition identifiable from legitimate non-language interventions, and the strongest denotation learnable from non-random user-machine interaction, determine whether a preregistered cross-system intervention law uniquely resolves only the remaining exposure- and response-aliased classes while eliminating every query/target/serving-policy recoding that preserves the complete language, exposure, click, causal, and outcome laws.

This candidate is not adopted. A positive result must specify an observation or intervention design whose information is not already supplied by a ranking policy, catalog ontology, parser, target label, reward, or completed trajectory.

## Next gate

Before any architecture proposal:

1. audit SILG/J-CRe3 for exposure-policy, parser, catalog, target, reward, and trajectory leakage;
2. define the complete logged interaction law and distinguish selection from intervention;
3. define the residual automorphism group after language-only, causal-only, and click-grounded baselines;
4. select a retrievable official interaction-grounding baseline or preregister a faithful non-architectural reproduction;
5. construct matched countermodels with identical language, exposure, click, and outcome laws but different `Q`, `P`, or `d`;
6. identify a non-leaking intervention that separates those countermodels;
7. directly score `Q`, `P`, and `d` rather than retrieval or task success alone;
8. reject the RQ if the required anchor simply provides the denotation being claimed as discovered.

## Claim discipline

- RQ-001: narrowed, not adopted.
- Interaction-derived lexical grounding: established prior art.
- Compositional dense denotation from clicks: established empirical prior art.
- Joint identification of raw-language equivalence and latent intervention partition: not established.
- Public baseline reproduction: not started.
- Experiment: not started.
- Model size / peak RSS / wall time / three seeds: not yet applicable.
- New architecture: none.
- Novelty claim: none.
- Intelligence-principle claim: none.
- Capability-progress claim: none.
