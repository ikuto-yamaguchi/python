# Causal Identifiability Audit C063

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the available observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes: (a) prior-art matrix refinement, (b) theorem/assumption/observation/guarantee comparison, and (d) an identifiability counterexample. It also audits official public code; numerical reproduction is not started.

## Primary work audited

Burak Varici, Emre Acarturk, Karthikeyan Shanmugam, and Ali Tajer, **“Linear Causal Representation Learning from Unknown Multi-node Interventions,”** NeurIPS 2024.

Primary sources:

- Paper: https://papers.nips.cc/paper_files/paper/2024/hash/ca70528fb11dc8086c6a623da9f3fee6-Abstract-Conference.html
- arXiv: https://arxiv.org/abs/2406.05937
- Official code: https://github.com/acarturk-e/umni-crl

The paper studies interventional causal representation learning when each environment may intervene on an unknown subset of latent nodes. The latent causal model may be parametric or nonparametric, the observation is a linear mixing of latent variables, and intervention targets are not supplied. Under sufficient diversity of environments, the results distinguish two regimes:

- with soft interventions, recovery is possible up to an ancestor-related ambiguity;
- with hard interventions, perfect latent-variable and intervention-target identification is possible within the paper's declared equivalence.

The constructive algorithms use score differences between environments. This work therefore closes a major part of the non-language problem: unknown multi-node targets do not by themselves require language supervision when the linear-mixing, intervention-diversity, and score assumptions hold.

## Prior-art matrix refinement

| Candidate contribution | Status after C063 | Reason |
|---|---|---|
| Recovering causal representations from environments with unknown multi-node interventions | Existing | UMNI-CRL directly addresses unknown subsets of intervened latent nodes. |
| Identifying unknown intervention targets under hard multi-node interventions | Existing under assumptions | The hard-intervention result gives perfect identification in the stated linear-mixing setting. |
| Recovering useful causal information under unknown soft multi-node interventions | Existing under assumptions | The soft-intervention result identifies up to an ancestor-related ambiguity. |
| Using score differences across environments to construct a CRL algorithm | Existing | This is a central constructive step of UMNI-CRL. |
| Reducing environment count through diverse multi-node intervention patterns | Existing theoretical direction | The guarantee relies on sufficiently diverse intervention environments rather than one known atomic intervention per node. |
| Claiming language is necessary merely because intervention targets are unknown and multi-node | Excluded | UMNI-CRL supplies a non-language identification route under explicit assumptions. |
| Jointly identifying raw-language equivalence, a semantic target partition, and denotation | Not established | The paper identifies causal coordinates and environment target sets, not a raw-language ontology or external denotation. |
| Eliminating simultaneous recoding of latent coordinates, target sets, utterance classes, and world interfaces | Not established | The theorem's causal identification does not fix an external semantic naming law. |

Accordingly, “unknown multi-node intervention discovery,” “score-based recovery of target sets,” and “hard-intervention perfect CRL identification” cannot alone support novelty for RQ-001.

## Assumption / observation / guarantee comparison

### UMNI-CRL

**Supplied or fixed**

- A fixed latent dimension and a latent structural causal model.
- An observation model that is a linear transformation of the latent variables.
- Multiple environments, each produced by an intervention on an unknown subset of latent nodes.
- Sufficient diversity or coverage of intervention changes across environments.
- Regularity needed to define and estimate score functions and their differences.
- For the strongest result, hard-intervention structure satisfying the paper's assumptions.

**Observed**

- Samples from each environment.
- Environment identity, so samples can be grouped by distributional regime.
- Distributional or score changes induced by interventions.

**Guaranteed under the theorem assumptions**

- Under soft interventions, recovery of causal information up to the paper's ancestor-level ambiguity.
- Under hard interventions, perfect recovery of latent causal representations and unknown intervention targets within the theorem's equivalence.
- Constructive achievability through score-based algorithms.

**Not guaranteed or directly evaluated**

- Recovery of a raw-utterance equivalence relation `Q`.
- Recovery of a semantic partition that may split or merge intervention-identical latent targets beyond the causal variables recovered by the theorem.
- Recovery of a denotation map `d: Q -> P`.
- Identification of names, units, orientation, or ordinary-language predicates for recovered coordinates.
- Elimination of a joint permutation of coordinates, environment target sets, utterance classes, and target-indexed interfaces.
- Distinguishing synonyms from different meanings that happen to have the same complete interventional law.

### RQ-001

RQ-001 is strictly stronger. It asks whether observations determine all three objects:

1. the equivalence relation `Q` over raw utterances;
2. the semantic intervention-target partition `P`;
3. the denotation `d: Q -> P`.

UMNI-CRL may recover the non-language causal coordinates and the subset targeted in each environment. It does not establish which raw expressions should be grouped, which semantic distinctions should be imposed inside an interventionally aliased block, or which expression block denotes which recovered coordinate or target subset.

## Environment-label and target-interface leakage boundary

For an RQ-001 experiment, the following must be treated as supplied supervision or potential leakage if used to connect language to UMNI-CRL outputs:

- environment names containing the intervened object or variable;
- simulator target masks exposed to the learner;
- parser outputs containing latent-coordinate indices;
- intervention commands whose arguments are gold target IDs;
- filenames, directory structure, or metadata encoding target subsets;
- reward or success labels produced from a known target codebook;
- causal-coordinate matching performed using ground-truth permutation alignment and then reused for language supervision;
- pretrained embeddings trained on the same target names;
- score estimators conditioned on semantic labels rather than only environment membership.

Environment identity is legitimate for estimating separate distributions. Semantic content embedded in that identity is not.

## Identifiability counterexample 1: perfect hard-intervention recovery with a different denotation

Let `Z = (Z1, ..., Zd)` be latent causal coordinates, `E` the environment index, `T(E)` the unknown multi-node intervention target set, `X = AZ` the observed linear mixture, `Q` raw-utterance classes, `P` semantic target blocks, and `d: Q -> P` the denotation.

Assume an oracle UMNI-CRL learner perfectly recovers:

- the latent coordinates;
- the causal graph or the causal information guaranteed by the theorem;
- every target set `T(E)`;
- every environment distribution.

Choose a non-trivial permutation `pi` of latent coordinates. Construct a second system by simultaneously replacing:

- `Z` with `Z' = pi(Z)`;
- every target set with `T'(E) = pi(T(E))`;
- the mixing matrix with the corresponding recoded matrix;
- semantic target blocks with `P' = pi(P)`;
- raw-language classes and denotation with a corresponding recoding;
- target-indexed action, sensor, reward, policy, decoder, logging, and evaluation interfaces.

The two systems can preserve:

- every environment-indexed observational distribution;
- every score and score difference;
- every recovered target-set pattern;
- the hard-intervention identification objective;
- causal-representation recovery metrics after admissible permutation alignment;
- next-state prediction, action accuracy, reward, and task success through the recoded interface;
- raw-language likelihood and a recoded language-conditioned policy.

Nevertheless, the same surface utterance class can denote a different external target block. Therefore:

> Perfect identification of unknown hard multi-node intervention targets does not by itself identify raw-language equivalence or external denotation.

This is not a failure of UMNI-CRL. It is a mismatch between internal causal-coordinate identification and cross-system semantic identification.

## Identifiability counterexample 2: interventionally identical coordinates admit semantic merge/split alternatives

Suppose two candidate target variables or blocks `p1` and `p2` have identical laws under every available environment and every admissible intervention family. In particular, replacing either one produces the same distribution over all measured trajectories, outcomes, rewards, and future intervention responses.

Model A declares:

- `p1` and `p2` to be one semantic target block;
- utterances `u1` and `u2` to be synonyms in one class.

Model B declares:

- `p1` and `p2` to be two distinct semantic target blocks;
- `u1` and `u2` to have distinct meanings;
- all available causal and behavioral laws to remain identical.

Both models agree on all data UMNI-CRL can use, including all environment distributions and score differences, but they disagree on `Q` and `P`.

Therefore:

> Even a method that perfectly recovers every identifiable unknown multi-node target can recover only the quotient induced by the available intervention family; semantic distinctions inside an interventionally identical block are not data-identified.

## Identifiability counterexample 3: hard-versus-soft guarantees do not orient language semantics

Hard interventions may improve causal-coordinate identification from ancestor-level ambiguity to perfect recovery. This removes an internal causal ambiguity, but it does not orient words such as:

- increase versus decrease;
- parent versus child in ordinary-language reference;
- first versus second recovered coordinate;
- object names, units, colors, or roles;
- a phrase denoting one coordinate versus a multi-node set.

If language classes, coordinate identities, and the target-indexed actuator/sensor interface are recoded together, the stronger hard-intervention theorem remains true in both systems. Hence stronger causal recovery is necessary evidence for grounding experiments, but it is not sufficient semantic evidence.

## Official public-code audit

Official repository:

- `acarturk-e/umni-crl`
- audited commit: `7ed4755b13c1679aff29968fe5916e7bc3a61de4`

The README identifies the repository as the code for the NeurIPS 2024 UMNI-CRL paper, requires the public `causaldag` package, and directs users to run `umni_crl_test.py` to reproduce Section 5 experiments. It also states that the most recent implementation is maintained in `acarturk-e/score-based-crl`.

Confirmed:

- paper-specific public repository;
- exact commit pin;
- a named Section 5 reproduction entry point;
- declared external dependency on `causaldag`;
- pointer to the later score-based CRL codebase.

Not yet established:

- hash-locked dependencies;
- an immutable container;
- dataset or generated-data checksum;
- canonical three-seed manifest;
- raw-result checksum;
- model bytes;
- peak RSS;
- wall-clock time;
- CPU inference latency;
- direct evaluation of `Q`, `P`, and `d`;
- an RQ-001 countermodel benchmark.

Classification:

> Paper-specific official code and an exact commit are confirmed, but a hermetic baseline-reproduction bundle and semantic-identification evaluation are not established.

Numerical reproduction is not started in C063. Consequently, model size, peak RSS, runtime, and three-seed reporting are not yet applicable.

## Decision

**NARROWED BEYOND UNKNOWN MULTI-NODE INTERVENTION CRL — NOT ADOPTED**

The surviving candidate is:

> After recovering the finest causal-coordinate and unknown multi-node intervention-target quotient identifiable from legitimate environment-indexed data, and separately recovering the finest raw-language quotient supported by language dynamics, can preregistered cross-system probes whose actuator, sensor, orientation, unit, and response identities are fixed independently of both codebooks eliminate the residual joint automorphism and identify `Q`, residual `P`, and `d` without environment-name, target-mask, parser, reward, or evaluator leakage?

Before adoption, at minimum:

1. map the benchmark observations to the UMNI-CRL linear-mixing, soft/hard-intervention, and intervention-diversity assumptions;
2. compute the finest non-language target quotient before adding language;
3. separate legitimate environment identity from semantic target metadata;
4. preregister language-blind UMNI-CRL and language-only baselines;
5. construct paired countermodels preserving all environment distributions while changing `Q`, `P`, or `d`;
6. directly evaluate utterance partition, target partition, and denotation rather than task success alone;
7. define independently calibrated probes that are not generated from simulator target names or parser slots;
8. prove which residual automorphisms those probes eliminate;
9. reproduce the selected public baseline with exact dependencies, checksums, three seeds, model size, RSS, and runtime before introducing any architecture.

## Status

- RQ-001: further narrowed; not adopted.
- Unknown multi-node intervention CRL: existing under explicit assumptions.
- Perfect hard-intervention target recovery: existing under explicit assumptions.
- Soft-intervention ancestor-level recovery: existing under explicit assumptions.
- Raw-language equivalence: not identified by this work.
- Joint semantic target partition and denotation: not established.
- Official code: confirmed.
- Exact commit: pinned.
- Public baseline reproduction: not started.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
