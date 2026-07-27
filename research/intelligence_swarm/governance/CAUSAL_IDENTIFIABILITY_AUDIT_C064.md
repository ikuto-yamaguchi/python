# Causal Identifiability Audit C064

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the available observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes: (a) prior-art matrix consolidation, (b) theorem/assumption comparison across the audited literature, and (d) a general identifiability counterexample and decision gate.
- Numerical reproduction is not started.

## Purpose of C064

C026–C063 repeatedly established paper-specific versions of the same boundary:

1. non-language methods may identify causal coordinates, causal graphs, intervention targets, response mixtures, abstractions, concepts, dynamical parameters, or reward-relevant partitions;
2. language-only or language-dynamics methods may identify predictive, distributional, assertion-based, or task-functional language quotients;
3. interactive grounding may identify a policy-sufficient or reward-sufficient correspondence inside a supplied world interface;
4. none of these results alone fixes the cross-system denotation when language classes, target classes, and target-indexed interfaces admit a common recoding.

C064 therefore stops adding another isolated example and consolidates the repeated counterexamples into one explicit criterion that can decide whether RQ-001 should be adopted, narrowed, or rejected.

## Consolidated prior-art matrix

| Identified object | Representative audited lines of work | Strongest guarantee already available | Residual ambiguity relevant to RQ-001 |
|---|---|---|---|
| Latent causal coordinates and graph | general CRL, score-based CRL, uncoupled interventions, unknown multi-node interventions | coordinate or graph recovery under explicit assumptions, sometimes with unknown target recovery | coordinate permutation, componentwise transform, target-interface recoding |
| Intervention-target quotient | unknown-target CRL, causal response mixtures, RePaRe, BISCUIT, UMNI-CRL | recovery of the finest partition exposed by the available intervention family | merge/split freedom inside interventionally identical blocks; external naming not fixed |
| Causal abstractions and concepts | causal abstraction, semantic embedding, intervention-context concept models, targeted causal reduction | recovery of supplied or intervention-induced abstraction under assumptions | concept inventory or target semantics may be supplied; internal recoding remains |
| Interactive functional grounding | IGL, Messenger/EMMA, IGLU, OpenLock, click grounding | reward-, policy-, construction-, or interaction-sufficient mapping | task success does not directly identify `Q`, `P`, or `d`; world interface may carry the codebook |
| Language dynamics and internal equivalence | token-level causal discovery, assertion-based semantic emulation, Dynalang | predictive or internal equivalence recovery under restricted conditions | no unique map from language quotient to external target quotient |
| Active probing with advice | active causal discovery with advice and clarification-style interaction | fewer interventions or robust structure recovery on an indexed vertex set | vertex identity correspondence is fixed before the theorem applies |

The remaining RQ is therefore not “can language help recover a causal representation?” or “can interaction ground language well enough for control?” Both are already established in multiple forms. The remaining issue is whether observations uniquely determine the triple:

- `Q`: equivalence relation over raw utterances;
- `P`: residual semantic partition over intervention targets;
- `d: Q -> P`: denotation.

## Unified observation model

Let the complete observable record be

`O = (L, E, X, A, Y, R, C)`

where:

- `L` is raw language and its temporal context;
- `E` is environment or episode identity stripped of semantic target names;
- `X` is non-language state or observation;
- `A` is an action or physical probe;
- `Y` is the subsequent observation or trajectory;
- `R` is reward, success, or task feedback when legitimately observable;
- `C` is clarification or human response when present.

A candidate grounded model contains at least:

- a raw-language quotient `Q`;
- a causal target quotient `P`;
- a denotation map `d: Q -> P`;
- target-indexed transition, sensor, actuator, reward, policy, parser, and evaluator components as applicable.

The available experiment identifies `(Q, P, d)` only if every model producing the same law over all admissible adaptive transcripts has the same triple, up to an explicitly declared trivial equivalence.

## Residual Joint Automorphism Criterion

Define a transformation `g` acting jointly on:

- raw utterance classes;
- latent or recovered causal coordinates;
- intervention-target blocks;
- denotation;
- target-indexed actuator and sensor channels;
- target-indexed transition, reward, policy, decoder, parser, logging, and evaluation interfaces.

Call `g` an admissible joint automorphism when, for every allowed adaptive strategy, applying `g` preserves the probability law and cost of the complete observable transcript.

### Proposition C064.1 — necessary condition for joint identification

If a non-trivial admissible joint automorphism exists and it changes at least one of `Q`, `P`, or `d`, then the triple `(Q, P, d)` is not identifiable from the declared observation model.

### Proof sketch

Take a model `M` compatible with the observation model and apply the non-trivial automorphism to obtain `g(M)`. By definition, every admissible adaptive strategy generates the same transcript law and the same probe cost in both models. No estimator based only on those transcripts can distinguish `M` from `g(M)`. Since the two models disagree on at least one of `Q`, `P`, or `d`, the triple is not uniquely determined by the observations. Therefore joint identification fails.

This proposition subsumes the recurring counterexamples from C026–C063. It applies even when one or more internal subproblems are perfectly solved:

- perfect latent-coordinate recovery;
- perfect unknown-target recovery;
- perfect causal graph recovery;
- perfect future prediction;
- perfect reward decoding;
- perfect instruction following;
- perfect active causal discovery;
- perfect task success.

## Adaptive interaction does not automatically remove the automorphism

Suppose an interaction policy selects the next probe from the previous transcript. If query identity, response law, action cost, and observation interface are all equivariant under `g`, then the transcript law remains invariant at every round by induction:

1. the empty histories agree;
2. equal transformed histories induce corresponding next probes;
3. corresponding probes have equal cost and transformed response distributions;
4. therefore the next histories again agree in law.

Consequently, unlimited adaptive interaction is insufficient when the entire query-response-cost system shares the same symmetry.

This converts the repeated qualitative observation “more interaction is not enough” into a concrete audit rule:

> A proposed probe is informative for semantic identification only if it is not invariant under at least one currently surviving joint automorphism.

## Merge/split non-identifiability inside observationally identical blocks

Permutation is not the only problem. Let two candidate targets have exactly the same complete law under all admissible probes, including future consequences and costs. Then both of the following ontologies fit the data:

- a merged ontology with one target and two synonymous utterances;
- a split ontology with two distinct targets and two distinct utterance meanings.

Thus even after all label permutations are quotient out, `Q` and `P` remain non-identifiable inside a complete interaction-equivalence class unless an additional observable separates the candidates.

The finest data-identifiable target object is therefore the quotient induced by the complete admissible transcript law, not an arbitrary semantic ontology finer than that quotient.

## What can break the residual symmetry

A resource can serve as a legitimate symmetry breaker only if its identity and response law are fixed independently of both the language codebook and the simulator or benchmark target codebook.

Candidate legitimate anchors include:

- a physical actuator whose identity is fixed by wiring or independently audited hardware;
- a sensor axis with independently calibrated orientation and units;
- a measurement standard fixed before language or target labels are assigned;
- a human response collected under a protocol that does not expose simulator target names, parser slots, or gold semantics;
- an intervention feasibility or cost asymmetry arising from physical constraints rather than target labels;
- a held-out consequence generated by an independently specified physical law.

The following do not count as independent symmetry breakers unless separately justified:

- parser-produced target IDs;
- simulator object names or latent-variable names;
- environment filenames encoding target identity;
- gold reward or success labels derived from a target codebook;
- reference structures or evaluator labels generated from gold semantics;
- pretrained embeddings trained on the same target names;
- clarification answers generated from the benchmark ontology;
- intervention costs assigned using target labels.

## Sufficient-condition template, not yet a theorem of the project

A plausible adoption route is now precise enough to state as a proof obligation.

Let `G0` be the group of all joint automorphisms preserving the language law, non-language intervention law, adaptive transcript law, and probe costs before adding independent anchors. Let `H1, ..., Hk` be preregistered anchor laws. Define:

`G* = { g in G0 : g preserves every Hi }`.

A sufficient-condition program would need to prove all of the following:

1. every observationally equivalent model differs only by an element of `G0` plus declared componentwise nuisance transformations;
2. the anchors are generated independently of the disputed language and target codebooks;
3. `G*` is exactly the declared trivial equivalence group;
4. no merge/split alternative remains inside a complete transcript-equivalence block;
5. `Q`, `P`, and `d` are directly recoverable under these assumptions.

C064 does not claim this theorem has been proved. It defines the minimum positive result required before RQ-001 can be adopted.

## Decision gate introduced by C064

Future runs should no longer narrow the RQ merely by auditing another paper with the same permutation counterexample. A new audit is decision-relevant only if it does at least one of the following:

1. proves that a previously surviving automorphism is actually eliminated by a stated observation;
2. finds prior work already proving the required cross-system identification;
3. constructs a countermodel that survives the proposed independent anchors;
4. reproduces a public baseline needed to estimate the finest non-language or language-only quotient;
5. formalizes and preregisters a concrete anchor protocol without semantic leakage.

If none of these occurs, the run adds evidence volume but does not move the adoption decision.

## Baseline consequence

The next experimental step remains baseline reproduction, not architecture design. Before introducing any new architecture, the project must reproduce at least one selected public baseline for each side of the factorization:

- a non-language unknown-target CRL baseline to estimate the finest identifiable target quotient;
- a language-only or language-dynamics baseline to estimate the finest supported raw-language quotient;
- an interactive functional-grounding baseline to quantify what task success adds beyond the two separate quotients.

Each experimental baseline must report:

- exact commit and dependency lock;
- input and generated-data checksums;
- three fixed seeds;
- model bytes;
- peak RSS;
- wall-clock training and evaluation time;
- direct metrics for `Q`, `P`, and `d`, not only task success.

No experiment is started in C064, so resource reporting is not yet applicable.

## Decision

**NARROWED TO AN EXTERNAL SYMMETRY-BREAKING IDENTIFICATION PROBLEM — NOT ADOPTED**

The surviving candidate is:

> After independently recovering the finest raw-language quotient and the finest non-language intervention-target quotient, can preregistered cross-system probes whose identities, orientations, units, costs, and response laws are fixed independently of both codebooks reduce the residual joint automorphism group to the declared trivial equivalence group and eliminate merge/split alternatives, thereby identifying `Q`, residual `P`, and `d` without parser, simulator-label, reward, evaluator, or clarification-codebook leakage?

This is narrower and more decision-ready than the previous formulation. Adoption now requires a positive symmetry-elimination theorem or an equivalent prior result, followed by baseline reproduction and preregistered testing.

## Status

- RQ-001: narrowed to an external symmetry-breaking identification problem; not adopted.
- Prior-art consolidation: completed.
- Cross-paper theorem/assumption comparison: completed.
- General identifiability counterexample: completed.
- Residual joint automorphism criterion: recorded as a governance proposition.
- Positive sufficient-condition theorem: not proved.
- Public baseline reproduction: not started.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
