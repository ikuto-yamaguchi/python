# Causal Identifiability Audit C030

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Causal Abstraction Inference under Lossy Representations

Kevin Muyuan Xia and Elias Bareinboim. ICML 2025, PMLR 267:68225–68235.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/xia25a.html
- OpenReview: https://openreview.net/forum?id=WDybFnCPaB
- paper PDF: https://raw.githubusercontent.com/mlresearch/v267/main/assets/xia25a/xia25a.pdf

The paper addresses a case directly relevant to the remaining RQ-001 boundary: several distinct low-level interventions may be mapped by a lossy abstraction to the same high-level intervention even though their low-level effects differ. Standard abstraction definitions often require an abstract-invariance condition that is violated in this setting. Xia and Bareinboim replace the deterministic high-level intervention image with a **projected abstraction** that represents the lost low-level detail through a distribution over low-level interventions or states.

The framework preserves the ability to translate observational, interventional, and counterfactual queries between levels. It also provides graphical criteria for identifying and estimating high-level causal queries from limited low-level data when the full low-level causal model is unavailable. Thus, ambiguity induced by many-to-one intervention mappings is not by itself a new language-grounding problem: part of that ambiguity can already be represented and queried formally without recovering a unique fine-grained low-level partition.

No paper-specific official software link is exposed by the PMLR or OpenReview records. Targeted searches located the paper and author records but did not establish an immutable author-maintained reproduction repository with pinned dependencies. Therefore this cycle did not start a public baseline experiment.

## Theorem / assumption boundary added to the prior-art matrix

Projected abstraction and the remaining RQ-001 ask different questions.

Projected abstraction assumes or constructs a low-to-high abstraction and then asks whether causal queries remain well-defined and identifiable despite information loss. Its guarantee is query-level: observational, interventional, and counterfactual quantities at the abstract level can remain meaningful even when multiple low-level interventions collapse to one abstract intervention.

RQ-001 instead asks whether two unknown partitions can be recovered jointly:

1. an equivalence relation over raw utterances; and
2. a latent intervention-target partition.

The projected-abstraction result removes the following claims from the novelty space:

- that many-to-one mappings from low-level interventions to one high-level intervention are inherently invalid;
- that distinct low-level interventions must always be separated before high-level causal reasoning is possible;
- that language is required merely because a representation is lossy;
- that recovering accurate abstract interventional or counterfactual queries proves recovery of the fine-grained latent target partition;
- that a human-readable high-level label resolves which low-level intervention generated an abstract effect.

The remaining question can only concern distinctions that are required for joint partition identification but are intentionally marginalized by the strongest valid projected abstraction.

## Identifiability counterexample: perfect abstract query recovery without joint partition recovery

Let low-level intervention targets be

\[
T = \{t_1,t_2,t_3,t_4\},
\]

and let a lossy high-level intervention map be

\[
\alpha(t_1)=\alpha(t_2)=h_0, \qquad
\alpha(t_3)=\alpha(t_4)=h_1.
\]

Assume a projected abstraction stores, for each high-level intervention, the correct conditional distribution over the low-level members that were collapsed. It therefore answers every permitted high-level observational, interventional, and counterfactual query exactly.

Now construct two models.

- Model A uses the fine partition \(P=\{\{t_1\},\{t_2\},\{t_3\},\{t_4\}\}\) and an utterance partition \(Q\).
- Model B swaps or mixes \(t_1,t_2\) within the fibre \(\alpha^{-1}(h_0)\), and simultaneously recodes the corresponding utterance classes, producing \(P'\neq P\) and \(Q'\neq Q\).

Choose the projected mixing distribution in Model B so that the induced high-level projected abstraction is unchanged. Then the two models agree on:

- every high-level observational query;
- every high-level intervention query;
- every high-level counterfactual query admitted by the abstraction;
- task success and action accuracy for policies using only the high-level abstraction;
- next-state prediction at the high level;
- utterance prediction and paraphrase accuracy after the joint language recoding;
- language-shuffle gaps when the shuffle destroys the same high-level label information.

Nevertheless, the fine-grained target partition and raw-utterance equivalence differ inside the lossy fibre.

Therefore:

> Exact identification of all queries supported by a projected abstraction does not identify the fine-grained intervention-target partition or the raw-language equivalence classes hidden inside an abstraction fibre.

This is not a failure of projected abstraction. It is precisely the information that the abstraction is allowed to discard. RQ-001 cannot count recovery of abstract causal queries as evidence that the discarded partition has been jointly recovered.

## Necessary boundary for a surviving language contribution

Let \(A_{proj}\) denote the maximal projected abstraction justified by the low-level data and valid graphical criteria, and let \(P_{fiber}\) denote a residual partition within one of its fibres.

A necessary information condition for language to refine that fibre is

\[
I(P_{fiber};L\mid A_{proj},X,A,Y,H) > 0,
\]

where \(X,A,Y,H\) include observations, actions, outcomes, and interaction history available to the non-language baseline.

Even this is insufficient unless the denotation law is externally fixed. Otherwise a permutation or more general automorphism inside each abstraction fibre can be absorbed jointly by:

- the fine target partition;
- the utterance equivalence relation;
- the language encoder/decoder; and
- the projected mixing distribution.

The surviving theorem obligation is therefore stronger than query preservation: the external language law must make the automorphism group within every relevant projected-abstraction fibre trivial.

## Updated decision for RQ-001

**NARROWED BEYOND LOSSY PROJECTED CAUSAL ABSTRACTIONS — NOT ADOPTED**

The only remaining candidate is:

> After constructing the strongest valid projected abstraction and identifying every high-level query available from low-level data, can a preregistered externally fixed language law distinguish fine-grained target partitions inside a lossy abstraction fibre, jointly identify the corresponding raw-utterance equivalence, and eliminate all fibre-preserving joint recodings?

Adoption now requires at minimum:

1. an explicit projected abstraction and its identified query class;
2. a concrete fibre containing at least two observationally and interventionally indistinguishable fine partitions under the non-language evidence;
3. a language contrast unavailable from observations, actions, outcomes, environment identity, or completed trajectories;
4. an externally fixed denotational anchor established before fitting;
5. a proof that all fibre-preserving automorphisms are removed;
6. an impossibility theorem when language only names the high-level projected intervention;
7. direct recovery metrics for utterance classes and fine target blocks, not only high-level query accuracy or task success;
8. true-group, projected-group, predicted-group, language-blind, state-only, target-label-shuffle, and outcome-shuffle controls;
9. public baseline reproduction and preregistration before any architecture work.

## Status

- RQ-001: further narrowed; not adopted
- projected high-level causal-query identification: established by prior art under its assumptions
- fine target-partition recovery inside lossy fibres: not established
- raw-language equivalence identification: not established
- official paper-specific code: not verified
- new architecture: none
- experiment started: no
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
