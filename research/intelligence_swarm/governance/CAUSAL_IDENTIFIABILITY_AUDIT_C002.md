# Causal Identifiability Audit C002

## Scope

This cycle does not introduce a new architecture. It narrows RQ-001-N using primary-source overlap and an explicit identifiability counterexample.

## New closest prior art

### Generative Intervention Models (Schneider et al., ICML 2025)

GIM jointly estimates a causal model and maps observed perturbation features to distributions over atomic interventions, including prediction for unseen perturbation features.

Consequence for this program:

- treating a raw utterance embedding merely as a perturbation feature and learning a distribution over intervention targets is not by itself novel;
- a defensible contribution must remove or test assumptions that GIM retains, such as supplied perturbation features, non-interactive distributional supervision, or a representation whose semantics need not be recovered from raw language;
- RQ-001-N therefore cannot claim novelty from `language -> intervention distribution` alone.

### Isolated Causal Effects of Natural Language (Lin et al., ICML 2025)

This work formalizes causal effects of focal language changes on external outcomes and emphasizes bias from inadequate approximation of non-focal language.

Consequence:

- language interventions and external outcomes are already a formal causal-estimation topic;
- our remaining gap is not “language can be treated causally,” but whether raw interactive language contributes identifiable information about a latent intervention partition beyond observed state/action/history.

### Sanity Checking CRL on a Simple Real-World System (Gamella et al., ICML 2025)

Representative CRL methods fail even on a controlled optical system satisfying their headline assumptions, with reproducibility failures already visible in simplified synthetic ablations.

Consequence:

- theory-only identifiability is insufficient;
- public baseline reproduction and a real or public interactive benchmark remain mandatory before a new mechanism is admissible.

## Exact no-go statement

Let the observable trajectory be

`O = (X_t, U_t, A_t, X_{t+1}, E)`

where `U_t` is a raw utterance and `E` is an observed environment identifier. Let `Z` be latent causal variables and `T(U)` the latent intervention partition induced by an utterance.

Assume:

1. no semantic anchor, shared object identifier, intervention-target label, parser, pretrained language model, or cross-environment lexical correspondence is supplied;
2. the learner observes only the joint distribution of `O`;
3. the data-generating family is closed under a joint permutation `pi` of latent variables and utterance-equivalence labels.

Then exact latent-variable names and exact utterance-to-target names are not identifiable. For every admissible model `M`, a jointly permuted model `M_pi` induces the same observable distribution. Recovery is possible at most up to the joint permutation orbit, or up to a coarser causal abstraction if the intervention family does not separate individual variables.

This is stronger than saying “zero-shot rename is hard.” It states that exact naming is not a valid target without an observable symmetry breaker.

## What language must prove

A language-aware model must not merely predict better than random. It must show information not already present in state/action/history.

The minimum empirical necessity test is:

`Delta_lang = score(full) - score(state_action_history_only)`

on held-out mechanisms and held-out language forms, with the same trajectories, seeds, parameter budget, and optimization budget.

Required controls:

- within-environment utterance shuffle;
- transition shuffle preserving marginal state/action frequencies;
- entity rename and paraphrase-preserving equivalence;
- environment-ID-only and history-only baselines;
- intervention-target-label shuffle when labels exist only for evaluation.

A positive `Delta_lang` is still not semantic identifiability. Promotion additionally requires:

- invariance to joint renaming;
- recovery scored up to optimal latent permutation or abstraction map;
- stable gain across at least two environment families and all three preregistered seeds;
- collapse under language shuffle but not under meaning-preserving paraphrase;
- prospective task success or next-state prediction, not post-treatment reconstruction only.

## RQ decision

Status: **NARROW AGAIN; NOT ADOPTED**.

Revised candidate:

> On a fixed public interactive benchmark, does raw language contain statistically necessary information about an intervention partition or causal abstraction beyond state, action, history and environment identity, and can that information be recovered up to joint permutation without target labels, semantic parsers, object slots, pretrained language models, or perturbation-feature supervision?

## Rejection conditions

Reject the RQ if any of the following holds:

1. GIM or another primary source already demonstrates the same raw-language, interactive, no-target-label setting;
2. SILG/LDD reproduction yields no stable full-vs-state/action/history gain on held-out mechanisms;
3. the gain disappears under entity rename or meaning-preserving paraphrase;
4. recovery is only exact-name accuracy and vanishes when evaluated up to latent permutation;
5. the method requires supplied perturbation features, object slots, target candidates, or intervention-axis labels;
6. results do not reproduce across two environment families and seeds 1, 7 and 19.

## Primary sources

- Schneider et al., Generative Intervention Models for Causal Perturbation Modeling, ICML 2025: https://proceedings.mlr.press/v267/schneider25a.html
- Lin et al., Isolated Causal Effects of Natural Language, ICML 2025: https://proceedings.mlr.press/v267/lin25k.html
- Gamella et al., Sanity Checking Causal Representation Learning on a Simple Real-World System, ICML 2025: https://proceedings.mlr.press/v267/gamella25a.html
- Li et al., On the Identifiability of Causal Abstractions, AISTATS 2025: https://proceedings.mlr.press/v258/li25g.html
- Ng et al., Causal Representation Learning from General Environments under Nonparametric Mixing, AISTATS 2025: https://proceedings.mlr.press/v258/ng25a.html

## Claims not made

- no new intelligence principle;
- no capability improvement;
- no public baseline reproduction;
- no exact semantic identity recovery;
- no high-school-level intelligence.
