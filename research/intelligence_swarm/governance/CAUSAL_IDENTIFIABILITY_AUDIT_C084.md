# Causal Identifiability Audit C084

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) applicability/identifiability counterexamples.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C083 narrowed the remaining language-blind B4 gate to a globally consistent, action-complete, full-consequence, recursively stable approximate quotient. The next question is whether a robust or perturbation-stable global quotient is itself already covered by probabilistic-bisimulation theory and public implementations, and whether such a quotient can be used as the empirical B4 estimand.

## Primary prior art

### Fatmi, Kiefer, Parker, and van Breugel, CAV 2025

*Robust Probabilistic Bisimilarity for Labelled Markov Chains* introduces robust probabilistic bisimilarity for finite labelled Markov chains (LMCs).

The work establishes that:

- robust bisimilarity is an equivalence relation and a probabilistic bisimulation;
- it is the greatest relation satisfying the paper's robustness condition;
- it is computable by a polynomial-time fixed-point/refinement algorithm;
- the resulting relation is sufficient for continuity of probabilistic-bisimilarity distance under small transition perturbations;
- the algorithm was implemented in PRISM's explicit-state engine and evaluated on public probabilistic-model benchmarks.

The paper received a CAV 2025 Distinguished Paper Award. A 2026 follow-up, *On the Continuity of the Probabilistic Bisimilarity Distance*, strengthens the boundary by showing that robust bisimilarity is also necessary for continuity at distance zero and extends the continuity analysis to non-bisimilar state pairs.

### Spork, Baier, Katoen, Piribauer, and Quatmann, CONCUR 2024

*A Spectrum of Approximate Probabilistic Bisimulations* studies several approximate notions for LMCs, including `epsilon`-perturbed bisimulation: two models are related if transition probabilities can be perturbed within a prescribed budget so that the resulting models become exactly probabilistically bisimilar.

This removes the following from possible novelty:

- defining a perturbation-stable probabilistic equivalence;
- computing a greatest globally transitive robust relation rather than independent pairwise thresholds;
- connecting approximate/perturbed bisimulation to exact probabilistic bisimulation;
- using a fixed-point refinement algorithm to obtain a robust global partition;
- requiring continuity of a bisimulation distance under small transition perturbations;
- implementing robust LMC minimisation in a mature public model checker.

Thus C083's demand for a global tolerance-aware object is not generically open. Strong positive solutions exist for LMCs under specific robustness semantics.

## Assumption and guarantee comparison

### What robust LMC bisimilarity supplies

For a finite LMC with state labels and transition kernel `tau`, robust bisimilarity supplies:

- a genuine equivalence relation;
- a greatest fixed point;
- global transitivity by construction;
- preservation of ordinary probabilistic bisimulation;
- resistance of the induced distance-zero relation to small transition perturbations;
- a polynomial-time decision/minimisation procedure;
- a public PRISM implementation reported by the paper.

This directly resolves two concerns left by C082–C083 in the LMC setting:

1. approximate pairwise comparisons need not be glued by an ad hoc transitive closure;
2. a perturbation-aware estimand can be defined globally and recursively rather than as independent distribution clusters.

### What it does not supply for LBQ001-B4

The central mismatch is that the published relation is defined for labelled Markov chains, not action-controlled MDPs with a preregistered full-consequence family.

LBQ001-B4 requires equivalence only when, for every allowed action/intervention:

- action availability agrees;
- immediate independent consequence laws agree under the selected exact/approximate contract;
- physical cost and terminal consequence agree;
- transition mass into recursively defined quotient blocks agrees;
- uncovered actions force abstention rather than implicit marginalisation.

The LMC result does not by itself provide:

- action identity or universal quantification over actions;
- protection against behaviour-policy action marginalisation;
- a full-consequence label construction independent of semantic codebooks;
- finite-sample confidence or abstention guarantees;
- an empirical rule converting sample uncertainty into the paper's perturbation model;
- recovery of language quotient `Q` or denotation `d`.

### Robustness is not the same as approximate merging

A particularly important correction is that Fatmi et al.'s robust bisimilarity is a subset of ordinary probabilistic bisimilarity. It selects exactly bisimilar pairs whose distance-zero relationship is stable to perturbations; it does not simply merge any states whose transition laws are numerically close.

Therefore it should not be described as a generic `epsilon`-merge rule. It is a stability filter on exact bisimilarity.

The CONCUR 2024 `epsilon`-perturbed relation is closer to a tolerance-indexed merge semantics, but it answers an existential model-repair question: whether small perturbations can make systems exactly bisimilar. That estimand still differs from confidence-valid identification of the unknown true controlled model.

## Counterexample 1: action marginalisation survives a global robust LMC partition

Consider controlled states `s,t`, actions `a,b`, and physically distinct terminal consequence states `x,y`.

- From `s`: action `a` reaches `x`, action `b` reaches `y`.
- From `t`: action `a` reaches `y`, action `b` reaches `x`.

Assume the logging policy chooses `a` and `b` uniformly and action identity is removed when constructing an LMC. Both `s` and `t` then induce the same marginal transition law:

`P(x)=P(y)=1/2`.

They may therefore be robustly bisimilar in the action-marginal LMC, including under small perturbations. In the controlled B4 model they must be separated because the consequence of each named action differs.

Therefore:

> a globally transitive and perturbation-stable LMC quotient can still be strictly coarser than the action-complete controlled quotient, even with infinite data.

This is an estimand mismatch, not an implementation defect.

## Counterexample 2: existential perturbation equivalence is not identification of the true partition

Let a confidence region contain two point transition models.

- Model `M0`: states `s,t` are exactly bisimilar.
- Model `M1`: `s,t` differ by a small but nonzero transition asymmetry.

Suppose both can be perturbed by at most `epsilon` into one common exactly bisimilar model. Then an `epsilon`-perturbed relation may merge `s,t` throughout the region.

However, the unknown true point model has different exact Storm quotients in `M0` and `M1`.

Thus:

> existence of a nearby bisimilar repair does not imply that the unknown true system's exact partition is identified.

It defines a useful tolerance-indexed abstraction, but it must be reported as such. It cannot be used as evidence for exact latent-target identity.

## Counterexample 3: robustness can prefer stable over semantically complete distinctions

Let two states have identical ordinary labels and exactly equal transition mass into every current LMC block, so they are ordinarily bisimilar. Suppose the equality depends on a cancellation that is destroyed by arbitrarily small independent perturbations. Robust bisimilarity may separate them because the relation is discontinuous.

Now suppose the perturbed probabilities are not physical alternatives but independent estimation noise around one structurally tied mechanism. A symbolic mechanism-level equality would justify merging the states, whereas kernel-level robustness rejects the merge.

Therefore:

> robust kernel bisimilarity encodes stability to unconstrained probability perturbations, not invariance under the actual data-generating mechanism.

For LBQ001, the admissible perturbation set must be preregistered. Independent per-entry perturbations, parameter-tied perturbations, and confidence regions can induce different partitions.

## Counterexample 4: full-consequence labels can leak the target ontology

Robust LMC minimisation begins from state labels. If those labels include:

- gold target IDs;
- parser slots;
- simulator object or role names;
- target masks;
- semantic reward/evaluator outputs;

then the initial partition already contains the ontology being claimed as discovered. The subsequent robust refinement can be perfectly correct while only preserving supplied semantic supervision.

For B4, labels may include only preregistered non-semantic physical consequence channels. A language/target-codebook leakage scan remains mandatory.

## Public-code availability audit

Confirmed public records:

- peer-reviewed CAV 2025 paper and open manuscript;
- arXiv `2505.15290`;
- PRISM bibliography entry explicitly stating that the minimisation algorithm is implemented in PRISM;
- paper description of a Java implementation in PRISM's explicit-state engine;
- public PRISM model checker repository and benchmark ecosystem;
- CONCUR 2024 paper and arXiv `2407.07584`;
- June 2026 follow-up arXiv `2606.27209` on continuity.

Not confirmed in this run:

- a paper-specific public branch/tag or immutable PRISM commit containing the robust-bisimilarity implementation;
- a canonical command exposed by a released PRISM version;
- a machine-readable mapping from the paper's benchmark tables to exact model/command pairs;
- an MDP/action-conditioned implementation of the robust relation;
- a finite-sample confidence-to-perturbation calibration;
- LBQ001 partition metrics, seeds `17 / 29 / 43`, model size, RSS, wall time, or result digests.

Repository search of the accessible default PRISM code index did not identify a file by the paper title or the phrase `robust bisimilarity`. Therefore the code claim is credible and primary-source-backed, but no immutable paper-specific implementation pin is promoted in this run.

Classification:

> primary theorem, algorithm, and declared PRISM implementation are confirmed; an immutable executable paper-specific pin and an action-conditioned LBQ001-compatible path are not confirmed.

No unofficial reimplementation is promoted to canonical status.

## Prior-art matrix update

| Candidate | Global equivalence | Recursive/fixed point | Tolerance/robustness semantics | Action-conditioned | Finite-sample identification | Public immutable code | C classification |
|---|---:|---:|---:|---:|---:|---:|---|
| Fatmi et al. CAV 2025 robust bisimilarity | yes | yes | continuity-stable subset of exact LMC bisimilarity | no | no | implementation declared; exact commit not pinned | robust LMC quotient prior art |
| Spork et al. CONCUR 2024 `epsilon`-perturbed bisimulation | yes/notion-dependent | relational | existential small model perturbation | LMC focus | no | not pinned here | tolerance-indexed LMC prior art |
| Kumar–Pote–Scarlett COLT 2026 | yes | no endogenous successor quotient | exact repeated distributions plus TV separation | no | yes | not confirmed | global distribution clustering prior art |
| Storm exact B4 oracle | yes | yes | exact point MDP | yes | no | pinned in C073 | exact controlled oracle |
| Required empirical approximate B4 | yes | yes | preregistered mechanism-valid tolerance | yes | yes with abstention | not selected | remaining execution gate |

## Decision

> **NARROWED BEYOND GLOBAL ROBUST AND PERTURBATION-AWARE PROBABILISTIC BISIMULATION FOR LABELLED MARKOV CHAINS — ROBUST/GLOBAL APPROXIMATE QUOTIENTS ARE EXISTING PRIOR ART, BUT THE AVAILABLE RESULTS DO NOT PROVIDE ACTION-COMPLETE FULL-CONSEQUENCE MDP IDENTIFICATION, FINITE-SAMPLE CALIBRATION, OR LANGUAGE–TARGET COUPLING — NOT ADOPTED.**

C083's remaining question is narrowed again. The open execution issue is not whether a globally transitive robust quotient can be defined. It is whether one can instantiate an action-complete, full-consequence, recursively stable approximate MDP quotient with a perturbation set justified by the data-generating mechanism, global statistical guarantees, and abstention for uncovered actions.

## Consequence for RQ-001

This run concerns only the language-blind partition `P`. Even a perfect robust controlled quotient would not identify:

- raw-language equivalence `Q`;
- whether linguistic distinctions finer than the robust behavioral quotient are externally justified;
- denotation `d: Q -> P`;
- external semantic orientation.

A later joint stage must still use observable cross-system dependence that does not expose target IDs, parser outputs, simulator names, semantic reward, or evaluator codebooks.

## Next gate

1. Search PRISM branches/releases and paper artifacts for an immutable commit and command for the CAV 2025 implementation; do not reproduce from an unpinned moving branch.
2. Audit whether robust bisimilarity has already been extended from LMCs to action-labelled probabilistic automata or MDPs with action-preserving semantics.
3. Preregister the perturbation model: independent kernel entries, tied physical parameters, or confidence-set perturbations must not be conflated.
4. State whether B4 approximate mode targets robust exact bisimilarity, `epsilon`-perturbed bisimilarity, or a metric-diameter quotient; these are different estimands.
5. Require action-complete coverage and permanent abstention for uncovered actions.
6. Preserve only preregistered non-semantic consequence labels and run the leakage scan before execution.
7. Only after exact implementation and estimand pins are fixed, execute seeds `17 / 29 / 43` with model size, peak RSS, wall time, commands, commits, dataset digest, and result digest.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- public-code availability audit: complete;
- applicability/identifiability counterexamples: complete;
- global robust probabilistic-bisimulation quotient for LMCs: existing prior art;
- perturbation-aware approximate probabilistic bisimulation for LMCs: existing prior art;
- generic claim that globally transitive robust quotients are unavailable: rejected;
- action-complete finite-sample full-consequence robust B4 estimator: not selected;
- immutable CAV 2025 implementation commit: not confirmed;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://www.prismmodelchecker.org/bibitem.php?key=BFKP25
- https://link.springer.com/chapter/10.1007/978-3-031-98679-6_12
- https://arxiv.org/abs/2505.15290
- https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CONCUR.2024.37
- https://arxiv.org/abs/2407.07584
- https://arxiv.org/abs/2606.27209
