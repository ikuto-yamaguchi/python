# Causal Identifiability Audit C003

Date: 2026-07-25
Status: **RQ-001-N2 narrowed; not adopted**

## Purpose

This audit separates two claims that had been conflated:

1. **Language-information necessity**: raw language improves held-out prediction beyond state, action, history and environment identity.
2. **Joint semantic/causal identifiability**: raw utterance equivalence classes and latent intervention partitions are recoverable, up to an admissible equivalence such as joint permutation or causal abstraction.

Claim 1 does not imply Claim 2. A model may use language as an environment, policy, reward or episode-index proxy without recovering an intervention partition.

## Primary-source comparison

| Work | Observable grouping / supervision | Identifiable object | Relevance to RQ |
|---|---|---|---|
| Ng et al. 2025, CRL from General Environments | Environment-indexed distributions and sufficient mechanism changes | Latent variables and DAG under model/change assumptions | Environment grouping is supplied; raw language equivalence is not discovered |
| Li et al. 2025, Identifiability of Causal Abstractions | Contrastive pre/post pairs under a family of unknown subset interventions | The finest causal abstraction supported by the intervention family | Exact low-level variables may be impossible even without language |
| Lee et al. 2026, Beyond Identifiability | Multiple environments with unknown multi-node interventions in a finite-sample model | Graph, mixing representation and unknown targets | Removes novelty from few-environment unknown-target recovery; no raw-language view |
| Schneider et al. 2025, Generative Intervention Models | Perturbation features plus intervention-distribution data | Mapping from perturbation features to distributions over atomic interventions | Utterance features can be substituted as perturbation features; prediction alone is not a new contribution |
| Zhong et al. 2021/2022, SILG and LDD | Symbolic state/action APIs and language-described interactive trajectories | Policy/dynamics improvement, not causal-variable identifiability | Establishes the prediction baseline that must be reproduced first |
| Gamella et al. 2025, real-system CRL sanity check | Controlled real system with known factors | Empirical recovery benchmark | Shows that theorem assumptions and practical recovery must be audited separately |

## Two-gate formulation

### Gate L — Language-specific predictive information

On a public interactive benchmark, the full model must outperform all of the following on the **same held-out episodes**:

- state + action + history only
- environment-ID only
- language-only
- within-environment utterance shuffle
- transition shuffle
- target-label shuffle when labels are available for evaluation only

Required metrics:

- task success
- next-state prediction
- action accuracy
- held-out entity transfer
- held-out dynamics/mechanism transfer
- meaning-preserving paraphrase retention
- full entity rename retention

Passing Gate L establishes only that language contains usable information not captured by the controls. It does **not** establish semantic or causal identifiability.

### Gate I — Joint intervention-partition identifiability

Gate I is evaluated only after Gate L passes. The recovered structure must predict held-out interventions and align with the evaluation-only intervention partition under an admissible matching:

- exact matching is prohibited unless observable anchors justify names;
- joint-permutation-aware matching is the default;
- abstraction-aware matching is required when the intervention family cannot separate low-level variables.

Necessary controls:

- utterance-cluster shuffle
- latent-partition shuffle
- environment-label shuffle
- policy-history shuffle
- reward-only and terminal-state-only probes

A positive Gate I result requires that the same recovered partition supports prospective prediction on held-out mechanisms. Post-hoc clustering agreement alone is diagnostic.

## No-go statements

### N1 — Predictive language gain is not semantic identifiability

If an utterance predicts environment identity, task family, reward density or policy phase, a full model can outperform state-only controls while carrying no recoverable intervention semantics.

Therefore `Full > State-only` is insufficient.

### N2 — Joint names are not identifiable without anchors

For any simultaneous permutation of latent-variable identities and utterance-equivalence identities that preserves the transition kernel, the observable trajectory distribution is unchanged. Exact names cannot be a valid target.

### N3 — Intervention-limited data may identify only an abstraction

If the available interventions never separate two latent components, no learner can be required to recover them as distinct variables. The target must be the finest intervention-supported abstraction.

### N4 — Supplied environment partitions can silently solve the hard part

CRL guarantees that assume environment-indexed distributions do not directly establish recovery when the learner must infer those environment/intervention partitions from raw trajectories and language.

## Revised candidate question

**RQ-001-N3:**

> On a fixed public interactive benchmark, does raw language provide predictive information about held-out mechanism changes beyond state, action, history, reward and environment identity; and, conditional on that predictive gain, can an utterance-conditioned intervention partition be recovered up to joint permutation or the finest intervention-supported causal abstraction, without target labels, semantic parsers, object slots, pretrained language models or supplied perturbation semantics?

Status: **NARROWED AGAIN — NOT ADOPTED**.

## Adoption conditions

RQ-001-N3 may be preregistered only after:

1. SILG/RTFM recurrent baseline is reproduced on canonical seeds 1, 7 and 19.
2. Matched state-only, language-blind, language-shuffle and transition-shuffle controls are measured on identical episodes.
3. Gate L is nontrivially testable on at least two environment families.
4. Evaluation-only intervention partitions can be constructed without exposing them to training.
5. A literature audit finds no prior work satisfying both Gate L and Gate I under the same restrictions.

## Rejection conditions

Reject the RQ if any of the following holds:

- language gain disappears after environment-ID, reward, history and transition controls;
- gain is absent on held-out mechanisms or full entity rename;
- GIM-style perturbation-feature modeling fully subsumes the operational setting;
- only post-hoc cluster agreement improves while prospective capability does not;
- the public environments do not contain intervention diversity sufficient to define a nontrivial partition;
- a primary source already demonstrates the same joint recovery under equal or weaker supervision.

## Program consequence

No new architecture is authorized. The next C work is to operationalize Gate L on the reproduced SILG trajectories, then determine whether Gate I is even well-defined for RTFM or Messenger. If it is not, RQ-001-N3 must move to a benchmark with explicit evaluation-only mechanism interventions rather than modifying SILG into another toy task.

## Primary sources

- https://proceedings.mlr.press/v258/ng25a.html
- https://proceedings.mlr.press/v258/li25g.html
- https://arxiv.org/abs/2603.25796
- https://proceedings.mlr.press/v267/schneider25a.html
- https://proceedings.mlr.press/v267/gamella25a.html
- https://proceedings.neurips.cc/paper_files/paper/2021/hash/b3e3e393c77e35a4a3f3cbd1e429b5dc-Abstract.html
- https://proceedings.neurips.cc/paper_files/paper/2022/hash/51053d7b8473df7d5a2165b2a8ee9629-Abstract-Conference.html
