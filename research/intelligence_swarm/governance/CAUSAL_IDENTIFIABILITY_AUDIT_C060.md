# Causal Identifiability Audit C060

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the available observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes: (a) prior-art refinement, (b) assumption/observation/guarantee comparison, and (d) an identifiability counterexample. It also audits public-code availability, but does not begin a numerical reproduction.

## Primary work audited

Liangru Xiang, Yuxi Ma, Zhihao Cao, Yixin Zhu, and Song-Chun Zhu, **“Grounding Before Generalizing: How AI Differs from Humans in Causal Transfer,”** Proceedings of the Annual Meeting of the Cognitive Science Society, 2026; arXiv:2604.24062.

Primary sources:

- Paper: https://arxiv.org/abs/2604.24062
- Author publication page: https://yzhu.io/publication/openlock2026cogsci/
- Project page: https://causal-openlock.github.io/

The paper adapts OpenLock to test interactive causal discovery and transfer in current LLMs/VLMs. Each environment has seven levers and a door. The active subsystem instantiates either a Common Cause (CC) or Common Effect (CE) topology. Surface labels, colors, and positions vary across environments while the abstract topology is preserved. Models receive up to 30 three-action attempts to find three solutions. The text-only interface supplies the current lever states, complete action/outcome history, explicit state-change feedback, explicit solution-found notifications, and the number of remaining solutions. The transfer condition additionally supplies all three action sequences from a previous environment with the same topology.

The empirical guarantee is deliberately limited: the work measures discovery efficiency and transfer behavior; it does not give an identifiability theorem for meanings, latent target partitions, or denotations. The reported central result is that models can perform strong within-environment causal discovery, especially through symbolic text, but generally do not show the immediate structure-transfer benefit observed in humans. Gains tend to appear only after environment-specific mapping has begun.

## Prior-art matrix refinement

| Candidate contribution | Status after C060 | Reason |
|---|---|---|
| Interactive discovery of a latent causal topology from action/outcome feedback | Existing | OpenLock directly evaluates sequential discovery of hidden CC/CE structure. |
| Transfer of an abstract causal schema across surface-remapped environments | Existing evaluation problem | The transfer condition changes labels, colors, and positions while preserving topology. |
| Measuring whether grounding is needed before causal transfer | Existing empirical finding | The paper explicitly distinguishes immediate structural transfer from post-hoc environment-specific mapping. |
| Using raw/symbolic language histories to support causal exploration | Existing | The text interface includes symbolic state, history, and explicit outcome descriptions. |
| Showing that text can outperform image or text-plus-image in interactive causal discovery | Existing empirical result | The paper reports degradation from visual input for most tested models. |
| Inferring raw-language equivalence classes jointly with latent intervention-target partitions | Not established by the paper | Surface symbols and action interfaces are already indexed; equivalence and denotation are not latent evaluation targets. |
| Proving uniqueness of the language-to-target mapping | Not established | No theorem excludes joint relabeling of symbols, levers, actions, and environment interface. |

Accordingly, “interactive causal learning,” “environmental grounding before transfer,” “symbolic-language-assisted active discovery,” and “cross-environment topology transfer” cannot be used alone as novelty claims for RQ-001.

## Assumption / observation / guarantee comparison

### OpenLock 2026

**Supplied or fixed**

- A fixed action grammar that addresses lever/interface elements.
- A known interaction protocol: two lever actions followed by a door attempt.
- Explicit action-success and state-change messages in the text condition.
- Explicit notification that a solution was found.
- Explicit count of remaining solutions.
- In the transfer condition, exact successful action sequences from a previous environment.
- A benchmark generator in which the researcher knows which surface elements instantiate the active topology.

**Observed**

- Surface descriptions or rendered images.
- Chosen actions.
- State transitions and null-change outcomes.
- Solution acknowledgements and trial history.

**Evaluated**

- Whether all three solutions are found within 30 attempts.
- Number of attempts.
- Marginal discovery cost.
- Improvement relative to a no-transfer baseline.
- Differences across CC/CE and modalities.

**Not guaranteed or directly evaluated**

- Recovery of a raw-expression equivalence relation `Q`.
- Recovery of an unknown semantic intervention-target partition `P`.
- Recovery of a denotation map `d: Q -> P`.
- Exclusion of simultaneous recoding of surface tokens, action names, target identities, and the environment interface.
- Identification of semantics beyond task- and interface-equivalence.

### RQ-001

RQ-001 is stronger. It requires that the observations determine, up to a declared harmless equivalence:

1. which raw utterances are semantically equivalent;
2. which latent intervention targets form the same semantic block; and
3. which utterance block denotes which target block.

OpenLock tests whether a model can exploit or reconstruct a causal topology behind an already addressable interface. It does not identify the interface’s semantic codebook from unindexed raw language.

## Interface supervision and leakage boundary

The text-only condition is not semantically supervision-free. It includes high-value signals such as explicit state changes, success notifications, and the remaining-solution count. These are legitimate observations for the paper’s behavioral question, but for RQ-001 they must be classified before use:

- If lever names and action arguments are generated from simulator object identities, the target index is supplied through the interface.
- If “solution found” and remaining-solution counts are used to infer the utterance partition, outcome supervision may substitute for semantic discovery.
- If previous solutions are provided as exact action sequences in the transfer prompt, the prior environment’s action codebook is supplied, even though the new surface mapping remains to be discovered.
- If evaluation compares against simulator-known lever roles or topology labels, those labels may be used for scoring but must not enter training, probing, prompt generation, or representation selection.

Therefore, OpenLock can be a useful interactive testbed only after separating physically observable feedback from simulator-semantic bookkeeping.

## Identifiability counterexample 1: complete OpenLock success with different denotation

Let an environment contain addressable surface tokens `S`, actions `A`, hidden active components `V`, transition law `T`, solution predicate `R`, and a raw-language partition `Q` with denotation `d: Q -> V`.

Choose a non-trivial permutation `pi` of the active component identities. Construct a second model by simultaneously transforming:

- active component identities `v -> pi(v)`;
- surface-token assignment;
- action arguments and action parser;
- transition and solution interfaces;
- raw-language classes;
- denotation `d' = pi o d`;
- logging and evaluation bookkeeping.

For every adaptive policy, couple the two worlds so that each action/history transcript is mapped through `pi`. Then the following are unchanged:

- all text and image distributions after interface recoding;
- all action-conditioned state-change and null-change messages;
- solution-found notifications;
- number of remaining solutions;
- success probability;
- attempt counts and marginal discovery cost;
- CC/CE topology up to graph isomorphism;
- transfer improvement;
- language-conditioned policy value.

Nevertheless, a given raw-language class denotes a different external component. Thus even perfect discovery, perfect transfer, and perfect task success do not uniquely identify `d` when the complete interface may be jointly recoded.

## Identifiability counterexample 2: topology transfer does not determine semantic partition

Consider two raw expressions `u1` and `u2` that always trigger or describe the same addressable action in every reachable history. Let two candidate latent targets `p1` and `p2` have identical transition, reward, feedback, and solution consequences under every allowed probe.

Two ontologies are observationally equivalent:

- Model A: `u1` and `u2` are synonyms and denote one semantic target.
- Model B: `u1` and `u2` have different meanings and denote two distinct but intervention-aliased targets.

Both models induce the same OpenLock transcript distribution, discovery curve, transfer curve, and success rate. Hence neither more episodes nor better causal-schema transfer can decide whether the expressions or targets should be merged. The benchmark identifies at most the quotient induced by its available interaction law.

## Identifiability counterexample 3: adaptive probing cannot break an equivariant interface

Let `G` be a non-trivial group acting jointly on utterance classes, target identities, action names, surface labels, and responses. Suppose the initial observation law, allowable query set, response law, and query cost are equivariant under `G`.

For any adaptive strategy, the transformed world produces the transformed transcript with the same probability and cost. This follows inductively: if histories are paired under an element of `G`, the strategy’s next query can be paired, and equivariance pairs the next response. Therefore adaptivity alone does not remove the ambiguity.

A successful symmetry-breaking probe must rely on an element not transformed by `G`, such as an independently calibrated actuator, sensor axis, physical unit, or human response whose identity is fixed outside the learned/simulator semantic codebook.

## Consequence for the candidate RQ

The OpenLock result strengthens the negative boundary:

> Strong interactive causal discovery and even cross-environment structural transfer do not imply joint identification of raw-language equivalence, latent semantic target partition, or denotation when the symbolic/action interface is indexed or jointly recodable.

The residual positive question is no longer whether interaction helps. It is which externally fixed, non-leaking interaction law reduces the residual automorphism group after the strongest language-only and non-language causal quotients have already been recovered.

## Public-code availability audit

The author publication page declares a `Code` link to `https://github.com/caozh20/CausalLLM` and a dataset download. At C060 audit time:

- the declared GitHub repository returned `404 Not Found` through both the public web route and the connected GitHub repository search;
- no accessible author repository with that exact owner/name was found;
- the author page and project page remain available;
- the dataset link is declared, but no immutable checksum or repository commit was established in this run.

Classification:

> Paper, project page, and declared code/dataset links are public; an accessible paper-specific immutable code commit was not confirmed. Public numerical reproduction is therefore not started in C060.

A non-official reimplementation is prohibited before baseline selection and preregistration.

## Decision

**NARROWED BEYOND INTERACTIVE CAUSAL DISCOVERY AND ENVIRONMENT-GROUNDED STRUCTURE TRANSFER — NOT ADOPTED**

The surviving candidate is:

> After recovering the finest raw-language quotient identifiable from language dynamics, the finest intervention-target quotient identifiable from non-language interactions, and the strongest transferable causal topology identifiable from OpenLock-style adaptive transcripts, can a preregistered set of independently indexed probes reduce the residual joint automorphism group to the declared harmless equivalence and thereby identify `Q`, residual `P`, and `d` without parser, simulator-label, success-counter, or target-codebook leakage?

## Required next evidence before adoption

1. Write the residual automorphism group explicitly for the selected benchmark.
2. Separate physical observations from simulator-generated semantic bookkeeping.
3. Define which actuator/sensor identities are fixed independently of language and target labels.
4. Construct matched countermodel pairs with identical topology and task success but different `Q`, `P`, or `d`.
5. Preregister direct recovery metrics for `Q`, `P`, and `d`; success rate and attempt count are insufficient.
6. Include utterance, target, interface, and joint-permutation controls.
7. Reproduce a competent public baseline before adding an architecture.
8. Once numerical experiments begin, record model bytes, peak RSS, wall time, and three fixed seeds.

## Status after C060

- RQ-001: further narrowed; not adopted.
- Interactive causal discovery: existing empirical benchmark.
- Environment-grounded causal transfer: existing empirical finding.
- Joint raw-language/target identification: not established.
- Paper-specific accessible immutable code commit: not confirmed.
- Public baseline reproduction in this run: not started.
- New architecture: none.
- Legacy A–E toy mechanisms: unchanged.
- Experiment started: no.
- Model size / RSS / runtime / three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: none.
- Capability progress: not recognized.
