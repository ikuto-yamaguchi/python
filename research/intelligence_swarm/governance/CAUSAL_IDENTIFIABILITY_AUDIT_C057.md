# Causal Identifiability Audit C057

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + assumption/observation/guarantee comparison + official-code audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Learning to Model the World With Language

Jessy Lin, Yuqing Du, Olivia Watkins, Danijar Hafner, Pieter Abbeel, Dan Klein, and Anca Dragan. ICML 2024 Oral.

Primary records:

- PMLR: https://proceedings.mlr.press/v235/lin24g.html
- arXiv: https://arxiv.org/abs/2308.01399
- project page: https://dynalang.github.io/
- official repository: https://github.com/jlin816/dynalang
- audited repository commit: `5e3b93d4cdf3318537a97faa64a01219b82912a8`

Dynalang is directly relevant to the language-dynamics-pretraining component of RQ-001. It trains a multimodal world model over interleaved text and visual observations, predicts future representations and rewards, learns a policy from imagined rollouts, and supports text-only pretraining before downstream embodied control.

## RQ variables

Let:

- `U` be raw language observations or instructions;
- `X_t` be non-language observations at time `t`;
- `A_t` be actions;
- `R_t` be rewards;
- `Z_t` be the learned multimodal world-model state;
- `Q` be the unknown raw-language equivalence relation;
- `P` be the unknown latent intervention-target partition;
- `d: U/Q -> P` be the denotation map required by RQ-001.

## Observations available to Dynalang

Depending on the benchmark, the learner receives:

- raw or pre-embedded text tokens;
- image or symbolic environment observations;
- actions during online interaction;
- rewards and termination signals;
- sequential ordering of text and visual observations;
- benchmark-specific environment generators and task splits;
- optional offline text-only data such as TinyStories;
- optional replay data from a downstream environment when monitoring pretraining.

The central learning signal is future prediction: past language is useful when it improves prediction of future text, visual observations, latent states, or rewards.

## Assumptions embedded in the method and benchmarks

Dynalang's empirical success relies on at least the following:

1. language is statistically informative about future observations, dynamics, rewards, or useful actions;
2. the train and evaluation environments share enough latent structure for future-predictive representations to transfer;
3. the multimodal sequence order preserves relevant temporal dependencies;
4. the world-model state has sufficient capacity to encode both language and environment information;
5. benchmark rewards orient which predictive distinctions are behaviorally valuable;
6. text-only pretraining data shares reusable regularities with downstream language;
7. tokenization or sentence embeddings preserve task-relevant distinctions;
8. environment generators, entity inventories, action semantics, and train/test splits do not introduce unreported semantic supervision;
9. predictive equivalence is sufficiently close to the semantic distinctions required by the tasks;
10. no observationally indistinguishable but semantically distinct target ontology is required for success.

These assumptions support learning and transfer. They are not an identifiability theorem for `Q`, `P`, and `d`.

## Guarantees actually established

The paper establishes empirical results showing that:

- diverse language can be integrated into a multimodal predictive world model;
- future prediction can support language-conditioned control;
- language about future observations, corrections, dynamics, instructions, and manuals can improve task performance;
- imagined world-model rollouts can train a policy;
- text-only pretraining can improve downstream embodied performance;
- the same model family can generate environment-conditioned language;
- Dynalang outperforms several language-conditioned RL baselines on the reported tasks.

The paper does not prove:

- unique recovery of raw-language equivalence classes;
- unique recovery of latent intervention-target blocks;
- unique recovery of the language-to-target denotation;
- causal identification of target variables from prediction alone;
- elimination of language/state/target/world-interface permutations;
- separation of semantic grounding from reward, generator, embedding, or benchmark-interface supervision;
- that future-predictive equivalence equals semantic equivalence;
- that text-only pretraining removes cross-system recoding ambiguity.

## Prior-art boundary added to the matrix

The following claims are excluded from the novelty space:

- treating language as a signal for future-state, future-text, or reward prediction;
- grounding diverse language through a multimodal predictive world model;
- jointly modeling text and visual observations as a temporal sequence;
- learning a policy from imagined rollouts of a language-aware world model;
- pretraining an embodied world model using text-only corpora;
- transferring text-only predictive structure into downstream RL;
- using future prediction to unify instructions, environment descriptions, dynamics statements, and corrections;
- generating language from an embodied latent world model;
- claiming novelty merely because language-dynamics pretraining improves downstream policy performance.

Therefore, RQ-001 cannot claim novelty from the combination of language modeling, multimodal future prediction, world-model pretraining, and downstream control alone.

## Boundary between predictive grounding and semantic identification

Dynalang demonstrates **future-predictive functional grounding**: language representations become useful because they help predict future observations, rewards, or text and thereby improve control.

RQ-001 asks for a stronger property. The complete observational and interactive law must uniquely determine:

1. which raw expressions are equivalent;
2. which latent targets belong to the same intervention block;
3. which language class denotes which target block.

A predictive objective distinguishes only contrasts that change its prediction targets. Any semantic distinction that leaves the available future distribution unchanged is invisible to the objective.

Likewise, prediction can identify a sufficient statistic for future behavior without identifying the ontology that generated it. Multiple latent partitions and denotation maps may induce the same predictive state process.

## Identifiability counterexample A: future-predictive recoding

Assume an oracle Dynalang perfectly predicts:

- all future text;
- all future visual observations;
- all rewards;
- all action-conditioned transitions;
- all latent rollout distributions;
- all downstream optimal actions.

Let `sigma` be a non-identity permutation of latent target blocks. Construct a second model by simultaneously transforming:

- raw-language classes;
- target-block labels;
- world-model latent coordinates;
- language-encoder outputs;
- target-indexed transition interfaces;
- reward-interface bookkeeping;
- policy and decoder inputs/outputs;
- benchmark evaluation labels.

The second model can preserve:

- the complete text distribution;
- the complete visual observation distribution;
- every action-conditioned future distribution;
- every reward distribution;
- world-model likelihood and reconstruction loss;
- next-token, next-state, and reward prediction;
- imagined rollout law;
- policy value and task success;
- language-shuffle effects computed on the same recoded interface.

Yet the external assignment from language classes to target blocks differs.

Therefore:

> Perfect multimodal future prediction and perfect downstream control do not uniquely identify denotation when language, latent targets, world-model coordinates, and environment interfaces admit a simultaneous recoding.

## Identifiability counterexample B: predictive-equivalent semantic refinement

Let two candidate target meanings `p1` and `p2` induce identical distributions over every observed future under every admissible action and language history:

`p(future text, future observation, reward | history, action, p1) = p(future text, future observation, reward | history, action, p2)`.

Construct Model A:

- `u1` and `u2` are synonyms;
- both denote one target block `p`.

Construct Model B:

- `u1` and `u2` have distinct meanings;
- they denote distinct targets `p1` and `p2`;
- the complete predictive and interactive law makes `p1` and `p2` indistinguishable.

Both models preserve:

- all text and visual sequences;
- all actions, rewards, and terminal outcomes;
- every world-model training target;
- every model-based rollout;
- every optimal policy and benchmark score;
- every text-pretraining loss;
- every downstream finetuning metric.

Nevertheless `Q_A != Q_B` and `P_A != P_B`.

Thus future-predictive equivalence does not imply semantic equivalence.

## Identifiability counterexample C: text-only pretraining cannot choose the cross-system map

Assume text-only pretraining perfectly recovers the complete language dynamics and the finest equivalence relation supported by the text corpus, `Q_text`. Assume non-language interaction separately recovers the finest intervention partition supported by the environment, `P_env`.

For any nontrivial bijection `sigma` between equally sized blocks, define:

`d_sigma(q) = sigma(d(q))`.

If the downstream target interface, language encoder, policy, and decoder are transformed consistently, text likelihood, environment likelihood, and task performance remain unchanged.

Therefore text-only pretraining may improve optimization, representation quality, and sample efficiency while leaving the cross-system denotation symmetry intact.

## Identifiability counterexample D: reward-predictive collapse

Two utterances may describe different latent facts but imply the same reward and optimal policy on every training and evaluation task. A reward-predictive world model may collapse them without penalty. Conversely, two true paraphrases may remain internally distinct while producing identical rollouts and actions.

Hence policy success, reward prediction, and latent rollout accuracy do not directly score `Q`, `P`, or `d`.

## Consequence for interactive language grounding

Interaction improves identifiability only when it creates a contrast that separates previously predictive-equivalent candidate targets. Repeating trajectories sampled from the same predictive law adds data but does not break the symmetry.

A useful interaction must therefore be specified in terms of the residual automorphism group. It must produce an observable consequence that differs between candidate denotation maps while not directly supplying the gold target identity.

Examples of insufficient additions include:

- more rollouts under the same policy and world law;
- more text sampled from the same corpus;
- reward labels that are unchanged across candidate targets;
- parser slots or target IDs derived from the benchmark ontology;
- sentence embeddings pretrained on equivalent target supervision;
- future prediction targets generated by a serving system that already uses the desired denotation.

## Mandatory controls introduced by C057

Before RQ adoption, a Dynalang/SILG/J-CRe3-style baseline must include:

1. language-only dynamics baseline;
2. language-blind world-model baseline;
3. reward-blind multimodal prediction baseline;
4. shuffled-text baseline preserving token and episode statistics;
5. future-target shuffle preserving marginal distributions;
6. latent-coordinate permutation control;
7. simultaneous utterance/target/world-interface permutation control;
8. text-only pretraining with random or mismatched corpus control;
9. frozen random text encoder and pretrained encoder controls;
10. direct evaluation of `Q`, `P`, and `d` separately;
11. held-out interventions that distinguish targets with identical training futures;
12. countermodels with identical predictive likelihood and policy value but different semantic partitions;
13. disclosure of parser, tokenizer, sentence-embedding, environment-generator, entity, reward, and split leakage;
14. preregistration of which observable contrast removes which residual automorphism.

## Official public-code audit

Official repository:

https://github.com/jlin816/dynalang

Audited commit:

`5e3b93d4cdf3318537a97faa64a01219b82912a8`

The repository provides:

- the Dynalang implementation adapted from DreamerV3;
- HomeGrid, Messenger, VLN, LangRoom, and text-pretraining entry points;
- example shell scripts accepting a seed;
- a Dockerfile;
- `pyproject.toml` and setup metadata;
- a pinned VLN conda environment for legacy Habitat dependencies;
- instructions for external Messenger, VLN-CE, Habitat, Matterport3D, R2R, and Hugging Face assets;
- text-only TinyStories pretraining and downstream world-model checkpoint loading instructions;
- multi-GPU configuration guidance.

Reproduction gaps:

- no single hermetic environment covering all reported tasks;
- several external repositories, forks, datasets, embeddings, and legacy dependencies are required;
- no repository-wide immutable asset checksum manifest;
- no canonical paper-wide three-seed command manifest in the audited README;
- no bundled raw-result checksum set;
- no model-byte, peak-RSS, wall-time, or CPU-latency report;
- same-paper batch sizes may require multiple GPUs;
- Matterport3D download requires a legacy Python 2.7 path in the documented workflow;
- no direct `Q`, `P`, or `d` recovery metric;
- no identifiability countermodel benchmark.

Classification:

> Official code, exact commit, task scripts, Dockerfile, and text-pretraining workflow are available. A single hermetic R0 reproduction bundle and semantic-identification evaluation are not available.

Public baseline reproduction was not started in C057. Starting it requires a preregistered task subset, exact commands, dependency and external-asset pinning policy, seed list, resource budget, model-byte/RSS/time measurements, artifact checksums, and direct partition metrics. No unofficial architecture modification was made.

## Decision

**NARROWED BEYOND FUTURE-PREDICTIVE MULTIMODAL LANGUAGE WORLD MODELS — NOT ADOPTED**

Reason:

- language-conditioned multimodal future prediction is established prior art;
- language dynamics and text-only pretraining can already improve embodied world-model control;
- the established result is functional and empirical rather than a joint-identifiability theorem;
- predictive-equivalent targets can support different semantic refinements;
- simultaneous language/target/latent/world-interface recoding preserves the complete predictive and interactive law;
- text-only pretraining cannot by itself choose the external denotation map;
- task success and prediction loss do not directly evaluate `Q`, `P`, or `d`.

## Surviving candidate after C057

> After recovering the finest raw-language equivalence supported by legitimate language dynamics, the finest target partition supported by non-language interventions, and the strongest future-predictive multimodal alignment obtainable from Dynalang-like world modeling, determine whether a preregistered cross-system intervention uniquely separates only the remaining predictive-, policy-, and reward-aliased classes while eliminating every utterance/target/latent/world-interface recoding that preserves the complete language, observation, transition, reward, and action laws.

This candidate is not adopted. A positive result must identify an observable cross-system contrast that is unavailable to language-only prediction and non-language world modeling, does not directly encode the gold target or denotation, and provably reduces the residual automorphism group to the permitted equivalence.

## Next gate

Before any architecture proposal:

1. map SILG/J-CRe3 observations and labels onto the Dynalang observation/assumption table;
2. define language-dynamic, future-predictive, policy, reward, intervention, and semantic equivalence separately;
3. select a minimal official Dynalang baseline task and immutable runtime policy;
4. preregister three seeds, resource limits, model-byte measurement, peak RSS, wall time, and artifact checksums;
5. add direct `Q`, `P`, and `d` scoring rather than future prediction or success alone;
6. create matched environments with identical training future laws but different held-out intervention responses;
7. specify the held-out interaction that separates those environments without using target IDs or semantic codebooks;
8. prove which simultaneous recodings remain before and after that interaction;
9. reject the RQ if the required anchor directly supplies the denotation.

## Claim discipline

- RQ-001: narrowed, not adopted.
- Language-conditioned multimodal future prediction: established empirical prior art.
- Text-only pretraining of an embodied world model: established empirical prior art.
- Future-predictive functional grounding: established empirical prior art.
- Joint identification of raw-language equivalence and latent intervention partition: not established.
- Official code: available and exact commit fixed.
- Public baseline reproduction: not started.
- Experiment: not started.
- Model size / peak RSS / wall time / three seeds: not yet applicable.
- New architecture: none.
- Novelty claim: none.
- Intelligence-principle claim: none.
- Capability-progress claim: none.
