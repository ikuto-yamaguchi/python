# Causal Identifiability Audit C052

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### General Identifiability and Achievability for Causal Representation Learning

Burak Varici, Emre Acartürk, Karthikeyan Shanmugam, and Ali Tajer. AISTATS 2024.

Primary records:

- PMLR: https://proceedings.mlr.press/v238/varici24a.html
- paper PDF: https://proceedings.mlr.press/v238/varici24a/varici24a.pdf
- paper-linked official code: https://github.com/bvarici/score-general-id-CRL
- audited official commit: `61abbec02ced47198ad7da2866266cd5ff609ae8`
- README-designated newer implementation: https://github.com/acarturk-e/score-based-crl

This paper studies causal representation learning under a general nonparametric latent causal model and a general nonlinear observation transformation. Its main result addresses a stronger unknown-target setting than merely hiding the node label: the learner receives two hard intervention environments per latent node but is not told either which node each environment targets or which two environments target the same node. The environments are therefore uncoupled.

The paper proves that observational data plus these uncoupled interventions suffice, under interventional-discrepancy and regularity assumptions, to recover the latent DAG exactly and the latent variables up to permutation and element-wise diffeomorphisms. It also gives the constructive GSCALE-I recovery procedure based on score variations across environments.

This is directly relevant to RQ-001. Unknown intervention-environment pairing, unknown target identity, general nonlinear mixing, and constructive latent/DAG recovery are established prior art. Raw language is not required for those guarantees.

The paper does **not** receive raw utterances, infer a raw-language equivalence relation, identify a denotation map, or assign externally fixed semantic identities to the recovered latent coordinates.

## Assumption, observation, and guarantee comparison

Let:

- `Z = (Z1, ..., Zn)` be latent causal variables governed by DAG `G`;
- `X = g(Z)` be observed data;
- `g` be an unknown diffeomorphism onto its image;
- `E0` be the observational environment;
- `Ei` and `E~i` be two hard intervention environments for latent node `i`;
- the learner observe two unordered environment collections without knowing their target nodes or cross-collection pairing;
- `pi`, `qi`, and `q~i` denote the observational and two interventional mechanisms for node `i`.

### Structural assumptions

The main uncoupled-environment result relies on:

1. a continuously differentiable, invertible observation transformation onto its image;
2. a general nonparametric latent SCM with positive, sufficiently differentiable densities;
3. two stochastic hard interventions per latent node;
4. interventional discrepancy between each relevant pair of observational/interventional mechanisms;
5. observational samples in addition to the interventional environments;
6. enough information to estimate environment-specific score functions in the population argument;
7. modular interventions that replace only the targeted node mechanism.

The learner does not know:

- the intervention target of an environment;
- which two intervention environments target the same node;
- the latent DAG;
- the latent coordinates;
- the observation transformation.

### Theorem boundary

Theorem 1 states that observational data and two uncoupled hard intervention environments per node, with the required interventional discrepancy, suffice to:

- perfectly recover the latent DAG;
- perfectly recover the latent variables in the paper's identifiability sense;
- achieve those guarantees constructively through Algorithm 1 / GSCALE-I.

The latent-variable guarantee is not an externally named semantic recovery. It is recovery up to a permutation and component-wise invertible transformations:

\[
\hat Z(X) = P_{\pi}\,\phi(Z),
\]

where `P_pi` is a coordinate permutation and `phi` acts element-wise.

### What is guaranteed

Under the theorem assumptions, the observable multi-environment law can determine:

- the correct pairing of the two otherwise uncoupled intervention collections;
- which environments correspond to the same recovered latent coordinate;
- the latent causal variables up to permutation and element-wise diffeomorphism;
- the latent DAG exactly modulo the recovered coordinate correspondence;
- an encoder achieving the stated recovery guarantee;
- the intervention-environment structure needed by GSCALE-I.

Therefore, the following are not available novelty claims for RQ-001:

- identifying latent variables under unknown intervention targets;
- recovering the target pairing of uncoupled intervention environments;
- using score differences across environments to invert a general nonlinear observation map;
- recovering a latent DAG and variables without intervention labels;
- replacing target metadata with environment-distribution asymmetry;
- claiming that language is required merely because intervention-target labels are absent.

### What is not guaranteed

The theorem does not identify:

- which raw utterances are semantically equivalent;
- whether two utterances associated with the same recovered coordinate are synonyms or distinct descriptions with aliased effects;
- a semantic partition finer than the complete family of available intervention distributions;
- a denotation from utterance classes to externally fixed target meanings;
- the externally intended identity of a latent coordinate rather than its location up to permutation;
- distinctions between target meanings that induce identical observational and interventional laws;
- elimination of joint permutations of latent coordinates, environment pairs, utterance classes, and denotation;
- a unique ontology beyond the intervention-separating partition supplied by the environment family.

The result identifies causal coordinates. It does not identify a unique language ontology over those coordinates.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- general nonlinear CRL from hard interventions with unknown target labels;
- latent-variable and DAG recovery when intervention environments are uncoupled;
- discovering which two environments intervene on the same latent variable;
- score-variation-based recovery of an inverse nonlinear observation map;
- exact latent DAG recovery from observational plus uncoupled intervention data;
- removing faithfulness requirements by including observational data in this setting;
- interpreting unknown environment pairing as an unsolved semantic-grounding problem;
- claiming raw-language grounding merely because a language-conditioned policy predicts the recovered intervention pair.

The surviving novelty candidate must operate strictly beyond the finest partition induced by all legitimate observational and uncoupled interventional distributions.

## Theorem/assumption boundary for RQ-001

Define:

- `Q`: an unknown equivalence relation over raw utterances;
- `P`: an unknown semantic intervention-target partition;
- `d: U_raw/Q -> P`: denotation;
- `Lambda(p)`: the complete family of observational and intervention-induced distributions attributable to target `p` under the preregistered environments;
- `P_Lambda`: the partition separating targets exactly when their complete distributional signatures differ.

The AISTATS 2024 result can recover latent coordinates and correctly couple intervention environments when the intervention family provides the required discrepancy. It does not establish that `P_Lambda = P`, nor that the recovered coordinate label has an externally fixed denotation.

A necessary condition for raw language to refine the strongest non-language partition is:

\[
I(P_{residual}; U_{raw} \mid X, E, \Lambda) > 0.
\]

This is not sufficient. The joint law must additionally eliminate every automorphism that changes `Q`, `P`, or `d` while preserving all observational, interventional, language, and behavioral distributions.

## Identifiability counterexample: perfect uncoupled recovery, different semantic ontology

Assume unlimited data and oracle execution of GSCALE-I. Suppose the complete latent DAG, latent coordinates, and correct pairing of every uncoupled intervention environment are recovered in the theorem's allowed sense.

### Countermodel pair A: residual coordinate relabeling

Construct Model A with:

- latent coordinates `Z1, ..., Zn`;
- semantic target blocks `p1, ..., pn`;
- utterance classes `q1, ..., qn`;
- denotation `d(qi) = pi`.

For any non-identity permutation `sigma`, construct Model B by simultaneously applying `sigma` to:

- latent coordinates;
- DAG node labels;
- the paired intervention environments;
- semantic target blocks;
- utterance classes;
- denotation;
- language encoder outputs;
- policy and decoder inputs.

Models A and B preserve:

- the observational distribution;
- every interventional distribution;
- every environment-specific score function;
- all score-difference sparsity patterns;
- the inferred uncoupled-environment pairing;
- GSCALE-I's objective and recovered DAG;
- latent recovery up to the theorem's permutation allowance;
- next-state prediction;
- action accuracy and task success;
- utterance likelihood;
- language-shuffle gaps.

Yet the externally asserted correspondence between raw language and named semantic targets differs. Thus perfect uncoupled-environment recovery does not remove the exact joint permutation that matters for denotation.

### Countermodel pair B: intervention-aliased semantic refinement

Let two candidate meanings `p1` and `p2` induce exactly the same complete observational and hard-intervention distributions under every available environment, after an allowed component-wise reparameterization.

Construct Model A:

- `p1` and `p2` are one semantic target block;
- raw forms `u1` and `u2` are synonyms in one utterance class.

Construct Model B:

- `p1` and `p2` are distinct semantic target blocks;
- `u1` and `u2` are distinct utterance classes;
- the two targets remain distributionally indistinguishable under the entire observed intervention family.

Both models can preserve:

- all observational and intervention samples;
- the number and pairing of environment distributions;
- all score functions and score differences;
- interventional-discrepancy conditions for the recoverable coordinates;
- the recovered latent DAG and variables;
- reconstruction and latent-recovery metrics;
- all downstream behavioral metrics.

Nevertheless, `Q_A != Q_B`, `P_A != P_B`, and the denotation maps differ.

Therefore:

> Perfect latent and DAG recovery under unknown, uncoupled intervention targets identifies the intervention-separating causal coordinates, but it does not identify semantic refinements inside intervention-equivalent classes or a unique denotation from raw language to those coordinates.

## Consequence for interactive language grounding

Before language receives credit for discovering a target partition, the benchmark must first instantiate the strongest non-language baseline allowed by all observational and intervention-environment information.

A valid separating test must:

1. reproduce or faithfully instantiate a language-blind unknown-target CRL baseline;
2. hide both target labels and intervention-environment pairing from the learner;
3. compute the finest partition recoverable from complete environment-distribution signatures;
4. enumerate target pairs still aliased after non-language recovery;
5. preregister raw-language observations or interactions that could separate those pairs;
6. exclude parser slots, object IDs, environment templates, answer labels, completed trajectories, and target-derived embeddings;
7. directly score `Q`, residual `P`, and `d`, rather than only latent correlation or task success;
8. include joint coordinate/environment/utterance permutation controls;
9. compare against a countermodel with the same complete intervention law and a different semantic ontology;
10. specify an external, independently fixed anchor if absolute semantic identity is claimed.

Additional interaction samples from the same intervention family do not resolve an alias that is exact at the population level. A new intervention family can refine `P_Lambda`, but that refinement is attributable to new non-language information unless the language channel supplies a separately testable cross-system constraint.

## Official-code and reproducibility audit

PMLR links the paper-specific official repository `bvarici/score-general-id-CRL`. The audited official head commit is:

`61abbec02ced47198ad7da2866266cd5ff609ae8`

The repository contains a compact simulation implementation:

- `main.py` for the GSCALE-I simulation;
- `analyze.py` for evaluation metrics;
- `quadratic_sem.py` for the synthetic latent SCM;
- `utils.py` for supporting functions;
- a README stating `torch >= 2.0`;
- experiment parameters edited directly in the scripts.

The official README states that the repository reproduces simulations for the transform `X = tanh(T.Z)` and directs readers to the newer `acarturk-e/score-based-crl` repository for the most recent code.

Reproducibility limitations of the paper-specific snapshot:

- no immutable dependency lock or hash-pinned environment;
- no container digest;
- no canonical command manifest covering every paper table and figure;
- experiment hyperparameters are changed in source variables rather than a versioned configuration bundle;
- no dataset/checkpoint checksum package;
- no canonical three-seed protocol;
- no raw-result archive with hashes;
- no model-byte, peak-RSS, wall-time, or CPU-latency contract;
- the synthetic implementation does not contain raw language, interactive denotation recovery, or utterance-partition evaluation.

Classification:

> **paper-specific official code and exact commit verified; constructive synthetic implementation is public; immutable environment, canonical seed/resource/checksum bundle, and language-grounding task are absent**

No experiment was started in this cycle. Model size, peak RSS, wall time, CPU latency, and three-seed measurements are therefore not applicable yet.

## Decision

**NARROWED BEYOND GENERAL UNCOUPLED-INTERVENTION CRL IDENTIFIABILITY — NOT ADOPTED**

The broad claim that latent causal variables, their DAG, or unknown intervention-environment pairing can be discovered without target labels is rejected as a novelty candidate because Varici et al. already prove and constructively address that setting under explicit assumptions.

The surviving candidate is narrowed to:

> After recovering the latent DAG, latent coordinates, and strongest intervention-target partition identifiable from all legitimate observational and uncoupled interventional environments, can a preregistered raw-language law uniquely refine only the remaining intervention-aliased blocks and jointly identify utterance equivalence, residual semantic target partition, and denotation, while eliminating every joint coordinate/environment/utterance recoding that preserves the complete multi-environment law?

Adoption still requires a positive theorem or a preregistered separating experiment after baseline reproduction. Neither exists yet.
