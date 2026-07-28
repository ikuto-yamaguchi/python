# Causal Identifiability Audit C053

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code availability audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Interaction-Grounded Learning

Tengyang Xie, John Langford, Paul Mineiro, and Ida Momennejad. ICML 2021.

Primary records:

- PMLR: https://proceedings.mlr.press/v139/xie21e.html
- paper PDF: https://proceedings.mlr.press/v139/xie21e/xie21e.pdf
- supplementary PDF: linked from the PMLR record
- Microsoft Research publication record: https://www.microsoft.com/en-us/research/publication/interaction-grounded-learning/
- arXiv: https://arxiv.org/abs/2106.04887

Relevant extensions included in the boundary audit:

- Xie et al., **Interaction-Grounded Learning with Action-Inclusive Feedback**, NeurIPS 2022 / arXiv: https://arxiv.org/abs/2206.08364
- Hu, Farnia, and Leung, **An Information Theoretic Approach to Interaction-Grounded Learning**, ICML 2024: https://proceedings.mlr.press/v235/hu24e.html
- Zhang et al., **Interaction-Grounded Learning for Contextual Markov Decision Processes with Personalized Feedback**, arXiv 2026: https://arxiv.org/abs/2602.08307

The ICML 2021 paper studies a learner that observes context `X`, chooses an action `A`, receives a multidimensional feedback vector `Y`, and never observes the binary latent reward `R`. The learner jointly selects a policy and a reward decoder from interaction data. This is directly relevant because it provides a positive identifiability result for an ungrounded signal without explicit reward labels.

The key boundary is that IGL identifies a reward decoder and a high-value policy under assumptions that orient the otherwise sign-ambiguous latent reward. It does not infer an unknown equivalence relation over raw language, an unknown partition of latent intervention targets, or an externally fixed denotation between the two.

## Assumption, observation, and guarantee comparison

Let:

- `X` be the observed context;
- `A` be an action selected from a finite action set;
- `R in {0,1}` be an unobserved latent reward;
- `Y` be the observed multidimensional feedback vector;
- `pi` be a policy mapping contexts to action distributions;
- `psi: Y -> [0,1]` be a reward decoder;
- `pi_bad` be a known low-value baseline policy, instantiated by uniform random actions in the main construction.

### Observations available to IGL

The learner observes interaction triples:

\[
(X,A,Y),
\]

but not `R`.

The learner is given or can execute a known baseline policy `pi_bad`, and it can collect exploratory interaction data under that policy.

### Assumption 1: conditional independence

The original result assumes:

\[
(X,A) \perp Y \mid R.
\]

Thus the feedback distribution depends on the interaction only through the latent binary reward. This excludes context- or action-specific feedback variation after conditioning on reward.

Under this assumption, the decoded value difference factorizes as:

\[
L(pi,psi)
= V(pi,psi)-V(pi_{bad},psi)
= (V(pi)-V(pi_{bad}))\,\Delta_{psi},
\]

where:

\[
\Delta_{psi}
= E[psi(Y)\mid R=1]-E[psi(Y)\mid R=0].
\]

This factorization makes the decoder-induced ordering of policies independent of the selected policy when `Delta_psi > 0`.

### Assumption 2: orientation / identifiability gap

Jointly maximizing over policy and decoder otherwise has two directions:

- the best policy paired with a correctly oriented decoder;
- the worst policy paired with an oppositely oriented decoder.

The paper therefore assumes a sufficiently bad baseline policy and a positive margin so that the correct orientation is the unique global optimum. Informally, random actions must be wrong often enough to distinguish positive from inverted reward semantics.

This assumption is an **orientation anchor**. It is not a discovery of unrestricted semantics from interaction alone. It introduces asymmetry through the known low-value reference policy.

### Guarantees

Under the conditional-independence and identifiability assumptions, the batch result gives finite-sample bounds on:

- the value regret of the learned policy;
- the reward-decoder quality gap;
- convergence to the correctly oriented policy-decoder solution after sufficient exploration data.

The online E2G construction interleaves uniform exploration and exploitation and provides a regret guarantee under related assumptions.

The guarantee concerns the policy value and decoder orientation relative to a binary latent reward. It does not guarantee recovery of a unique latent ontology or a raw-language semantic partition.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- discovering a useful latent binary reward decoder from unlabelled multidimensional interaction feedback;
- grounding an interactive policy without observing explicit reward labels;
- using a known low-value random policy to orient an otherwise sign-ambiguous latent feedback decoder;
- jointly optimizing a policy and feedback decoder through value-difference objectives;
- obtaining finite-sample policy and decoder guarantees under feedback conditional independence;
- obtaining online regret guarantees through exploration/exploitation in an ungrounded-feedback setting;
- allowing action information inside feedback through later action-inclusive IGL guarantees;
- enforcing or approximating the IGL conditional-independence assumption through information-theoretic objectives;
- extending latent-feedback grounding from contextual bandits toward sequential contextual MDPs;
- claiming that interaction alone is a new mechanism for grounding an unlabelled signal.

A language-conditioned agent that learns to exploit implicit feedback is therefore not by itself evidence for a new language-grounding principle. Interaction-grounded reward learning is established prior art.

## What the existing guarantees do not identify

The audited IGL line does not identify:

- an unknown equivalence relation `Q` over raw utterances;
- an unknown semantic intervention-target partition `P`;
- a denotation map `d: U_raw/Q -> P`;
- whether two raw forms with identical reward consequences are synonyms or distinct meanings with aliased utility;
- semantic distinctions that do not alter the binary reward distribution;
- the externally intended name or identity of a reward state;
- a target ontology finer than the reward-relevant partition;
- absolute semantic identity without the low-value-policy orientation anchor;
- elimination of simultaneous recodings of utterances, target blocks, reward labels, feedback decoder, and policy.

IGL recovers enough grounding to optimize reward. That guarantee is intentionally weaker than recovering a unique semantic ontology.

## Theorem/assumption boundary for RQ-001

Define:

- `Q`: an unknown equivalence relation over raw utterances;
- `P`: an unknown latent intervention-target partition;
- `d: U_raw/Q -> P`: denotation;
- `R`: an unobserved reward functional over interaction outcomes;
- `Y`: ungrounded feedback generated from `R` under the IGL assumptions;
- `B_R`: the coarsest partition of target meanings induced by equality of all reward and feedback laws under all admissible interactions.

IGL can identify a decoder sufficient to order policies by `R` when the required orientation anchor and conditional-independence structure hold. It does not establish:

\[
B_R = P,
\]

nor that the utterance partition `Q` or denotation `d` is uniquely determined.

A necessary condition for language to refine the reward-relevant partition is:

\[
I(P_{residual};U_{raw}\mid X,A,Y,R\text{-relevant signatures}) > 0.
\]

This remains insufficient. The full interaction law must eliminate every automorphism that changes `Q`, `P`, or `d` while preserving contexts, actions, feedback, decoded values, policy behavior, and reward orientation.

## Identifiability counterexample A: perfect IGL success, different language ontology

Assume unlimited data and oracle optimization. Let an IGL learner recover a reward decoder with correct orientation and an optimal policy with zero regret.

Construct Model A with:

- target meanings `p1, ..., pm`;
- utterance classes `q1, ..., qm`;
- denotation `d(qi)=pi`;
- latent binary reward `R`;
- feedback decoder `psi`;
- optimal policy `pi_star`.

For a non-identity permutation `sigma`, construct Model B by simultaneously applying `sigma` to:

- target blocks;
- utterance classes;
- denotation entries;
- language-encoder outputs;
- target-indexed policy inputs;
- target-indexed environment interfaces.

Keep the latent binary reward, feedback distribution, and known bad-policy orientation unchanged.

Models A and B preserve:

- the complete distribution of `(X,A,Y)` under every policy;
- the latent reward distribution;
- conditional independence `(X,A) independent of Y given R`;
- the value of every policy;
- the IGL objective for every policy-decoder pair;
- the identity of the low-value baseline policy;
- decoder orientation and `Delta_psi`;
- learned-policy regret;
- E2G exploration and exploitation statistics;
- action accuracy, task success, and feedback likelihood;
- any language-shuffle gap defined only through the same interaction behavior.

Yet the asserted correspondence between raw utterances and semantic targets differs. Therefore perfect IGL reward grounding does not remove joint utterance/target recoding.

## Identifiability counterexample B: reward-aliased semantic refinement

Let two candidate target meanings `p1` and `p2` have identical consequences under every admissible context and action:

\[
P(R,Y,X'\mid X,A,p1)
=
P(R,Y,X'\mid X,A,p2).
\]

Construct Model A:

- `p1` and `p2` form one semantic target block;
- raw forms `u1` and `u2` are synonyms in one utterance class.

Construct Model B:

- `p1` and `p2` are distinct semantic target blocks;
- `u1` and `u2` are distinct utterance classes;
- all reward, feedback, transition, and policy-relevant laws remain identical.

Both models satisfy the IGL assumptions and preserve:

- all interaction triples;
- all values `V(pi)`;
- all decoded values `V(pi,psi)`;
- the value-difference factorization;
- the orientation margin;
- the learned reward decoder;
- the optimal policy and regret;
- every downstream behavioral metric.

Nevertheless:

\[
Q_A \ne Q_B,\qquad P_A \ne P_B,
\]

and their denotation maps differ.

Therefore:

> Interaction can identify a reward-relevant grounding and orient a latent feedback decoder, while leaving every semantic distinction inside a reward-and-feedback-equivalent block unidentified.

## Identifiability counterexample C: the baseline policy is an anchor, not unrestricted discovery

Remove the assumption that a known baseline policy is sufficiently bad. For a binary latent reward, transform:

\[
R' = 1-R,
\qquad
psi'(Y)=1-psi(Y),
\]

and exchange the best and worst policy interpretations.

Without an independently justified orientation asymmetry, the observed `(X,A,Y)` law cannot in general determine which decoder orientation corresponds to intended success. The IGL identifiability assumption deliberately breaks this symmetry through `pi_bad`.

For RQ-001 this yields a strict audit rule:

- a known low-value policy, success prior, reward polarity, user preference direction, or task-completion convention is an external anchor;
- results depending on that anchor must not be described as unrestricted semantic discovery;
- if the anchor is derived from gold targets, parser slots, environment templates, terminal labels, or completed trajectories, it is potential target leakage.

## Consequence for interactive language grounding

A valid interactive-language experiment must separate three levels:

1. **reward grounding**: learning a decoder sufficient to optimize a latent reward;
2. **causal target recovery**: recovering the finest target partition distinguishable by non-language interventions and dynamics;
3. **semantic joint identification**: uniquely recovering raw-utterance equivalence, residual target partition, and denotation.

Success at level 1 does not establish level 2 or level 3. Success at level 2 does not establish level 3.

Before language receives credit for refining a target partition, the benchmark must:

1. instantiate the strongest language-blind unknown-target causal baseline;
2. instantiate an IGL-style feedback-only baseline using exactly the same interactions;
3. disclose every orientation anchor, including low-value policies and success conventions;
4. compute the finest reward-and-feedback-equivalence partition;
5. enumerate target pairs still aliased under all non-language interaction laws;
6. preregister language observations that could distinguish only those residual pairs;
7. exclude target-derived parser slots, IDs, templates, labels, terminal success, and completed-trajectory leakage;
8. directly score `Q`, residual `P`, and `d`;
9. include reward-polarity reversal, utterance permutation, target permutation, and joint recoding controls;
10. compare against a countermodel with the same complete interaction law and a different semantic ontology.

## Official public-code audit

The PMLR paper record, Microsoft Research publication page, arXiv record, author publication page, and targeted GitHub search did not expose a paper-specific author-maintained repository for the ICML 2021 E2G experiments.

The paper provides algorithmic descriptions, theoretical proofs, and proof-of-concept experiment details, but this audit did not locate:

- an official immutable implementation commit;
- a dependency lockfile;
- a container digest;
- a canonical command manifest;
- dataset/split checksums;
- raw experiment logs;
- a fixed multi-seed reproduction bundle;
- model-size, peak-RSS, or wall-time records.

Classification:

> Primary paper and theorem are public; no paper-specific official implementation was located in the audited primary records. Public baseline reproduction is therefore not claimed in C053.

No unofficial reimplementation was started because architecture or experiment work remains prohibited before baseline selection and preregistration.

## Decision update

Formal decision:

> **NARROWED BEYOND INTERACTION-GROUNDED LATENT-REWARD IDENTIFIABILITY — NOT ADOPTED**

The surviving candidate is:

> After recovering the strongest non-language causal target partition and the finest reward/feedback-equivalence partition identifiable from all legitimate interactions, determine whether a preregistered raw-language law uniquely separates only the remaining reward-and-intervention-aliased blocks and jointly identifies utterance equivalence, residual semantic target partition, and denotation, while eliminating every joint utterance/target/reward-decoder/policy recoding that preserves the complete interactive law.

Adoption requires at minimum:

- a formal distinction between reward-decoder identifiability and semantic partition identifiability;
- a complete inventory of all success-polarity and low-value-policy anchors;
- an IGL-style feedback-only baseline and a language-blind causal baseline;
- direct evaluation of `Q`, residual `P`, and `d`;
- reward-polarity reversal and joint recoding countermodels;
- a preregistered external denotational anchor if absolute target identity is claimed;
- a proof that the anchor removes the residual automorphism group;
- baseline reproduction or a preregistered faithful implementation before any new architecture.

## Current status

- RQ-001: further narrowed, not adopted
- interaction-grounded latent reward learning: established prior art
- latent feedback decoder orientation under a bad-policy anchor: established prior art
- raw-language equivalence recovery: not established
- joint language/target/denotation identification: not established
- official paper-specific code: not located
- public baseline reproduction: not started
- experiment started: no
- model size / peak RSS / wall time / three seeds: not yet applicable
- new architecture: none
- old A–E toy mechanism: none
- novelty claim: none
- intelligence-principle claim: none
- capability-progress claim: none
