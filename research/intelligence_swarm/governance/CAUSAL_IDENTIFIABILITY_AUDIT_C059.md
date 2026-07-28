# Causal Identifiability Audit C059

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + public-code availability audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Active causal structure learning with advice

Davin Choo, Themistoklis Gouleakis, and Arnab Bhattacharyya. Proceedings of the 40th International Conference on Machine Learning, PMLR 202, 2023.

Primary records:

- PMLR: https://proceedings.mlr.press/v202/choo23a.html
- paper PDF: https://proceedings.mlr.press/v202/choo23a/choo23a.pdf
- OpenReview: https://openreview.net/forum?id=u2Ap3vr5zQ
- arXiv: https://arxiv.org/abs/2305.19588
- author publication page: https://davinchoo.com/

This work is relevant to the surviving interactive part of RQ-001 because it formally separates two roles that language-like side information could play:

1. side information may propose a causal structure;
2. active interventions verify or repair that proposal.

The paper calls the side information **advice** and allows it to be imperfect or arbitrarily bad.

## RQ variables

Let:

- `U` be raw utterances or advice strings;
- `Q` be the unknown raw-language equivalence relation;
- `Z = {Z_1, ..., Z_n}` be causally sufficient observed causal variables;
- `G*` be the unknown true causal DAG over the fixed variable set;
- `G_adv` be an advice DAG supplied to the active learner;
- `I_1, I_2, ...` be adaptively selected ideal interventions;
- `P` be the unknown semantic partition of intervention targets;
- `d: U/Q -> P` be the denotation map required by RQ-001.

## Observations and supervision in the audited setting

The learner is given:

- the observational essential graph, assumed recoverable from data;
- a fixed, already indexed causal variable set;
- an advice DAG consistent with the observational essential graph;
- the ability to perform ideal interventions on chosen indexed variables or bounded-size indexed sets;
- interventional orientation information sufficient to update the essential graph.

The learner is not asked to infer:

- which raw strings are equivalent;
- which perceptual factors constitute the causal variables;
- whether two indexed intervention actions denote the same external target;
- a mapping from language classes to target classes.

Thus advice is structurally aligned side information, not raw language whose semantics must be discovered.

## Assumptions relevant to the guarantee

The audited results rely on conditions including:

1. causal sufficiency: no latent confounding;
2. faithfulness;
3. no selection bias or missingness in the core setting;
4. ideal, noiseless interventions;
5. an observational essential graph that is correctly recovered;
6. advice that is a DAG consistent with that essential graph;
7. fixed identities for vertices and intervention actions;
8. intervention outcomes that correctly orient the corresponding causal edges;
9. an intervention-cost model defined over those fixed vertex identities.

These assumptions already provide the cross-system indexing that RQ-001 is trying to discover. In particular, the advice graph and intervention oracle refer to the same named vertex set.

## Guarantee actually established

For advice DAG `G_adv` and true DAG `G*`, the paper defines an advice error/distance `psi(G_adv, G*)`, bounded by the number of variables and equal to zero when the advice is correct.

The adaptive search algorithm recovers the true DAG while using an intervention cost within a logarithmic factor depending on the advice error. In the paper's stated form, the cost is bounded by an `O(max{1, log psi})` factor relative to verification cost; the bounded intervention-size result also contains the corresponding `log k` dependence.

The guarantee is robust in the algorithm-with-predictions sense:

- good advice can reduce active-search cost;
- arbitrarily bad advice does not destroy the worst-case guarantee.

The work does not establish:

- identification of raw-language equivalence `Q`;
- discovery of a latent target partition from perceptual observations;
- identification of denotation `d`;
- validation that two pieces of advice have the same meaning;
- elimination of simultaneous advice/vertex/intervention relabeling;
- joint identification of `Q`, `P`, and `d`.

## Prior-art boundary added to the matrix

The following claims are excluded from the novelty space:

- using imperfect language-like advice to choose causal interventions;
- actively verifying or repairing a proposed causal graph;
- obtaining an instance-dependent intervention saving when advice is close to correct;
- retaining a worst-case guarantee when advice is arbitrarily wrong;
- treating a learned language model's graph prediction as fallible advice rather than ground truth;
- using clarification or probing only to reduce the number of interventions needed for an already indexed DAG;
- claiming a new grounding principle merely because language-guided active search outperforms advice-free active search.

The surviving RQ must therefore concern semantic identification beyond efficient graph verification on a supplied common vertex alphabet.

## Theorem comparison with the surviving RQ

The audited theorem answers:

> Given a correctly indexed variable set, a correct observational essential graph, ideal intervention access, and possibly erroneous graph advice over the same vertices, how efficiently can an adaptive algorithm recover the true DAG?

RQ-001 asks:

> From raw language and observations whose target identities are not already jointly indexed, can an interactive learner identify raw-language equivalence, the latent intervention-target partition, and their denotation map?

The distinction is not cosmetic. The advice theorem assumes the identity relation between:

- a vertex in the advice DAG;
- a variable accepted by the intervention oracle;
- a variable whose incident edges are oriented by the result.

If a language parser supplies that identity, then the central denotation problem has already been solved upstream.

## Identifiability counterexample A: perfect active DAG recovery with different denotation

Assume an oracle active learner perfectly recovers `G*` and uses the optimal intervention sequence.

Let `sigma` be a non-identity permutation of the causal vertices. Construct a second world by simultaneously transforming:

- every vertex of `G*` by `sigma`;
- every vertex of `G_adv` by `sigma`;
- every intervention action accepted by the oracle;
- every interventional response record;
- every raw-language class;
- denotation `d`;
- all target-indexed logging and evaluation interfaces.

The transformed world preserves:

- the observational essential graph up to the same relabeling;
- the advice error `psi`;
- every verifying intervention-set size;
- the full adaptive intervention transcript;
- every oriented edge and recovered DAG score;
- total intervention cost and approximation ratio;
- all downstream predictions and task outcomes evaluated through the recoded interface.

Nevertheless, the external assignment from raw-language classes to causal targets differs.

Therefore:

> Exact active recovery of the causal DAG, even with optimal use of advice, does not identify cross-system denotation.

## Identifiability counterexample B: adaptive querying cannot break an equivariant symmetry

Let a nontrivial automorphism group `H` act jointly on:

- candidate language classes;
- causal vertices;
- available intervention actions;
- returned observations.

Suppose the observational law, advice distribution, intervention cost, and response oracle are all equivariant under `H`.

For any adaptive policy, the next query is a function of the previous transcript. Applying `h in H` to the complete transcript produces another transcript with the same probability and cost. Inductively, adaptation alone cannot select between the two semantic interpretations.

This remains true even when the policy:

- asks an unlimited number of questions;
- chooses interventions based on all past responses;
- perfectly recovers the unlabeled graph;
- is robust to adversarial advice.

Thus:

> Interaction breaks a semantic symmetry only when some allowed query, response, or cost is not invariant under that symmetry.

More interaction from the same equivariant oracle is not a sufficient condition for grounding.

## Identifiability counterexample C: advice robustness is not semantic validation

Consider two raw advice strings `u1` and `u2` that induce the same advice DAG over the supplied vertex alphabet.

Model A treats them as paraphrases in one language class.

Model B treats them as distinct meanings whose difference is outside the fixed graph/query interface.

The active algorithm receives the same advice DAG and therefore issues the same interventions, observes the same responses, and obtains the same guarantee in both models. Robustness to bad graph advice only protects causal-graph recovery; it does not decide whether the original strings were semantically equivalent.

Therefore advice quality, graph distance, intervention cost, and final DAG accuracy are not direct metrics for `Q` or `d`.

## Consequence for interactive language grounding

C059 sharpens the positive route suggested by C058.

A clarification or active intervention is informative for grounding only if its semantics are fixed independently of the language interpretation being tested. Candidate symmetry-breaking resources include:

- an actuator with externally fixed physical identity;
- an asymmetric intervention cost fixed before observing language;
- a sensor channel with fixed orientation or calibration;
- a human response whose scoring rule is not generated by the same parser or target codebook;
- an intervention availability constraint that differs across candidate targets for non-semantic physical reasons;
- a held-out consequence that differs between candidate denotations and cannot be recoded with the interface.

Conversely, the following are not independent anchors when produced from the same semantic pipeline:

- parser-selected target IDs;
- a language model's proposed vertex labels;
- simulator object names;
- gold entity slots;
- answer correctness computed from the same codebook;
- intervention costs assigned by target labels rather than physical operations.

## Mandatory controls introduced by C059

Before RQ adoption, preregistration must include:

1. a distinction between raw advice strings, parsed graph advice, and fixed intervention actions;
2. an explicit audit of where vertex identity is introduced;
3. an advice-free active causal discovery baseline;
4. a correct-advice baseline;
5. randomly permuted and adversarial-advice controls;
6. a raw-language baseline that does not receive parsed vertex identities;
7. simultaneous utterance/vertex/action relabeling controls;
8. intervention-cost permutation controls;
9. a proof or exhaustive finite check of the residual automorphism group of the active oracle;
10. at least one preregistered query whose response law is non-invariant under each targeted residual symmetry;
11. direct recovery metrics for `Q`, `P`, and `d` in addition to DAG accuracy and intervention cost;
12. fail-closed reporting when active search recovers only an unlabeled or jointly recodable structure;
13. disclosure of all parser, simulator, actuator, sensor, and target-label leakage;
14. immutable commands, dependencies, assets, checksums, resource measurements, and three seeds when execution begins.

## Public-code availability audit

The PMLR paper states that source code and experimental details are included in the appendices/supplementary material, and the first author's publication page exposes a Code link for this work. However, C059 did not establish a paper-specific author repository with an immutable Git commit through the accessible primary records.

Classification:

> Primary paper, proofs, and author-declared code are public; a paper-specific immutable repository commit was not confirmed in C059.

No unofficial reimplementation was started. The audited algorithm assumes a supplied essential graph and fixed indexed variables, so even a successful reproduction would be a causal-search baseline rather than a reproduction of joint language/target identification.

## Decision

**NARROWED BEYOND ADVICE-GUIDED ACTIVE CAUSAL STRUCTURE RECOVERY — NOT ADOPTED**

Reason:

- active causal structure recovery with imperfect advice and worst-case robustness is established prior art;
- the theorem assumes a common fixed vertex alphabet shared by advice, interventions, and observations;
- that common alphabet supplies the correspondence that raw-language grounding would need to discover;
- exact graph recovery and low intervention cost are invariant under simultaneous advice/vertex/action/utterance relabeling;
- adaptive interaction cannot remove a symmetry when the complete query-response-cost oracle is equivariant under it;
- no theorem for joint recovery of `Q`, `P`, and `d` is provided.

## Surviving candidate after C059

> After recovering the strongest unlabeled causal structure and target partition available from non-language observations, and treating raw language only as fallible unparsed advice, determine whether a preregistered family of physically indexed active probes has a query-response-cost law whose stabilizer intersects the residual language/target automorphism group only in the permitted trivial equivalence; if so, establish whether this jointly identifies raw-language equivalence `Q`, residual target partition `P`, and denotation `d` without parser, simulator-label, or target-codebook leakage.

## Adoption gate after C059

RQ-001 remains not adopted. Adoption requires at least:

1. a formal active observation model with raw language, latent targets, available probes, response laws, and costs;
2. separation of parsed advice from raw-language observations;
3. computation of the residual automorphism group before active probing;
4. a theorem showing that the chosen probe family reduces the group to the permitted trivial equivalence;
5. a necessity counterexample when probe asymmetry is removed;
6. direct `Q`, `P`, and `d` evaluation rather than only graph recovery or intervention savings;
7. a confirmed public baseline or preregistered faithful reproduction before architecture changes;
8. immutable commands, dependencies, assets, checksums, three seeds, model size, peak RSS, and wall time when experiments begin.

## Status

- RQ-001: narrowed further; not adopted.
- Advice-guided active causal structure learning: established prior art.
- Robust active graph recovery under bad advice: established prior art.
- Raw-language equivalence identification: not established.
- Joint target/denotation identification: not established.
- Public baseline reproduction: not started.
- Experiment started: no.
- New architecture: no.
- Novelty claim: no.
- Intelligence-principle claim: no.
- Capability-progress claim: no.
