# Causal Identifiability Audit C031

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Test-Time Learning of Causal Structure from Interventional Data

Wei Chen, Rui Ding, Bojun Huang, Yang Zhang, Qiang Fu, Yuxuan Liang, Han Shi, and Dongmei Zhang. ICML 2026 / arXiv:2602.19131.

Primary records:

- Microsoft Research publication page: https://www.microsoft.com/en-us/research/publication/test-time-learning-of-causal-structure-from-interventional-data/
- arXiv: https://arxiv.org/abs/2602.19131
- OpenReview predecessor record: https://openreview.net/forum?id=ZXs3pkmrRG

The paper studies causal discovery from multiple interventional datasets when the intervention targets are unknown. TICL combines test-time training with Joint Causal Inference. It self-augments an instance-specific training set and uses a PC-inspired two-phase supervised causal-learning procedure to infer both an interventional equivalence-class representation of the causal graph and the unknown intervention family.

The stated problem assumes Markovness and faithfulness, causal sufficiency, and intervention-context assumptions including exogeneity, complete randomized context, and a generic-context property. The target of identification is the invariant causal structure represented by an I-CPDAG together with intervention-target detection; it is not an unknown semantic partition over raw utterances.

The Microsoft Research and arXiv primary records confirm the paper and its ICML 2026 status. The inspected primary records did not expose a paper-specific immutable official repository with pinned dependencies and reproduction commands. The earlier OpenReview record explicitly used an anonymous/no-public-URL submission setting. Therefore this cycle did not start a public baseline experiment.

## Theorem / assumption boundary added to the prior-art matrix

TICL removes a broad but incorrect novelty premise from RQ-001: unknown intervention targets do not by themselves imply that language is required.

Under the paper's causal sufficiency, faithfulness, context-exogeneity, randomized-context, and generic-context assumptions, interventional datasets can support joint inference of causal structure and unknown intervention targets without a natural-language channel. Test-time adaptation changes the estimator's ability to match the specific test distribution; it does not supply semantic denotations.

The following claims are therefore excluded from the novelty space:

- unknown intervention targets can only be recovered through language;
- multi-variable or soft unknown interventions are inherently outside non-language causal discovery;
- predicting the intervention family is evidence that raw utterance equivalence has been identified;
- test-time adaptation to an intervention environment is a language-grounding principle;
- higher I-CPDAG or target-detection accuracy proves recovery of a latent semantic target partition;
- a language description of an intervention contributes identifiability when it merely encodes the same context signature already used by JCI.

TICL and RQ-001 nevertheless remain distinct. TICL observes a collection of environment-indexed datasets and seeks a graph equivalence class plus intervention targets under explicit context assumptions. RQ-001 asks to discover both an equivalence relation over raw utterances and a residual latent intervention-target partition, while preventing their joint recoding.

## Identifiability counterexample: perfect unknown-target detection without raw-language equivalence recovery

Let interventional data be generated from a causal graph \(G\) and intervention family

\[
\mathcal I = \{I_0, I_1, \ldots, I_K\}.
\]

Assume the non-language estimator perfectly recovers the correct I-CPDAG and every intervention target set \(I_k\) from the environment-indexed distributions.

Now add raw utterances \(U\) generated for each environment through a language channel

\[
U \sim p(U\mid I_k, E_k),
\]

where \(E_k\) is the observed intervention-context identifier or any context statistic already sufficient for target detection.

Construct two language-grounding models:

- Model A uses an utterance equivalence relation \(Q\) and maps its classes to target blocks through \(d\).
- Model B applies a nontrivial bijection \(\pi\) to the target-block labels, recodes the utterance classes to \(Q'\), and uses \(d'=\pi\circ d\).

Adjust the language encoder and generator in Model B so that the conditional distribution of raw utterances given each observed environment is unchanged. The two models then agree on:

- every environment-conditioned observational and interventional distribution;
- the recovered I-CPDAG;
- every detected intervention target set;
- causal-edge and intervention-target metrics;
- next-state prediction, action accuracy, and task success for policies using the recovered targets;
- utterance likelihood and paraphrase accuracy after the joint recoding;
- language-shuffle gaps when the shuffle removes the same environment/target information.

Nevertheless, \(Q\neq Q'\), and the semantic names assigned to the target blocks differ. Perfect intervention-target detection therefore does not identify raw-language equivalence or its denotational alignment.

The counterexample becomes stronger when language is conditionally redundant:

\[
L \perp P_{residual}\mid S_{JCI},X,A,Y,H,
\]

where \(S_{JCI}\) is the maximal non-language statistic available from JCI/TICL, and \(X,A,Y,H\) contain observations, actions, outcomes, and interaction history. In that case language cannot refine the residual partition at population level.

## Necessary boundary for a surviving language contribution

Let \(S_{TICL}\) denote the strongest graph, context, and intervention-target information recoverable by a faithful non-language unknown-target method. Let \(P_{residual}\) be a target partition not determined by that information.

A necessary information condition is

\[
I(P_{residual};L\mid S_{TICL},X,A,Y,H) > 0.
\]

This condition is not sufficient. A surviving RQ also needs an externally fixed denotation law that prevents simultaneous permutation of:

- intervention-target blocks;
- utterance-equivalence classes;
- context labels;
- the language encoder/decoder; and
- any target-name output head.

Without that anchor, language can improve finite-sample target detection or optimization while leaving the joint semantic partition non-identifiable.

## Updated decision for RQ-001

**NARROWED BEYOND UNKNOWN-TARGET JCI / TEST-TIME CAUSAL DISCOVERY — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest non-language unknown-target causal-discovery method and conditioning on its complete graph, context, and intervention-target sufficient statistics, can a preregistered externally fixed language law distinguish a residual target partition that remains observationally and interventionally equivalent, jointly identify raw-utterance equivalence, and eliminate every joint relabeling of target blocks, utterance classes, and context labels?

Adoption now requires at minimum:

1. an explicit audit of whether the benchmark satisfies causal sufficiency, faithfulness, context exogeneity, randomized-context, and generic-context assumptions;
2. an immutable public reproduction of the strongest applicable unknown-target baseline when official code becomes available;
3. the maximal target partition recoverable without language;
4. a concrete pair of models with identical environment-indexed distributions and identical recovered I-CPDAG but different residual target partitions;
5. language information unavailable from environment identity, target-detection features, rewards, actions, outcomes, or completed trajectories;
6. a denotational anchor fixed before fitting;
7. a proof that the residual joint automorphism group is trivial;
8. an impossibility result when language only names the JCI context or detected intervention target;
9. direct utterance-partition and residual-target-partition recovery metrics, not only graph SHD, target F1, task success, or prediction accuracy;
10. language-blind, state-only, context-label-shuffle, target-label-shuffle, and outcome-shuffle controls on identical instances;
11. preregistration before any architecture work.

## Status

- RQ-001: further narrowed; not adopted
- unknown-target causal discovery without language: established by prior art under explicit assumptions
- raw-language equivalence identification: not established
- residual semantic target-partition identification: not established
- official paper-specific immutable code: not verified
- new architecture: none
- experiment started: no
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
