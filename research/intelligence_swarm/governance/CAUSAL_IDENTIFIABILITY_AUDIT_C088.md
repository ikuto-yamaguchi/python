# Causal Identifiability Audit C088

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, and (d) an identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C087 fixed the target-side estimand to the exact full-consequence controlled predictive quotient and prohibited finite-sample empirical `merge` without symbolic equality or a complete point-model oracle. The resulting empirical target object is therefore generally not one partition. It is a set of exact partitions and denotations compatible with the observed controlled law, structural equalities, and all preregistered assumptions.

The question for C088 is:

> When `P` remains partially identified, what part of `d : Q -> P` is legitimately identified, and can language be used to select one completion without adding an identifying assumption?

## Primary prior art

### Manski-style partial identification

Manski's partial-identification program separates statistical uncertainty from identification. When observable evidence and maintained assumptions do not determine one parameter value, the scientific object is the identified set: all parameter values compatible with the population observation law and assumptions. Additional assumptions may shrink this set, but choosing one compatible point without such an assumption is not identification.

This directly applies to LBQ001 after C087. If finite controlled observations leave both merge-compatible and separate-compatible point models, the object is an identified set of target quotients, not a forced complete partition.

### Partial identification of finite mixtures

Henry, Kitamura, and Salanié show that latent finite-mixture components can remain partially identified even when observable variation constrains the compatible family. Their results distinguish recovery of a set of compatible latent decompositions from point identification of one component system. Unknown component count and discrete outcomes do not make arbitrary completion legitimate.

This is relevant because `Q`, `P`, and `d` form a latent decomposition/coupling problem. Recovering some invariant relations across all compatible decompositions is weaker than selecting one latent ontology, but is the correct claim when point identification fails.

### Automated sharp-bound computation

Duarte, Finkelstein, Knox, Mummolo, and Shpitser reduce discrete causal partial-identification problems to polynomial programs and provide Autobounds, which computes lower and upper bounds over all compatible data-generating processes. The important methodological precedent is not the specific causal estimand. It is the contract:

- declare observations and assumptions;
- optimize over all compatible latent models;
- return the sharp identified range or an outer range with an explicit sharpness gap;
- return a point only when the compatible set collapses.

The public repository `duarteguilherme/autobounds` provides a Python implementation, examples, tests, Docker instructions, and replication files. A paper-specific immutable commit was not fixed in this run, so it is classified as a public identified-set backend reference, not yet a canonical executable baseline.

## Joint identified-set formulation

Let `O` denote the population controlled observation law under the preregistered action/consequence interface, and let `A` denote the allowed structural assumptions, including any symbolic equality constraints.

Define the compatible model set

`M(O,A) = { M : M generates O and satisfies A }`.

Each compatible model induces

- a raw-language quotient `Q_M`,
- an exact target quotient `P_M`,
- a denotation relation or map `d_M`.

The correct joint identified set is

`I_QPd(O,A) = { (Q_M, P_M, d_M) : M in M(O,A) } / trivial label isomorphism`.

Point identification holds only if every element of this set is the same up to the declared trivial relabeling. Otherwise the result is partial identification.

## What can still be identified

For raw expressions `u,v`, define:

- **must-equivalent in Q** if `u ~_Q_M v` for every compatible model;
- **must-distinct in Q** if `u` and `v` are in different `Q_M` blocks for every compatible model;
- **unresolved in Q** otherwise.

For target histories/states `s,t`, define the analogous must-merge, must-separate, and unresolved relations over all compatible `P_M`.

For a language class candidate `q` and target candidate `p`, define:

- **must-denote** if every compatible model maps the corresponding language class to the corresponding target block;
- **cannot-denote** if no compatible model permits that mapping;
- **may-denote** otherwise.

These modal relations are invariant claims about the identified set. A single chosen completion is not.

## Proposition C088.1: invariant denotation criterion

Assume a common observable indexing of raw expressions and controlled histories, but allow compatible models to induce different quotient completions. A denotation assertion `u -> s` is point identified only if it is invariant across every member of `I_QPd(O,A)` after quotient-label isomorphisms are aligned.

Proof sketch:

1. Identification means that all observationally and assumption-compatible models agree on the asserted scientific quantity.
2. If two compatible models disagree on whether the class containing `u` denotes the block containing `s`, the assertion differs while `O` and `A` remain unchanged.
3. Therefore no estimator using only `O` and `A` can distinguish the two models at population level.
4. Conversely, if the assertion is invariant across the compatible set, it is identified relative to `O` and `A` even when other parts of `Q`, `P`, or `d` remain unresolved.

This proposition is a direct identified-set consequence, not a new intelligence theorem.

## Counterexample 1: language cannot legitimately complete unresolved target equality by agreement

Consider two target candidates `p1,p2` for which the finite controlled data and assumptions admit both:

- model `M_merge`, where they have exactly the same complete controlled law and form one target block;
- model `M_split`, where an arbitrarily small unobserved difference exists and they form two blocks.

Suppose the language distribution has two expressions `u1,u2` that a language model clusters separately with high confidence.

Two joint models remain compatible:

- `M_A`: one physical target, two stylistic or contextual language classes;
- `M_B`: two physical targets, one expression for each.

Language-internal confidence, likelihood, embedding separation, or pretraining dynamics can prefer `M_B`, but it does not remove `M_A` unless a cross-system observation assumption links the language contrast to an independently observed physical difference.

Therefore:

> Language may rank compatible completions, but ranking is not identification. Treating the top-ranked completion as recovered `P` or `d` silently adds a language-trust prior or structural assumption.

## Counterexample 2: one resolved target pair does not identify a full denotation permutation

Let `Q={q1,q2,q3}` and suppose the target identified set contains partitions with resolved block `p1` and an unresolved pair involving `p2,p3`. Assume cross-system evidence identifies `q1 -> p1`.

The remaining compatible mappings may include both

- `q2 -> p2`, `q3 -> p3`, and
- `q2 -> p3`, `q3 -> p2`.

Correct identification of one anchor pair does not identify the rest of the permutation. Reporting full denotation accuracy after filling the unresolved pairs by an optimizer, Hungarian matching, or lexical similarity would mix identified and convention-selected mappings.

## Counterexample 3: oracle-relative evaluation can conceal non-identification

A simulator chooses one ground-truth point model `M*` from a larger compatible set and supplies one oracle `P*` and `d*`. A learner may match this oracle perfectly.

If another model `M'` produces the same admissible observation law but a different `P'` or `d'`, perfect oracle accuracy establishes recovery of the simulator's hidden codebook, not identification from the declared observations.

Therefore simulator oracle metrics must be split into:

- **oracle agreement**, which measures prediction of the chosen hidden generator;
- **identified-set validity**, which checks that every asserted must-merge, must-separate, must-denote, or cannot-denote claim is invariant over all compatible models.

Only the second supports an identifiability claim.

## Counterexample 4: collapsing abstention into an error-free completion biases evaluation

Suppose the empirical procedure returns:

- one certified separation,
- no certified merges,
- four unresolved pairs.

A scoring script that forces unresolved pairs into singleton blocks will appear to recover a fine partition whenever the simulator oracle is also fine. A script that forces unresolved pairs into one block will appear successful whenever the oracle is coarse.

Both scores are artifacts of the completion rule. They do not measure the evidence supplied by the procedure.

The evaluation unit must therefore remain pairwise/modal until the identified set collapses sufficiently to define a unique partition.

## Evaluation contract for partially identified `P` and `d`

Before execution, LBQ001 should add the following non-completion metrics:

### Target relation metrics

- precision/recall for certified `must-separate` pairs against the exact oracle;
- precision/recall for structural-oracle `must-merge` pairs;
- false-merge count, with any empirical non-structural merge counted as a protocol violation;
- unresolved-pair rate;
- action/consequence coverage associated with every resolved pair.

### Denotation relation metrics

- precision of `must-denote` assertions;
- precision of `cannot-denote` assertions;
- proportion of language-target pairs remaining `may-denote`;
- number of denotation claims invariant across all compatible quotient completions;
- oracle agreement reported separately and never labeled identification accuracy.

### Identified-set calibration

For synthetic exact models where compatible completions can be enumerated, report:

- whether the true `(Q*,P*,d*)` lies in the returned identified set;
- identified-set size or a declared surrogate complexity;
- false exclusion count;
- point-collapse rate;
- width reduction attributable to each added assumption or observation family.

## Prior-art matrix update

| Prior art / object | What it establishes | What remains outside its guarantee | C088 classification |
|---|---|---|---|
| Manski partial identification | identified sets rather than arbitrary point completion under weak information | application-specific construction of `I_QPd`; language-target semantics | governing inference framework |
| Henry–Kitamura–Salanié finite mixtures | compatible latent decompositions may be set identified; observable variation can shrink the set | interactive controlled quotient and denotation | latent-decomposition boundary prior art |
| Duarte et al. / Autobounds | automated sharp or epsilon-sharp bounds over compatible discrete causal models | direct quotient-valued `Q/P/d` representation; immutable C088 execution pin | public identified-set backend reference |
| C087 exact quotient / Storm | unique quotient of a supplied complete point MDP | which point MDP is true under finite data; `Q`; `d` | exact member oracle, not identified-set solver |
| language pretraining score | may rank or regularize compatible completions | population identification without an explicit linking assumption | predictive diagnostic only |

## Public-code audit

`duarteguilherme/autobounds` publicly exposes a Python partial-identification engine, examples, tests, Docker usage, and replication materials. It operationalizes optimization over compatible discrete causal models and can return bounds rather than a fabricated point.

It is not directly suitable as the LBQ001 canonical baseline because:

- its estimands are scalar/vector causal queries rather than quotient-valued objects;
- it does not natively represent partition isomorphism classes or denotation correspondences;
- it does not implement the C087 asymmetric target relation contract;
- no paper-specific immutable commit was fixed in this run;
- no direct `Q/P/d` metrics, resource contract, or three-seed manifest is supplied.

No numerical reproduction was started.

## Decision

> **NARROWED TO JOINT PARTIAL IDENTIFICATION: WHEN THE TARGET QUOTIENT IS NOT POINT IDENTIFIED, THE SCIENTIFIC OBJECT IS THE IDENTIFIED SET OF `(Q,P,d)` COMPLETIONS AND ITS INVARIANT MUST/CANNOT RELATIONS; LANGUAGE MAY SHRINK THIS SET ONLY THROUGH AN EXPLICIT, AUDITABLE CROSS-SYSTEM ASSUMPTION OR OBSERVATION, NOT BY INTERNAL CONFIDENCE OR BEST-FIT COMPLETION — RQ-001 NOT ADOPTED.**

## Consequence for RQ-001

The candidate RQ is no longer accurately phrased as unconditional recovery of one `Q`, one `P`, and one `d` from finite observations. The admissible remaining question is:

> Given a preregistered controlled observation family and an explicit language–world linking assumption, what is the sharp joint identified set of raw-language quotients, exact target quotients, and denotations; which denotation assertions are invariant across that set; and what additional non-leaking interventions provably shrink the set to a point or a smaller equivalence class?

This remains potentially researchable, but novelty is not established. Partial identification, latent-mixture identified sets, and automated bound computation are prior art. A new contribution would require a quotient-valued sharpness theorem, a leakage-free observable linking law, and evidence that no existing latent-class/multi-view/causal partial-identification result already provides it.

## Next gate

1. Add a machine-readable identified-set evaluation section to LBQ001 without forcing unresolved pairs into a partition.
2. Define the admissible cross-system assumptions under which language observations may exclude a target/denotation completion.
3. Construct a finite exact benchmark where all compatible `(Q,P,d)` completions can be enumerated or solved symbolically, without extending legacy A–E mechanisms.
4. Audit whether latent-class algebraic-identification or causal-bound software already represents the required quotient-valued feasible set.
5. Only after the manifest, solver, and scoring contract are fixed may execution begin with seeds `17 / 29 / 43`, model size, parameter count, peak RSS, wall time, exact commands, commits, dataset digest, and raw-result digest.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- identifiability counterexamples: complete;
- target-side canonical estimand: exact quotient retained;
- empirical object under incomplete evidence: joint identified set, not forced partition;
- language-only completion of unresolved `P`: prohibited;
- invariant must/cannot denotation criterion: fixed;
- public identified-set backend reference: Autobounds audited, immutable execution pin not fixed;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://doi.org/10.1016/j.ijar.2004.10.006
- https://doi.org/10.3982/QE170
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11566246/
- https://github.com/duarteguilherme/autobounds
- https://s.aaai.org/Library/AAAI/1997/aaai97-017.php
