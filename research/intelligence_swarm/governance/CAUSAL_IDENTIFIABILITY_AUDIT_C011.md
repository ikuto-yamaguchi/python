# Causal Identifiability Audit C011

Date: 2026-07-25
Track: C — causal grounding / world identity / counterfactuals
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **identifiability counterexample + theorem/assumption comparison**.

No new architecture, toy operation/goal mechanism, hand-authored ontology, intervention-target label, memory mechanism, pretrained language model, benchmark branch, or stacked PR was introduced.

## Question under audit

C010 retained one final theory candidate:

> observable relations derived from raw utterance form might remove a causal-model symmetry that survives complete non-language trajectories and every finite auxiliary-index representation.

This cycle audits whether that statement is coherent on a finite benchmark and whether it lies outside existing auxiliary-variable, grouping, multi-view, unknown-target-intervention, and causal-abstraction results.

## Finite-index collapse proposition

Let a benchmark contain a finite set of observed utterances

\[
\mathcal{L}_{obs}=\{\ell_1,\ldots,\ell_n\}.
\]

Let `R(L)` denote **any** deterministic feature, relation signature, parse, token pattern, graph, equivalence class, or compositional descriptor computed only from the observed raw utterance strings. Then there exists a finite auxiliary variable

\[
U = \phi(L)
\]

with at most `n` values (or at most the number of distinct relation signatures) such that `R(L)` is measurable with respect to `U`.

The trivial construction is `U = index(L)`; a smaller construction takes `U` to be the equivalence class induced by equal relation signatures. Therefore, on a fixed finite dataset, no empirical result can establish that a raw-string relation is outside **every finite auxiliary-index representation**.

This is not a computational limitation. It is a representation fact: every finite observation table can be losslessly encoded by a finite index.

## Consequence for the previous surviving claim

The C010 phrase

> survives ... every finite auxiliary-index representation

is too strong and makes the proposed positive construction impossible on any finite benchmark. If the estimator is allowed an unrestricted finite `U`, choosing `U=L` or `U=index(L)` reproduces all raw-string information exactly.

Thus a benchmark result showing that language helps after conditioning on a selected environment ID, paraphrase class, or metadata field cannot prove that language contributes information unavailable to **all** finite auxiliary variables. It proves only that the chosen control variable was insufficient.

## Counterexample to finite-sample language-specific identifiability

Consider two latent causal models `M_1` and `M_2` that produce the same complete non-language trajectory `X` and the same finite collection of utterances `L` on the benchmark support. Suppose a proposed language relation `R` separates their claimed latent partitions.

Define

\[
U=(L,R(L)).
\]

Because the benchmark support is finite, `U` is finite. Any estimator using `(X,L,R)` can be rewritten as an estimator using `(X,U)` with identical predictions and identical population distribution on that support.

Therefore the observation that `R` refines a causal equivalence class does not, by itself, distinguish a language-specific identifiability theorem from an auxiliary-variable theorem. The distinction must come from **restrictions on the admissible auxiliary family** and from **out-of-support population structure**, not from the finite training table.

## Required repair: population-level structural claim

A coherent surviving research question must replace “every finite auxiliary index” with a restricted population-level comparison. At minimum it must specify:

1. a generative family for an unbounded or recursively compositional utterance space;
2. which statistics of language are observable without semantic oracle labels;
3. a restricted auxiliary class `\mathcal{U}` that cannot simply copy the full string;
4. an equivalence relation over causal models under the joint population distribution, not only the empirical sample;
5. a generalization requirement to unseen utterance forms, unseen compositions, or unseen intervention combinations;
6. a proof that the language relation removes a causal symmetry while every `U in \mathcal{U}` does not;
7. a comparison against multi-view and auxiliary-variable identifiability under the same observation assumptions.

Without these restrictions, “raw language contributes more than an auxiliary variable” is not a falsifiable or novel statement.

## Latest primary-work comparison

### Unknown intervention targets from heterogeneous environments

Yang, Salehkaleybar, and Kiyavash (AISTATS 2024) recover changed exogenous noises and match them to endogenous variables under sufficient assumptions; with latent confounding they return a candidate superset rather than unique targets.

Primary source:

- https://proceedings.mlr.press/v238/yang24d.html

Implication: unknown target identity is already identifiable in non-language settings under causal sufficiency and distribution-change assumptions. Language must resolve a precisely stated residual ambiguity, not merely name environments.

### General nonparametric CRL with uncoupled interventions

Varici et al. (AISTATS 2024) establish latent-model recovery under two hard uncoupled interventions per node, without knowing which intervention environments share a target.

Primary source:

- https://proceedings.mlr.press/v238/varici24a.html

Implication: lack of paired target labels is not itself the unresolved contribution.

### Arbitrary subset interventions identify only an abstraction

Li, Kaba, and Ravanbakhsh (AISTATS 2025) characterize how arbitrary subset interventions identify a causal model only up to an abstraction determined by the intervention family.

Primary source:

- https://proceedings.mlr.press/v258/li25g.html

Implication: the natural target of the current RQ may be refinement of an intervention-induced causal abstraction, not recovery of an exact latent partition. Any language theorem must state which abstraction cell is split and why.

### Coarsened graphs with unknown intervention targets

Madaleno, Misra, and Markham (CLeaR 2026) give graphical identifiability results and a consistent algorithm for learning abstract causal graphs from interventional data with unknown targets.

Primary source:

- https://proceedings.mlr.press/v323/madaleno26b.html

Implication: coarse latent partitions and unknown targets now have a direct 2026 abstraction literature. A language-based proposal must outperform or refine the identifiable coarsening under matched assumptions.

### Finite-sample unknown-target CRL

Lee, Jin, and Aragam (2026 preprint) provide finite-sample guarantees with a sublinear number of environments and unknown multi-node intervention targets.

Primary source:

- https://arxiv.org/abs/2603.25796

Implication: finite environment count and unknown multi-node targets are not sufficient novelty claims. The language contribution must alter the observation model or sample complexity under explicit restrictions.

## Revised theorem/assumption matrix

| Candidate claim | Why current form fails | Existing closest boundary | Required nontrivial form |
|---|---|---|---|
| Raw strings contain information beyond every finite auxiliary index | Any finite string table can be encoded by `U=index(L)` | Auxiliary-variable nonlinear ICA / generalized contrastive learning | Restrict admissible `U` and prove population-level out-of-support separation |
| Language identifies exact intervention partition | Intervention family may identify only a causal abstraction | Causal-abstraction and coarsening results | State the exact abstraction class and the cell refined by language |
| Unknown target labels create novelty | Unknown and uncoupled targets already have identifiability guarantees | Varici 2024; Yang 2024; Madaleno 2026 | Show a residual ambiguity remaining under their assumptions |
| Finite benchmarks demonstrate language-specific identifiability | Empirical lookup tables cannot distinguish language structure from indexing | Finite-sample CRL and auxiliary-variable results | Require unseen-form/composition/intervention generalization |
| Correct-vs-shuffled language proves causal grounding | It can detect dependence or environment pairing only | Generalized contrastive learning | Prove elimination of a specified causal-model symmetry |

## Decision on RQ-001-T1

### Decision: CURRENT FORM REJECTED; ONE REFORMULATION ALLOWED

Rejected formulation:

> raw utterance relations eliminate a symmetry surviving every finite auxiliary-index representation.

Reason: on finite support, the full raw string and all derived relations can always be represented by a finite auxiliary index. The condition is impossible to demonstrate empirically and cannot define novelty without restricting the auxiliary family.

Only admissible reformulation:

> Under an explicitly specified population grammar and a restricted auxiliary class that cannot copy utterance identity, determine whether observable compositional relations among previously unseen utterance forms refine a known intervention-induced causal abstraction beyond complete non-language trajectories, and prove the refinement under matched assumptions.

This reformulation is **not adopted**. It is allowed only as a final preregistration candidate and must be rejected if it requires oracle semantics, handcrafted slots, target labels, or a lookup-equivalent language representation.

## Preregistration requirements before any experiment

A future C-cycle may propose the reformulation only if it supplies all of:

- formal population language generator;
- explicit admissible auxiliary class `\mathcal{U}`;
- exact causal-model equivalence relation;
- known abstraction remaining after the available intervention family;
- positive construction on unseen utterance forms;
- matched negative construction;
- proof sketch and falsification condition;
- benchmark split that prevents utterance-identity lookup;
- prior-art comparison through relevant 2026 primary work.

No architecture or synthetic benchmark implementation is authorized before that preregistration and before an external public capability baseline is reproduced.

## Resource accounting

This cycle is theory/prior-art audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are therefore not applicable in this cycle and remain mandatory immediately when an experiment begins.

## Status

- Public capability baseline reproduced: no
- Empirical Gate I: rejected
- RQ-001-T1 current formulation: rejected
- Population-level restricted-auxiliary reformulation: allowed for preregistration only, not adopted
- Completed this cycle: identifiability counterexample and theorem/assumption comparison
- New architecture: none
- Novelty: not established
- Intelligence principle: not discovered
- Capability progress: not recognized
- High-school-level intelligence: not achieved
