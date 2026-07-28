# Causal Identifiability Audit C083

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) applicability/identifiability counterexamples.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C082 established that pairwise anytime-valid tests do not by themselves define a globally consistent approximate B4 partition. The next question is whether global recovery of a hidden partition of multiple sampled distributions is itself already covered by distribution-testing theory.

## Primary prior art

Gunjan Kumar, Yash Pote, and Jonathan Scarlett, *A Distribution Testing Approach to Clustering Distributions*, COLT 2026, PMLR 336:4308–4348, arXiv `2512.08376`.

The paper studies `k` discrete distributions over a domain of size `n` with an unknown hidden partition. In its central two-cluster setting:

- all distributions inside each cluster are exactly equal;
- the two distinct cluster distributions are at least `epsilon` apart in total variation;
- the goal is to recover the complete hidden partition from samples;
- both the case where one cluster distribution is known and the case where both are unknown are analyzed;
- upper and lower sample-complexity bounds are given as functions of `n`, `k`, cluster size `r`, and `epsilon`, tight across regimes up to an `O(log k)` factor;
- the result extends to any constant number `d` of clusters.

This directly removes the following from possible novelty:

- converting distribution comparisons into a globally transitive hidden partition;
- recovering clusters of sampled distributions rather than returning isolated pairwise test results;
- proving finite-sample partition-recovery guarantees under exact within-cluster equality and between-cluster TV separation;
- handling the case in which the cluster distributions are both unknown;
- extending such recovery from two clusters to a fixed constant number of clusters.

Consequently, C082's concern that pairwise tests alone do not define a partition is valid, but the positive global-clustering solution is not generically open: it is existing prior art under a strong exact-equality/separation model.

## Assumption and guarantee comparison

### What the COLT 2026 result supplies

Let the sampled objects be distributions `p_1,...,p_k`. Under a hidden map `z_i in {1,...,d}` with constant `d`, the model assumes

`p_i = q_{z_i}`

for cluster representatives `q_1,...,q_d`, and distinct representatives are separated, e.g.

`TV(q_c,q_c') >= epsilon` for `c != c'`.

Under this contract, the estimand is already a well-defined equivalence partition: equality of the generating distributions is transitive, and the global algorithm recovers cluster membership rather than independently thresholding all pairs.

This supplies exactly the kind of global consistency missing from an unstructured pairwise-testing stack.

### What it does not supply for LBQ001-B4

The LBQ001-B4 object is not merely a collection of unrelated categorical distributions. It requires a controlled full-consequence quotient in which two states/targets are equivalent only if, for every preregistered action/intervention:

- action availability agrees;
- immediate non-semantic consequence laws agree to the selected exact or approximate contract;
- transition mass into every quotient block agrees;
- the partition is a fixed point because the successor blocks used in the comparison are themselves unknown.

The COLT clustering model does not, by itself, provide:

- action-complete coverage;
- recursive greatest-bisimulation/fixed-point refinement;
- unknown or growing numbers of target blocks beyond constant `d`;
- context-indexed or nonstationary controlled laws;
- within-cluster tolerance (`p_i` need not be exactly equal in an approximate B4 ontology);
- symbolic equality needed for exact empirical merge in the unrestricted model;
- consequence-channel independence from language/semantic codebooks;
- identification of language quotient `Q` or denotation `d`.

Thus the paper is a global statistical clustering primitive and a sharp prior-art boundary, not an end-to-end B4 or joint grounding solution.

## Counterexample 1: raw successor-distribution clustering can over-separate bisimilar states

Consider states `s` and `t`, one action `a`, and four successor states `x1,x2,y1,y2`. Suppose the correct full-consequence quotient has blocks

- `X = {x1,x2}`;
- `Y = {y1,y2}`.

Let

- `P(x1 | s,a)=1/2`, `P(y1 | s,a)=1/2`;
- `P(x2 | t,a)=1/2`, `P(y2 | t,a)=1/2`.

Assume members of `X` are fully bisimilar and members of `Y` are fully bisimilar, including every independent consequence channel. Then `s` and `t` are bisimilar because both send probability `1/2` to block `X` and `1/2` to block `Y`.

However, their categorical distributions over raw successor identities have disjoint support. A distribution-clustering algorithm applied before quotienting can place them in different clusters even with infinite data.

Therefore:

> global clustering of raw transition distributions is not equivalent to recovery of the greatest controlled quotient; the comparison domain must itself be the recursively recovered quotient blocks.

This is not a defect in the COLT result. It is a mismatch between its fixed observed alphabet and B4's endogenous successor-block alphabet.

## Counterexample 2: exact within-cluster equality does not cover a tolerance-indexed ontology

Suppose three consequence distributions satisfy

- `TV(p1,p2)=0.01`;
- `TV(p2,p3)=0.01`;
- `TV(p1,p3)=0.02`.

An approximate B4 definition may intend a block-diameter contract, a representative-radius contract, or another global tolerance object. None is equivalent to the exact-mixture model `p_i=q_{z_i}` unless within-block variation is zero.

Treating each small perturbation as a separate exact distribution can over-split the intended approximate quotient. Conversely, imposing pairwise threshold edges and taking connected components can merge endpoints farther apart than the tolerance.

Thus:

> exact distribution clustering solves a strong separated latent-class model, but it does not choose or justify the global approximate-equivalence estimand required by C082.

The approximate estimand must still be preregistered independently of the algorithm.

## Counterexample 3: independent per-action clustering need not yield the controlled quotient

Let states `s1,s2,s3,s4` have two actions `a,b` and identical immediate physical labels. Suppose exact consequence-distribution clusters are:

- under action `a`: `{s1,s2}` and `{s3,s4}`;
- under action `b`: `{s1,s3}` and `{s2,s4}`.

Each action separately has a valid global two-cluster partition. There is no nontrivial state partition respecting both; the common refinement is singleton blocks.

Therefore a B4 estimator cannot select one action's clustering or average action-indexed distributions. It must construct a common action-complete partition (or abstain for uncovered actions). Globality within each action is insufficient; globality is needed jointly over all actions and channels.

## Public-code availability audit

Audited public records:

- PMLR COLT 2026 paper page;
- arXiv `2512.08376`;
- author publication pages for Yash Pote and Jonathan Scarlett;
- public web/GitHub search for the exact paper title and author combination.

Confirmed:

- peer-reviewed COLT 2026 proceedings paper;
- public PDF and arXiv record;
- theorem statements and upper/lower sample-complexity results described by the primary record.

Not confirmed in this run:

- a paper-authored public implementation repository;
- an immutable implementation commit;
- canonical reproduction command;
- dependency lock/container;
- raw experimental artifacts;
- an implementation accepting action-indexed full-consequence observations;
- Storm-compatible partition output;
- seeds `17 / 29 / 43`, model size, RSS, wall time, or digests.

Classification:

> theory-level global distribution-partition recovery prior art; no immutable paper-specific public baseline was confirmed, and the published problem contract is not an executable LBQ001-B4 estimator.

No unofficial implementation is promoted to canonical status.

## Prior-art matrix update

| Candidate | Global partition output | Exact within-cluster law | Between-cluster separation | Action-conditioned | Recursive quotient/fixed point | Approximate within-block variation | Public immutable code | C classification |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Kumar–Pote–Scarlett COLT 2026 | yes | yes | TV `epsilon` | no | no | no | not confirmed | global distribution-clustering prior art |
| Pairwise anytime-valid tests from C082 | no | point/tolerance tests | configurable | per stream only | no | pairwise only | backend pinned | separation/confidence primitive |
| Storm B4 oracle | yes | exact point model | not statistical | yes | yes | no | pinned | exact-model oracle |
| Required empirical approximate B4 | yes | no; tolerance-indexed | preregistered gap | yes | yes | yes | not selected | still open execution gate |

## Decision

> **NARROWED BEYOND GLOBAL FINITE-SAMPLE CLUSTERING OF MULTIPLE DISTRIBUTIONS UNDER EXACT WITHIN-CLUSTER EQUALITY AND TV SEPARATION — GLOBAL TRANSITIVE PARTITION RECOVERY IS EXISTING PRIOR ART, BUT THE RESULT DOES NOT SUPPLY ACTION COVERAGE, A RECURSIVE GREATEST CONTROLLED QUOTIENT, APPROXIMATE WITHIN-BLOCK SEMANTICS, OR LANGUAGE–TARGET COUPLING — NOT ADOPTED.**

C082's next gate is therefore refined rather than discarded. The novelty question is no longer “can pairwise distribution tests be made into any global partition?” The remaining operational question is:

> can a preregistered tolerance-indexed, action-complete, full-consequence, recursively stable quotient be recovered with global error control and abstention, using existing components, without semantic leakage?

## Consequence for RQ-001

This run only narrows recovery of language-blind `P`. Even perfect recovery of distribution clusters or a B4 quotient does not identify raw-language equivalence `Q` or denotation `d`.

For joint identification, a later stage must still show observable cross-system dependence that aligns `Q` with `P` without target IDs, parser slots, simulator names, semantic reward, or evaluator codebooks. The COLT hidden cluster labels are statistical component labels, not externally oriented meanings.

## Next gate

1. Amend LBQ001 approximate mode to define a single global object, choosing among block-diameter, representative-radius, or a recursively defined approximate-bisimulation contract.
2. State whether the number of blocks is fixed, bounded, selected, or allowed to grow.
3. Construct the action-complete comparison law jointly across all actions/channels; independent per-action clustering is not sufficient.
4. Preserve recursive comparison over candidate successor blocks rather than raw successor identities.
5. Allocate simultaneous error across the complete global procedure and force abstention for uncovered actions.
6. Search specifically for public implementations of robust/approximate probabilistic partition refinement satisfying these requirements before writing any new estimator.
7. Only after the estimand and implementation pin are fixed, execute seeds `17 / 29 / 43` with model size, peak RSS, wall time, dataset digest, command, commit, and result digest.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- public-code availability audit: complete;
- applicability/identifiability counterexamples: complete;
- global finite-sample clustering of exactly repeated distributions: existing prior art;
- generic claim that pairwise tests cannot be turned into a global partition: narrowed/corrected;
- action-complete recursive approximate B4 estimator: not selected;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://proceedings.mlr.press/v336/kumar26a.html
- https://arxiv.org/abs/2512.08376
- https://yashpote.github.io/
- https://www.comp.nus.edu.sg/~scarlett/publications.html
