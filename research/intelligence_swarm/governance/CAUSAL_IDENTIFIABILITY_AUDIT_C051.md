# Causal Identifiability Audit C051

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### BISCUIT: Causal Representation Learning from Binary Interactions

Phillip Lippe, Sara Magliacane, Sindy Löwe, Yuki M. Asano, Taco Cohen, and Efstratios Gavves. UAI 2023.

Primary records:

- PMLR: https://proceedings.mlr.press/v216/lippe23a.html
- OpenReview: https://openreview.net/forum?id=VS7Dn31xuB
- official project page: https://phlippe.github.io/BISCUIT/
- official code: https://github.com/phlippe/BISCUIT
- audited official commit: `e558c4c3815679d42798475bf8995d5ed02997fe`

BISCUIT studies interactive environments in which low-level actions may change unknown causal variables. It assumes that, for each causal variable, the effect of interaction can be represented by an unknown binary interaction indicator selecting between two mechanisms, such as observational versus interventional dynamics. It then learns both a causal representation and the binary interaction variables from video and action information.

This is directly relevant to RQ-001 because it already establishes that unknown interaction targets need not be supplied as labels: under structural conditions, the latent causal variables and their corresponding interaction indicators can be identified from interactive data. Therefore, learning latent intervention targets from low-level actions, discovering action-conditioned interaction masks, and using interaction patterns to disentangle causal variables are prior art.

BISCUIT does **not** receive raw language, infer an utterance equivalence relation, identify a denotation map, or prove that an interaction-equivalence class is the unique semantic target class.

## Assumption, observation, and guarantee comparison

Let:

- `C_t = (C_{1,t}, ..., C_{K,t})` be latent causal variables;
- `X_t = g(C_t)` be observed frames through an injective observation map in the identifiability model;
- `A_t` be observed low-level action information;
- `I_{i,t} in {0,1}` be the unknown binary interaction variable for causal variable `i`;
- `p_i(C_{i,t+1} | C_t, I_{i,t})` be the variable-specific transition mechanism;
- `h_i(A_t, C_t)` be the interaction predictor that determines `I_{i,t}`.

### Structural boundary

The useful identifiability signal is not the action label itself. It is the fact that each latent causal variable admits two distinguishable transition mechanisms and that the interaction pattern varies sufficiently across actions and states. The practical model learns a binary interaction map per latent causal variable and conditions a temporal latent prior on the previous state and the learned interaction indicators.

The paper and official project description make the following boundary explicit:

1. maximum likelihood alone admits multiple entangled representations;
2. low-level actions can reveal which latent mechanism changed even when the target identity is not provided;
3. an unknown binary interaction variable can supply the asymmetry needed to separate causal variables;
4. identification is tied to the causal variables and interaction mechanisms, not to externally grounded semantic names.

### What is guaranteed

Under the paper's structural assumptions, including distinguishable interaction-dependent mechanisms and sufficient interaction diversity, the observable interactive process can identify, up to the paper's allowed representation ambiguities:

- latent causal variables;
- their temporal relations;
- binary interaction indicators associated with those variables;
- which low-level actions can intervene on which recovered variables;
- action-conditioned affordance or interaction maps.

Thus, unknown-target interactive causal representation learning without target labels is established prior art.

### What is not guaranteed

The framework does not identify:

- which raw utterances are equivalent;
- whether two utterances selecting the same interaction map are synonyms or distinct meanings with aliased effects;
- a semantic partition finer than equality of all learned interaction and transition signatures;
- a denotation from utterance classes to latent variables;
- semantic identity of a recovered latent component beyond the allowed permutation or componentwise reparameterization;
- distinctions between two targets that induce identical binary interaction variables and identical transition laws under all available actions and states;
- elimination of joint recoding of utterance classes, latent variables, interaction indicators, and denotations.

BISCUIT identifies actionable causal structure. It does not identify a unique language ontology for that structure.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- identifying causal variables from interactive trajectories with unknown intervention targets;
- learning binary observational/interventional mechanism selectors without target labels;
- using low-level action or agent-state information to infer which latent variable was affected;
- learning action-conditioned affordance or interaction maps;
- disentangling causal variables by exploiting heterogeneous interaction mechanisms;
- replacing a supplied intervention-target label with a learned binary interaction indicator;
- using an autoencoder followed by a normalizing flow to recover interactive causal factors;
- claiming semantic grounding merely because an action-to-latent interaction map is recovered;
- claiming raw-language equivalence merely because utterances produce the same recovered interaction indicator.

The surviving novelty candidate must operate strictly beyond the strongest non-language partition induced by all observable action-conditioned interaction and transition signatures.

## Theorem/assumption boundary for RQ-001

Define:

- `Q`: an unknown equivalence relation over raw utterances;
- `P`: an unknown semantic intervention-target partition;
- `d: U_raw/Q -> P`: denotation;
- `Sigma(p)`: the complete non-language signature of target `p`, consisting of all binary interaction indicators, conditional transition laws, action-conditioned affordances, and state-dependent effects available under the preregistered interactive process;
- `P_Sigma`: the coarsest partition that separates targets whenever their complete signatures differ.

BISCUIT-style identifiability can recover causal variables and interaction mechanisms when `Sigma` is sufficiently separating. It does not imply that `P_Sigma = P`.

If two semantic targets have the same complete signature under every available action and state, no estimator using only frames, actions, learned interaction indicators, and transitions can determine whether they are one semantic target or two semantically distinct but interaction-aliased targets.

A necessary condition for language to refine the non-language partition is:

\[
I(P_{residual}; U_{raw} \mid X_{0:T}, A_{0:T}, I_{0:T}, \Sigma) > 0.
\]

This is not sufficient. Joint observations must also eliminate every transformation that changes `Q`, `P`, or `d` while preserving the complete interactive law.

## Identifiability counterexample: identical interaction law, different semantics

Assume unlimited data and oracle recovery of the complete BISCUIT-relevant latent process. Let two candidate semantic targets `p1` and `p2` satisfy, for every state and low-level action:

\[
I_{p1}(A_t,C_t) = I_{p2}(A_t,C_t)
\]

and

\[
p(C_{p1,t+1} \mid C_t, I_{p1,t}) = p(C_{p2,t+1} \mid C_t, I_{p2,t})
\]

after an allowed relabeling of their latent coordinates. Assume their full action-conditioned affordance maps and all downstream observable effects are also equal.

Construct Model A:

- `p1` and `p2` form one semantic target block `p`;
- raw forms `u1` and `u2` are synonyms in one utterance class;
- the class denotes `p`.

Construct Model B:

- `p1` and `p2` are distinct semantic target blocks;
- `u1` and `u2` belong to distinct utterance classes;
- each class denotes its corresponding target;
- both targets retain identical interaction and transition signatures under every available action and state.

Models A and B can preserve:

- the complete distribution of observed frames and actions;
- the recovered latent transition model;
- every learned binary interaction variable;
- every action-conditioned affordance map;
- temporal likelihood and reconstruction loss;
- triplet or intervention-generation outputs;
- next-state prediction;
- action accuracy and task success;
- language likelihood;
- language-shuffle gaps when both forms carry the same control information;
- every official BISCUIT representation and interaction metric.

Nevertheless, `Q_A != Q_B`, `P_A != P_B`, and the denotation maps differ. Therefore:

> Perfect recovery of causal variables and unknown binary interaction targets does not identify semantic distinctions inside an interaction-equivalence class, raw-language equivalence, or the denotation between language and latent targets.

Even when every interaction signature is distinct, a residual symmetry remains: simultaneously permuting latent-variable labels, interaction-indicator labels, utterance classes, and the denotation map preserves the observable law. A separately fixed cross-system anchor is required to assign semantic identity rather than an arbitrary component index.

## Consequence for interactive language grounding

BISCUIT sharpens the benchmark design requirement. Before attributing any target discovery to language, the benchmark must first compute or approximate the strongest target partition recoverable from non-language interaction data alone.

A valid test must therefore:

1. train or reproduce a language-blind interactive CRL baseline;
2. estimate the action/state-conditioned interaction-equivalence partition;
3. identify target pairs that remain aliased under all training interactions;
4. preregister held-out interventions that separate those pairs;
5. test whether raw language predicts the held-out separation without target IDs, parser slots, object names, answer leakage, or completed trajectories;
6. directly score recovery of utterance partition, residual target partition, and denotation;
7. compare against a countermodel with the same interaction law and a different semantic partition;
8. use an independently fixed anchor if semantic component identity, rather than recovery up to permutation, is claimed.

Task success, action prediction, interaction-map quality, or causal-variable disentanglement alone is insufficient.

## Official-code and reproducibility audit

The authors' project page links the paper-specific official repository `phlippe/BISCUIT`. The audited official head commit is:

`e558c4c3815679d42798475bf8995d5ed02997fe`

The repository contains:

- `models/` with BISCUIT implementations;
- `experiments/` with autoencoder, normalizing-flow, and VAE training entry points;
- `data_generation/` for iTHOR, CausalWorld, and Voronoi datasets;
- a demo notebook with a pretrained BISCUIT-NF model;
- `environment.yml`;
- documented dataset-generation and training commands;
- links to published datasets on Zenodo.

The README documents Python 3.8, PyTorch 1.13, PyTorch Lightning 1.9, and later-tested PyTorch 2.0.1 / Lightning 2.0.3 combinations. It provides paper-oriented commands for generating iTHOR, CausalWorld, and Voronoi data and for training the autoencoder, BISCUIT-NF, and BISCUIT-VAE variants.

Reproducibility limitations visible in the audited public state:

- `environment.yml` is not an immutable hash-locked dependency bundle;
- the CausalWorld generator may require a modified package that the README says must be requested from the authors;
- no container digest or Nix environment is documented;
- the README does not define a canonical three-seed replication manifest;
- no complete raw-result checksum bundle is documented;
- no peak RSS, model bytes, CPU latency, or wall-time acceptance contract is documented;
- the official tasks do not contain raw-language equivalence or denotation recovery;
- the full iTHOR/CausalWorld reproduction is substantially heavier than the lightweight R0.1 competence gate and is not yet preregistered for this branch.

Classification:

> **paper-specific official code and exact commit verified; datasets and training entry points are public; immutable dependency, complete generator, seed, resource, and checksum contract is not established**

No experiment was started in this cycle. Model size, peak RSS, wall time, CPU latency, and three-seed measurements are therefore not applicable yet.

## Decision

**NARROWED BEYOND UNKNOWN BINARY-INTERACTION TARGET IDENTIFIABILITY — NOT ADOPTED**

The broad claim that interactive trajectories can discover unknown intervention targets is rejected as a novelty candidate because BISCUIT already provides a relevant identifiability result and public implementation.

The surviving candidate is narrowed to:

> After recovering the strongest causal-variable and interaction-target partition identifiable from all legitimate non-language frames, actions, states, and transition mechanisms, can a preregistered raw-language observation law uniquely refine the remaining interaction-aliased blocks and jointly identify utterance equivalence, residual semantic target partition, and denotation, while eliminating every joint recoding that preserves the complete interactive process?

Adoption still requires a positive theorem or a preregistered separating experiment. Neither exists yet.
