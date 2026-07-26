# Causal Identifiability Audit C048

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Models with a Cause: Causal Discovery with Language Models on Temporally Ordered Text Data

Bruce Rushing and Javier Gomez-Lavin. Transactions on Machine Learning Research, accepted 2026.

Primary records:

- OpenReview: https://openreview.net/forum?id=YJddclPGuY
- official code: https://github.com/brushing-git/models-with-cause
- audited official commit: `42fa75a7ed081c468b7dd712a4fd7838c3ecfb16`
- audited README blob: `0acba7fd5bf488cd10e1861ee0ba7c37ba14d090`

The paper asks whether language-model architectures possess inductive biases needed to recover causal structure in token-generation processes. It studies synthetic mixtures of first- and second-order Markov chains and evaluates conditional-independence behavior, Markov exchangeability, intervention comparisons, and qualitative probability rankings. The official implementation evaluates NADE, encoder-decoder Transformer, decoder-only Transformer, and Switch Transformer models.

This work is relevant to the `language dynamics pretraining` part of the reconstruction. It shows that temporally ordered token data can support recovery of token-level causal dependencies under standard causal assumptions and that trained sequence models may learn qualitative structural properties without exactly matching the full probability distribution.

It does **not** study raw utterances denoting latent environment interventions, unknown intervention-target partitions, interactive grounding, or semantic equivalence classes over natural-language instructions.

## Assumption, observation, and guarantee comparison

### Object identified by the paper

Let a token sequence be `W_1, ..., W_T`. The paper's causal object is the dependency structure governing token generation under temporal order. Its theoretical route relies on the fact that temporal precedence constrains candidate causal directions and that standard causal-discovery assumptions permit a unique token-level causal model.

The empirical setup provides:

- explicitly temporally ordered discrete token sequences;
- data generated from known synthetic Markov-chain mixtures;
- first- or second-order transition laws;
- controlled interventions in dedicated synthetic comparisons;
- train/validation splits over generated sequences;
- conditional-independence and Markov-exchangeability tests;
- model probability or log-probability rankings.

The reported guarantee concerns causal discovery in the **token-generation process** when the token sequence satisfies the required causal assumptions. The experiments test whether neural sequence models learn structural properties needed by those discovery procedures.

### What is not guaranteed

The work does not guarantee identification of:

- an equivalence relation over complete raw utterances;
- synonymy or paraphrase classes defined by external denotation;
- a latent intervention-target partition in an environment;
- a denotation map from utterance classes to intervention targets;
- causal variables underlying the non-language world state;
- an interactive policy that grounds language through action;
- semantic identity across two distinct token generators;
- removal of simultaneous relabeling of vocabulary, utterance classes, target blocks, and decoders.

Token-level temporal causal structure and external semantic denotation are different identification targets. The former can be unique relative to observed token identities and their temporal law while the latter remains arbitrary under a joint recoding of symbols and world targets.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- using temporal ordering in text as causal orientation information;
- applying standard causal-discovery assumptions to token-generation processes;
- testing whether autoregressive language models learn conditional independencies;
- testing Markov exchangeability of learned sequence probabilities;
- using mixtures of Markov chains as controlled language-dynamics data;
- using synthetic token interventions to test causal probability rankings;
- showing that qualitative rankings can reflect causal structure without exact density recovery;
- comparing NADE, encoder-decoder, decoder-only, and mixture-of-experts sequence models for these properties;
- treating successful token-level causal discovery as sufficient evidence of environment grounding;
- treating language-dynamics pretraining alone as identification of raw-language equivalence or latent intervention targets.

The surviving RQ must therefore concern a cross-system relation between language and environment interventions that is not reducible to causal discovery inside the token stream.

## Theorem/assumption boundary for RQ-001

Define:

- `L_t`: token at language time `t`;
- `U`: a complete raw utterance;
- `X`: environment observations and trajectories;
- `E`: intervention environment identity;
- `P`: latent intervention-target partition;
- `Q`: an unknown equivalence relation over utterances;
- `d: U/Q -> P`: denotation.

Even if the complete token-level causal model `G_L` and its transition law are identified from unlimited language data, this identifies relations among token variables relative to the observed vocabulary. It does not identify `P`, `Q`, or `d` unless the joint language–environment observation law contains an independently fixed cross-modal asymmetry.

A necessary information condition for a residual target distinction is:

\[
I(P_{residual}; U \mid G_L, S_{nonlang}) > 0,
\]

where `S_nonlang` includes the strongest legitimate non-language state, action, reward, outcome, environment, trajectory, parser, entity, schema, and target metadata available to the learner.

This condition is not sufficient. The joint law must also eliminate every transformation that preserves `G_L`, the language likelihood, the environment law, and task behavior while changing `Q`, `P`, or `d`.

## Identifiability counterexample: perfect language dynamics with arbitrary grounding

Assume an oracle identifies the exact token-level causal DAG and transition law of the language generator. Assume a policy also achieves perfect task success after consuming utterances.

Construct Model A with:

- vocabulary `V`;
- token causal model `G_L`;
- utterance partition `Q`;
- environment target partition `P`;
- denotation `d`;
- language encoder `f` and policy/decoder `g`.

Construct Model B by selecting a nontrivial bijection `pi_V` on vocabulary symbols and a nontrivial bijection `pi_P` on target blocks, then transforming:

- every token sequence by `pi_V`;
- the token mechanisms so that the transformed sequence distribution is exactly the pushforward of Model A;
- utterance classes by the induced utterance recoding;
- target blocks by `pi_P`;
- denotation to `d' = pi_P o d o pi_Q^{-1}`;
- encoder and policy/decoder by the corresponding inverse recodings.

Model B preserves:

- the complete token-sequence probability law up to the observed-symbol recoding;
- temporal order;
- all token-level conditional independencies;
- the token causal DAG up to node/symbol relabeling;
- Markov order and Markov exchangeability;
- intervention probability rankings inside the token generator;
- language-model loss and perplexity;
- next-token and next-state prediction;
- action accuracy and task success;
- language-shuffle gaps when the shuffle destroys the same encoded control signal.

Nevertheless, the external meanings assigned to utterance classes and target blocks differ. Therefore:

> Perfect recovery of language dynamics, token-level causal structure, and task-controlling language signals does not identify raw-language equivalence, the latent intervention-target partition, or their denotation. It identifies a predictive/control code only up to a joint language–world recoding unless an external cross-system anchor removes that symmetry.

A stronger partition counterexample does not require vocabulary permutation. Suppose two utterance forms always induce the same token-context distribution and the same observable environment behavior. Model A places them in one semantic equivalence class. Model B places them in two classes denoting distinct latent targets whose effects are observationally identical under every available intervention. All token-level causal tests, language likelihoods, trajectories, rewards, and task metrics agree. Thus temporal language structure cannot decide whether the forms are synonyms or distinct but observationally aliased meanings.

## Consequence for language-dynamics pretraining

Language-dynamics pretraining can be credited with learning:

- token temporal dependencies;
- conditional-independence patterns;
- Markov or higher-order sequence structure;
- qualitative probability rankings;
- representations useful for predicting controlled synthetic interventions.

It cannot be credited, without direct cross-system evidence, with discovering:

- which utterances are semantically equivalent;
- which latent world variables are intervention targets;
- whether two behaviorally equivalent instructions have one meaning or two aliased meanings;
- a unique denotation from language to environment variables.

Accordingly, a language-dynamics baseline belongs in the benchmark as a **strong language-only control**, not as evidence that grounding was identified.

## Official-code and reproducibility audit

The authors provide paper-specific official code at `brushing-git/models-with-cause`. The audited head commit is:

`42fa75a7ed081c468b7dd712a4fd7838c3ecfb16`

The repository provides:

- synthetic first- and second-order Markov-chain generators;
- intervention data generation;
- NADE, encoder-decoder Transformer, decoder-only Transformer, and Switch Transformer implementations;
- conditional-independence tests;
- Markov-exchangeability experiments;
- intervention outcome and probability experiments;
- hyperparameter-search scripts;
- training entry points;
- a `requirements.txt` installation path;
- commands corresponding to major experiment groups;
- five-seed averaging in the paper experiments.

Reproducibility limitations visible in the inspected repository state:

- no container or Nix environment is documented in the README;
- the README does not state dataset artifact checksums;
- dataset construction is notebook-driven rather than a single immutable command manifest;
- exact model bytes and raw-result checksums are not supplied in the README;
- CPU/GPU peak RSS and wall-time contracts are not supplied;
- the paper uses five seeds, whereas this reconstruction requires at least three after experiment start.

Classification:

> **paper-specific official code and exact commit verified; experiment scripts and seed requirement documented; immutable R0 dataset/model/resource/checksum bundle not yet established**

No experiment was started in this cycle. Model size, peak RSS, wall time, CPU latency, and three-seed measurements are therefore not applicable yet.

## Required controls before any adoption

A future joint-identification experiment must include identical domain × seed × instance cells for at least:

1. strongest non-language unknown-target CRL/coarsening baseline;
2. language-only dynamics baseline from temporally ordered text;
3. state-only and trajectory-only baselines;
4. random and untrained language encoders;
5. token-form shuffle preserving target frequencies;
6. utterance-to-target permutation fixed per run;
7. environment-label and target-label shuffle;
8. outcome/reward shuffle;
9. parser/entity/schema/template metadata removal;
10. direct recovery of `Q`, `P`, and `d`, not only task success;
11. countermodel pairs with identical token causal law and identical non-language interventional law but different grounding;
12. an anchor ablation proving that the residual automorphism is nontrivial without the anchor and trivial with it.

## Updated decision for RQ-001

**NARROWED BEYOND TOKEN-LEVEL CAUSAL DISCOVERY AND LANGUAGE-DYNAMICS PRETRAINING — NOT ADOPTED**

The surviving candidate is:

> After identifying the strongest recoverable token-level causal law from temporally ordered language and the finest causal target partition recoverable from all legitimate non-language observational/interventional data, can a preregistered cross-system language law jointly identify a residual raw-utterance equivalence relation and residual intervention-target partition while eliminating every language/world/denotation recoding that preserves both marginal causal laws and all task behavior?

Adoption now requires at minimum:

1. an explicit separation of token-generation causality from world-intervention causality;
2. exact inventories of language, parser, entity, target, environment, schema, reward, outcome, and trajectory channels;
3. a strong language-only dynamics baseline and strongest non-language unknown-target baseline;
4. direct metrics for utterance partition, target partition, and denotation;
5. a concrete pair of observationally equivalent countermodels before training;
6. a cross-system anchor fixed before fitting and unavailable from supplied semantic labels;
7. proof of the residual automorphism group before and after the anchor;
8. exact-commit, dependency, split, seed, resource, and checksum manifests for any started baseline;
9. preregistration before architecture or mechanism changes.

## Status

- RQ-001: further narrowed; not adopted
- token-level causal discovery from temporal text: prior art under stated assumptions
- language-dynamics pretraining as semantic grounding: not justified
- paper-specific official code: verified
- exact official commit: pinned
- public baseline reproduction: not started
- raw-language equivalence identification: not established
- latent intervention-target partition identification by language: not established
- semantic joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
