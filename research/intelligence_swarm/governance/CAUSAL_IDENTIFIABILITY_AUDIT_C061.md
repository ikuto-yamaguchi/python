# Causal Identifiability Audit C061

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the available observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes: (a) prior-art matrix refinement, (b) assumption/observation/guarantee comparison, and (d) an identifiability counterexample. It also audits official public code, but does not begin a numerical reproduction.

## Primary work audited

Julia Kiseleva et al., **“Interactive Grounded Language Understanding in a Collaborative Environment: IGLU 2021,”** Proceedings of the NeurIPS 2021 Competitions and Demonstrations Track, PMLR 176, 2022.

Primary sources:

- Paper: https://proceedings.mlr.press/v176/kiseleva22a.html
- Paper PDF: https://proceedings.mlr.press/v176/kiseleva22a/kiseleva22a.pdf
- Official environment: https://github.com/iglu-contest/iglu
- PyPI package: https://pypi.org/project/iglu/

IGLU studies collaborative construction in Minecraft. A human or dataset supplies natural-language instructions describing a target structure, and an embodied agent must manipulate blocks to realize that structure. The challenge decomposes the broader problem into language understanding, clarification/dialogue, and sequential control components, with automatic and human-in-the-loop evaluation.

The work establishes a benchmark and empirical task family. It does not provide an identifiability theorem for raw-language equivalence, latent intervention-target partitions, or denotation.

## Prior-art matrix refinement

| Candidate contribution | Status after C061 | Reason |
|---|---|---|
| Interactive grounding of natural-language instructions in an embodied construction task | Existing | IGLU directly evaluates instruction-following in a collaborative Minecraft environment. |
| Learning language-conditioned block placement and sequential control | Existing | The benchmark requires agents to convert instructions into construction actions. |
| Clarification or dialogue for resolving instruction uncertainty | Existing benchmark direction | IGLU explicitly motivates collaborative and human-in-the-loop interaction. |
| Generalization across natural-language descriptions and structures | Existing evaluation problem | Train/test examples vary in language and target construction. |
| Human-in-the-loop evaluation of grounded agents | Existing | It is a central competition design goal. |
| Inferring raw-language equivalence jointly with an unknown latent intervention-target partition | Not established | Block types, coordinates, action schema, and target structures are already externally represented and scored. |
| Proving uniqueness of the utterance-to-target denotation | Not established | No theorem excludes joint recoding of instructions, block identities, coordinates, actions, and evaluator bookkeeping. |

Accordingly, “interactive instruction grounding,” “collaborative embodied construction,” “clarification,” “language-conditioned control,” and “human evaluation” cannot be used alone as novelty claims for RQ-001.

## Assumption / observation / guarantee comparison

### IGLU 2021

**Supplied or fixed**

- A Minecraft-derived world with a fixed block/action interface.
- A bounded construction zone and coordinate system.
- An inventory and block-type vocabulary represented by the environment.
- A fixed action grammar for movement, camera control, selection, placement, and removal.
- Target structures represented in an evaluator-readable coordinate/block format.
- Dataset or human instructions paired with construction episodes or target structures.
- Automatic metrics that compare a built structure with the reference structure.

**Observed by the agent, depending on track**

- Natural-language instruction or dialogue history.
- Egocentric visual/world observation.
- Inventory and agent state.
- Previous actions and their visible consequences.
- Potential clarification responses from a human collaborator.

**Empirical guarantee/evaluation**

- Construction quality or similarity to a reference structure.
- Language-understanding benchmark performance.
- Sequential control performance.
- Human judgment in collaborative evaluation.

**Not guaranteed or directly evaluated**

- Recovery of a raw-expression equivalence relation `Q`.
- Recovery of an unknown semantic intervention-target partition `P`.
- Recovery of a denotation map `d: Q -> P`.
- Identification of which block/coordinate distinctions are semantic rather than evaluator-imposed.
- Exclusion of simultaneous recoding of language, block IDs, coordinates, actions, target structures, and scoring interface.

### RQ-001

RQ-001 is stronger. It requires observations to determine, up to an explicitly declared harmless equivalence:

1. which raw utterances are semantically equivalent;
2. which latent intervention targets form the same semantic block; and
3. which utterance block denotes which target block.

IGLU evaluates whether a model can act successfully through an already indexed construction interface. It does not ask the learner to identify the ontology or semantic codebook of that interface.

## Interface supervision and leakage boundary

For RQ-001, the following IGLU resources must be classified as supplied supervision rather than discovered semantics:

- block-type IDs and inventory slots;
- absolute or relative coordinate axes;
- action names and argument ordering;
- reference-structure files;
- simulator object IDs;
- evaluator-side block correspondence;
- canonical orientation conventions;
- task metadata generated from the target structure;
- dialogue responses produced using the hidden reference structure.

These are legitimate benchmark resources. However, if they are used to claim discovery of `P` or `d`, the central target partition or codebook has already been supplied.

A clarification answer is not automatically an independent semantic anchor. If the human or simulator answers using the same target file, object IDs, coordinate convention, or evaluator ontology, the response may reveal the existing codebook rather than identify semantics from an independently fixed law.

## Identifiability counterexample 1: perfect IGLU construction with a different denotation

Let the benchmark contain raw instruction classes `Q`, block/position target atoms `V`, action space `A`, transition law `T`, reference structures `R`, evaluator `E`, and denotation `d: Q -> V*`.

Choose a non-trivial bijection `pi` over block identities and/or spatial axes. Construct a second benchmark model by simultaneously transforming:

- block identities and inventory slots;
- coordinate axes or orientation;
- action arguments;
- renderer and transition interface;
- reference-structure encoding;
- evaluator bookkeeping;
- raw-language classes;
- denotation, with `d' = pi o d`;
- policy and decoder interfaces.

For every instruction and adaptive interaction history, couple the two worlds through `pi`. Then the following are unchanged:

- rendered observation distribution after interface recoding;
- action-success and transition law;
- reference-match score;
- exact-match or overlap metrics;
- dialogue success;
- human-visible construction after the corresponding renderer recoding;
- policy value and completion rate.

Nevertheless, a given raw-language class denotes a different external block, direction, or position. Therefore perfect construction and perfect human-rated collaboration do not uniquely identify `d` when the complete environment/evaluator interface may be jointly recoded.

## Identifiability counterexample 2: construction-equivalent expressions need not be synonyms

Consider two utterances `u1` and `u2` that induce the same optimal construction under every reachable benchmark context. Consider two candidate semantic targets `p1` and `p2` that differ outside the benchmark ontology but have identical block-placement, dialogue, visual, and score consequences inside IGLU.

Two models are observationally equivalent:

- Model A: `u1` and `u2` are synonyms and denote one target block.
- Model B: `u1` and `u2` have different meanings and denote distinct but construction-aliased target blocks.

Both models induce the same instruction distribution, action trajectories, clarification transcripts, final structures, and evaluation scores. Therefore IGLU identifies at most the quotient induced by its construction and dialogue interface; it cannot decide whether expressions or targets inside one quotient cell should be merged.

## Identifiability counterexample 3: adaptive clarification cannot break a codebook-equivariant dialogue

Let a group `G` act jointly on utterance classes, block/coordinate identities, action names, hidden reference structures, and clarification answers. Suppose:

- the allowed clarification questions are mapped into one another by `G`;
- the answer law is equivariant under `G`;
- query cost is invariant under `G`;
- the world transition and evaluator are equivariant under `G`.

For any adaptive dialogue policy, a transformed world produces a transformed transcript with the same probability, cost, and construction score. The claim follows inductively over dialogue turns. Adaptivity alone therefore does not eliminate the ambiguity.

A symmetry-breaking clarification must depend on an independently fixed resource not transformed by `G`, for example a calibrated physical direction, independently identified actuator, fixed measurement unit, or human reference whose identity and response law were not generated from the benchmark target codebook.

## Consequence for the candidate RQ

The IGLU benchmark strengthens the boundary:

> Strong collaborative instruction following, adaptive clarification, and exact embodied construction establish functional grounding relative to an indexed environment, but do not establish joint identification of raw-language equivalence, a latent intervention-target partition, or denotation.

The surviving positive question is not whether interaction or clarification helps. It is whether independently indexed probes or responses can remove the residual automorphism after the strongest language-only quotient and construction/intervention quotient have already been recovered.

## Official public-code audit

The official organization repository is:

- Repository: `iglu-contest/iglu`
- Audited commit: `8e84f0b73fb68df4766991aa406a5a653db6710c`

The repository README states that the environment is no longer supported for the competition and directs IGLU 2022 users to the GridWorld environment. It provides:

- a public Python environment;
- Java 8 and Xvfb setup instructions;
- Python 3.7 environment instructions;
- source installation and an environment test command;
- Docker documentation;
- access to the Minecraft Dialogue Corpus through environment configuration.

PyPI provides `iglu==0.2.2`, released 2021-07-03, with published package hashes. The source distribution SHA256 is `d6a2c80b9673113066ef73e42c5e6b825d1c348d38508a84940026ee7ee17c77` and the wheel SHA256 is `2f63f79dbefb78ac866ae29933569b1da4cc20060bf12f7ccdab565b14f9872f`.

Reproducibility limitations:

- the README contains an outdated clone path (`iglu_env`) while the current repository is `iglu`;
- the environment is explicitly deprecated for later competitions;
- Java/Minecraft dependencies are not captured by one immutable container digest;
- no canonical paper-wide three-seed manifest is supplied;
- no raw-result checksum bundle is supplied;
- model bytes, peak RSS, wall time, and CPU latency are not reported as a reproduction contract;
- no direct `Q`, `P`, or `d` recovery evaluation exists.

Classification:

> Official environment, exact commit, PyPI release, and package hashes are public. A hermetic R0 reproduction and semantic-identification evaluation are not established. Numerical reproduction is not started in C061.

## Decision

**NARROWED BEYOND INDEXED COLLABORATIVE CONSTRUCTION GROUNDING — NOT ADOPTED**

The surviving candidate is:

> After recovering the finest raw-language quotient identifiable from language dynamics and the finest construction/intervention-target quotient identifiable from non-language IGLU-style interaction, can a preregistered set of independently indexed clarification probes reduce the residual joint automorphism group to the declared harmless equivalence and thereby identify `Q`, residual `P`, and `d` without block-ID, coordinate, reference-structure, evaluator, parser, or dialogue-codebook leakage?

## Required next evidence before adoption

1. Separate physical observations from simulator/evaluator semantic bookkeeping.
2. Write the residual automorphism group for block identity, axes, action arguments, utterances, reference structures, and evaluator.
3. Define clarification probes whose identity and answer law are fixed independently of the target codebook.
4. Construct matched countermodel pairs with identical construction/dialogue success but different `Q`, `P`, or `d`.
5. Preregister direct metrics for utterance partition, residual target partition, and denotation.
6. Include utterance, block, axis, reference-structure, interface, and joint-permutation controls.
7. Reproduce a competent public baseline before adding any architecture.
8. Once experiments begin, record model bytes, peak RSS, wall time, and three fixed seeds.

## Status after C061

- RQ-001: further narrowed; not adopted.
- Collaborative embodied instruction grounding: existing benchmark.
- Adaptive clarification: existing benchmark direction.
- Functional construction success: insufficient for semantic identification.
- Official public environment: confirmed.
- Exact official commit: confirmed.
- PyPI package hashes: confirmed.
- Public baseline reproduction in this run: not started.
- New architecture: none.
- Legacy A–E toy mechanisms: unchanged.
- Experiment started: no.
- Model size / RSS / runtime / three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: none.
- Capability progress: not recognized.
