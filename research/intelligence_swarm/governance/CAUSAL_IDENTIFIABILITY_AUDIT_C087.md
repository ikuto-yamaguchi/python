# Causal Identifiability Audit C087

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, and (d) identifiability/selection counterexamples.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C086 showed that exact homogeneous partitions, epsilon-homogeneous global partitions, bisimulation metrics, robust relations, and perturbation-aware abstractions all exist in prior art, but they target different objects. The unresolved target-side gate was therefore not another algorithm. It was the absence of one uniquely specified estimand for LBQ001.

This run compares the candidate estimands by uniqueness, dependence on arbitrary choices, compatibility with exact known-model oracles, and finite-sample interpretability. It then updates LBQ001 to fix one canonical target.

## Primary prior art used for the comparison

### Exact homogeneous/bisimulation quotient

Dean and Givan, *Model Minimization in Markov Decision Processes* (AAAI 1997), define a homogeneous partition in which states in one block have identical action-conditioned probabilities of reaching every block. Their refinement algorithm returns the coarsest homogeneous refinement of a supplied observable partition and a reduced MDP minimal in the corresponding exact sense.

For LBQ001, after all admissible non-semantic consequences and action availability are included in the observable interface, this exact coarsest quotient is the finite-state form of the controlled predictive equivalence already used in the preregistration.

### Metric and approximate abstractions

Ferns, Panangaden, and Precup define MDP bisimulation metrics that quantify behavioral discrepancy and support value bounds. Dean, Givan, and Leach define epsilon-homogeneous partitions and bounded-parameter aggregate MDPs. Later robust and perturbation-aware bisimulation work supplies still other stability or repair-based objects.

These are valid prior-art abstractions but are not identical estimands. A metric requires a clustering rule, epsilon homogeneity depends on coordinate tolerances and refinement choices, robust exactness depends on a perturbation family, and perturbation repair changes the model being summarized.

### Public exact oracle

The pinned Storm path from earlier audits remains the public exact point-model oracle for strong MDP bisimulation. C087 does not add or modify an architecture. It changes only the preregistered interpretation and empirical decision contract.

## Estimand comparison

| Candidate | Unique relative to declared interface | Extra user choice | Compatible with exact Storm oracle | Finite-sample exact merge without structure | Suitable as canonical `P_LBQ` |
|---|---:|---|---:|---:|---:|
| Exact full-consequence controlled quotient | yes, up to block labels | declared action/consequence family | yes | no | yes |
| Bisimulation-metric threshold partition | no in general | metric, threshold, linkage | only at distance zero | no | no |
| Epsilon-homogeneous partition | no in general | epsilon, coordinate rule, split order/selection | only as epsilon -> 0 under matching labels | no | no |
| Robust-exact relation | yes only after perturbation family is fixed | physical/adversarial perturbation model | not the same quotient | no | diagnostic only |
| Perturbation-repair quotient | may be unique for a specified optimization, but summarizes a repaired model | repair norm and budget | not the original point-model quotient | no | diagnostic only |
| Task-relative reward/value abstraction | task dependent | reward/task family | generally coarser | no | B3 control only |

## Positive selection result

Relative to a fixed admissible action family `A*` and a fixed non-semantic consequence process `Y*`, define histories `h,h'` as equivalent when every allowed future intervention policy induces the same full future consequence law.

This relation is an equivalence relation. The set of equivalence classes is unique up to class labels because it is defined extensionally by equality of observable controlled laws. In a finite fully specified MDP, the corresponding coarsest stable partition can be computed by exact homogeneous/bisimulation refinement.

Therefore the target-side estimand is fixed as:

> **the exact full-consequence controlled predictive quotient induced by all preregistered non-semantic consequences and named admissible actions.**

This is not a new theorem or new intelligence mechanism. It is a governance choice selecting an existing exact object because approximate alternatives do not supply one unique ontology without additional conventions.

## Counterexample 1: metric threshold plus transitive closure is not the exact quotient

Let a valid pseudometric satisfy

- `d(s1,s2)=0.6 epsilon`,
- `d(s2,s3)=0.6 epsilon`,
- `d(s1,s3)=1.2 epsilon`.

Pairwise thresholding at `epsilon` is not transitive. Connected-component closure merges all three states even though the endpoints exceed the threshold. Complete-linkage separates at least one near pair. Both are legitimate clustering conventions but produce different partitions from the same identified metric.

Thus metric identification does not identify a partition until a non-theorem-derived clustering convention is added.

## Counterexample 2: epsilon-homogeneous admissibility is not uniqueness

With identical transitions and rewards `0`, `0.6 epsilon`, and `1.2 epsilon`, both

- `{{s1,s2},{s3}}`, and
- `{{s1},{s2,s3}}`

satisfy a within-block reward-diameter tolerance of `epsilon`, while neither refines the other.

Selecting one by split order, initialization, lexicographic state ID, or optimization heuristic makes the result reproducible but not observationally identifiable as a semantic ontology.

## Counterexample 3: robust or repair-based equivalence changes the scientific question

Suppose two states are non-bisimilar in the true point MDP but can be made bisimilar by a perturbation of size at most `epsilon`. A perturbation-repair method may merge them, whereas the exact point-model quotient separates them.

The repair quotient answers whether a nearby model admits the abstraction. It does not answer whether the unknown true model has equal controlled laws. Reporting the repaired quotient as latent target identity would silently replace the estimand.

## Counterexample 4: finite-sample non-rejection cannot certify exact merge

Consider two Bernoulli successor laws with parameters `1/2` and `1/2 + eta`. At `eta=0` the exact quotient may merge the states; for every `eta>0` it separates them. For any finite sample size, sufficiently small positive `eta` yields overlapping finite-sample evidence and the same count vector can occur under both models.

Therefore an empirical test may certify a difference under sufficient separation, but failure to reject equality cannot certify exact equality. Without structural parameter tying or a complete exact model, the correct result is `unidentified`.

This is why the updated empirical contract is asymmetric:

- `separate` after simultaneous confidence excludes equality;
- `merge` only from symbolic equality, deterministic identity, or exact complete-model oracle;
- `unidentified` otherwise, including missing action coverage.

## Counterexample 5: consequence-family choice remains an assumption, not a learned ontology

Even the exact quotient is relative to the declared observation/intervention interface. If a physically relevant sensor is omitted, states differing only on that sensor are merged. If a gold target ID or parser-derived semantic label is added, the quotient preserves supplied semantics.

Therefore exactness removes threshold and partition-selection ambiguity, but does not remove the need to preregister a complete leakage-free consequence family. The ontology claim remains no stronger than the declared interface.

## LBQ001 update completed

`benchmarks/grounded_causal/PREREGISTERED_LANGUAGE_BLIND_QUOTIENT_BASELINE_LBQ001.md` is updated in the same branch with:

- the canonical exact estimand lock;
- an exact empirical `separate / structural-oracle merge / unidentified` contract;
- an approximate-mode firewall;
- explicit false-merge and abstention metrics;
- fail-to-reject and missing-action controls;
- revised acceptance/rejection criteria.

Approximate partitions remain permitted only as separately named diagnostics. They cannot establish exact `P`, `Q`, or `d`.

## Prior-art matrix update

| Prior art / object | What it identifies or computes | What remains outside its guarantee | C087 classification |
|---|---|---|---|
| Dean–Givan exact homogeneous refinement | unique coarsest exact quotient relative to supplied labels/actions | unknown model, missing consequences, `Q`, `d` | canonical exact estimand/oracle theory |
| Storm strong MDP bisimulation | exact quotient of supplied point model | finite-sample model identification, leakage-free interface | pinned exact oracle |
| Ferns-style MDP metric | behavioral distance | unique partition and semantic threshold | diagnostic prior art |
| epsilon-homogeneous/BMDP | globally valid approximate partitions and planning bounds | unique ontology, finite-sample equality, `Q`, `d` | approximate diagnostic prior art |
| robust/perturbation-aware bisimulation | stability or nearby-model relation | true point-model exact quotient unless definitions coincide | separate estimand, diagnostic |
| empirical distribution tests/confidence sequences | evidence for separated laws under assumptions | exact equality certification and missing coverage | separation backend only |

## Decision

> **NARROWED AND ESTIMAND-FIXED: LBQ001 NOW TARGETS THE UNIQUE EXACT FULL-CONSEQUENCE CONTROLLED PREDICTIVE QUOTIENT; APPROXIMATE PARTITIONS ARE DIAGNOSTICS ONLY, AND FINITE-SAMPLE EXACT MERGE IS FORBIDDEN WITHOUT SYMBOLIC OR COMPLETE-MODEL EQUALITY — RQ-001 NOT ADOPTED.**

This resolves the C086 governance ambiguity but does not establish joint identification.

## Consequence for RQ-001

The target-side claim is now precise:

- `P` means the exact quotient induced by the preregistered non-semantic controlled law, not whichever approximate clustering performs best;
- empirical target evidence may remain partially unresolved;
- language is not allowed to fill unresolved target equivalence by assertion or internal confidence;
- a later coupling claim must directly evaluate `Q`, the resolved part of `P`, and `d`, while preserving uncertainty for unresolved target pairs.

A language model that predicts the oracle partition in a simulator may still be using target-codebook leakage. A language model that improves separation sample efficiency may be useful but does not by itself prove denotation. External semantic orientation remains outside exact behavioral quotient identification.

## Next gate

1. Freeze a machine-readable `A*`/`Y*` consequence manifest and leakage scan before any execution.
2. Pin the exact Storm command/model format used for B4 oracle output and direct partition export.
3. Select an existing public confidence backend for empirical separation only; do not call it a partition recovery architecture.
4. Define how partially resolved pair decisions are scored against the oracle without forcing abstentions into blocks.
5. Only then begin the three-seed execution with model size, parameter count, peak RSS, train/evaluation time, exact environment, commands, commits, dataset digest, and raw-result digest.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- identifiability/selection counterexamples: complete;
- canonical target-side estimand: fixed to exact full-consequence controlled quotient;
- approximate partition ambiguity: removed from canonical B4, retained as diagnostics;
- finite-sample exact merge without structure: prohibited;
- LBQ001 preregistration: updated;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://s.aaai.org/Library/AAAI/1997/aaai97-017.php
- https://arxiv.org/abs/1207.4114
- https://arxiv.org/abs/1302.1533
- https://www.prismmodelchecker.org/
