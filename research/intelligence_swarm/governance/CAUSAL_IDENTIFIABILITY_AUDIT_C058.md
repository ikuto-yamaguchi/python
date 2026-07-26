# Causal Identifiability Audit C058

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + public-code availability audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Disentangling Dynamical Systems: Causal Representation Learning Meets Local Sparse Attention

Markus W. Baumgartner, Anson Lei, Joe Watson, and Ingmar Posner. Proceedings of the Fifth Conference on Causal Learning and Reasoning, PMLR 323, 2026.

Primary records:

- PMLR: https://proceedings.mlr.press/v323/baumgartner26a.html
- arXiv: https://arxiv.org/abs/2603.14483
- author publication page: https://joemwatson.github.io/

This work is directly relevant to the non-language half of RQ-001. It studies whether fixed but unknown dynamical-system parameters can be recovered from raw trajectories when their causal influence on system components is sparse and possibly state dependent.

## RQ variables

Let:

- `U` be raw utterances or linguistic descriptions;
- `X_0:T` be raw system trajectories;
- `A_0:T-1` be optional actions or controls;
- `Theta` be fixed latent system parameters;
- `G_x(theta)` be the state-dependent local causal influence graph from parameter coordinates to system components;
- `Q` be the unknown raw-language equivalence relation;
- `P` be the unknown partition of latent intervention targets or parameter coordinates;
- `d: U/Q -> P` be the denotation map required by RQ-001.

## Observations and supervision in the audited setting

The learner receives trajectory collections from systems whose latent parameters are constant within a trajectory but vary across trajectories. The practical model encodes an observed trajectory into latent parameter coordinates and decodes one-step system dynamics while regularizing parameter-to-state influence to be sparse.

The language variables `U`, raw-language equivalence `Q`, denotation `d`, and interactive linguistic feedback are not part of the theorem or benchmark.

## Assumptions relevant to identifiability

The paper's guarantee depends on structural conditions of the dynamical system, including:

1. trajectories contain enough information to distinguish the latent system parameters;
2. parameters are fixed over the trajectory segment used for inference;
3. the decoder captures the system's one-step dynamics sufficiently well;
4. causal influence from parameter coordinates to system components is sparse;
5. the relevant parameter-to-component influence graph satisfies a graphical separation criterion;
6. local state-dependent influence patterns may be richer than the global union graph;
7. the learned latent dimension and parameterization are compatible with the true parameter family;
8. the residual ambiguity is limited to permutation and componentwise diffeomorphism under the stated criterion.

These conditions concern identification of dynamical parameters from trajectories. They do not supply a semantic codebook or identify which raw expression denotes which parameter.

## Guarantee actually established

The paper establishes a graphical identifiability criterion for disentangling system parameters from raw trajectories. Under its assumptions, parameter coordinates can be recovered up to permutation and diffeomorphism. It further shows that relying only on the global causal graph can give a weaker lower bound than exploiting local state-dependent causal structure.

The empirical method uses a sparsity-regularized transformer and variational inference on four synthetic dynamical domains to recover disentangled parameter representations.

The work does not establish:

- recovery of raw-language equivalence classes;
- recovery of a language-to-parameter denotation map;
- elimination of parameter-coordinate permutations by language;
- identification of semantic target refinements inside dynamically equivalent parameter classes;
- separation of linguistic supervision from simulator, parameter, or benchmark metadata;
- joint identification of `Q`, `P`, and `d`.

## Prior-art boundary added to the matrix

The following claims are excluded from the novelty space:

- recovering latent dynamical-system parameters from raw trajectories by exploiting sparse causal influence;
- using local state-dependent causal graphs to strengthen parameter disentanglement;
- deriving a graphical criterion for parameter identifiability;
- identifying parameters up to permutation and diffeomorphism without a predefined library of physical equations;
- using a sparsity-regularized attention model for system-parameter inference;
- interpreting successful trajectory-based parameter disentanglement as a new language-grounding principle;
- claiming that language is required merely because system parameters are unnamed.

Thus the non-language target partition may already be recoverable more finely than global-dynamics or reward-only approaches suggest. RQ-001 must be defined only over the residual ambiguity after the strongest local causal criterion is applied.

## Theorem comparison with the surviving RQ

The audited theorem answers a question of the form:

> When do raw trajectories determine latent system-parameter coordinates, modulo permutation and diffeomorphism?

RQ-001 asks the stronger joint question:

> When do raw trajectories and raw language jointly determine the utterance equivalence relation, the intervention-target partition, and their denotation map?

Even full parameter disentanglement leaves two distinct ambiguities relevant to RQ-001:

1. **coordinate orientation ambiguity** — the recovered parameter coordinates remain permutable and reparameterizable;
2. **cross-system semantic ambiguity** — a language class can be reassigned to another recovered parameter coordinate if the language interface and downstream bookkeeping are recoded consistently.

The local causal graph can eliminate mixtures of parameter coordinates that violate sparsity, but it does not name the surviving coordinates or select an external semantic interpretation.

## Identifiability counterexample A: perfect local causal disentanglement with different denotation

Assume an oracle recovers:

- the complete trajectory law;
- every local state-dependent parameter-to-component influence graph;
- the true parameter coordinates up to permutation and componentwise diffeomorphism;
- perfect one-step and long-horizon prediction.

Let `sigma` be a non-identity permutation of recovered parameter coordinates. Construct a second model by simultaneously transforming:

- parameter coordinates by `sigma`;
- parameter labels and intervention-target blocks;
- raw-language classes;
- the denotation map;
- the language encoder output coordinates;
- any target-indexed policy, decoder, logging, and evaluation interface.

The transformed model preserves:

- every raw trajectory distribution;
- every local and global causal influence graph up to relabeling;
- every sparsity score;
- every one-step and rollout prediction;
- every disentanglement metric that is permutation invariant;
- every action, reward, and task-success distribution;
- every language-conditioned result evaluated through the consistently recoded interface.

Nevertheless the external assignment from an utterance class to a physical parameter differs.

Therefore:

> Local causal parameter identifiability up to permutation and diffeomorphism does not identify the cross-system denotation map.

## Identifiability counterexample B: locally indistinguishable parameter refinement

Let two candidate semantic targets `p1` and `p2` have identical effects on all observed system components at every reachable state and under every admissible action:

`p(X_next | X, A, p1) = p(X_next | X, A, p2)`.

Assume they also induce the same local influence graph everywhere reachable.

Construct Model A:

- utterances `u1` and `u2` are synonyms;
- both denote one dynamical target block.

Construct Model B:

- `u1` and `u2` have distinct meanings;
- they denote distinct targets `p1` and `p2`;
- the targets are dynamically and locally causally indistinguishable in the complete observed regime.

Both models preserve:

- all trajectories and controls;
- all local and global influence graphs;
- all prediction losses;
- all learned parameter posteriors;
- all sparsity objectives;
- all downstream policies and outcomes;
- all language likelihoods compatible with the same utterance corpus.

Yet `Q_A != Q_B` and `P_A != P_B`.

Thus even local state-dependent causal structure cannot identify semantic distinctions that never produce an observable local contrast.

## Identifiability counterexample C: diffeomorphic recoding and linguistic predicates

Suppose a scalar physical parameter `theta` is identifiable only up to an invertible transformation `h(theta)`. A language corpus may contain predicates such as "larger", "smaller", "twice", or threshold descriptions. Without an externally fixed measurement law, units, order orientation, or calibrated intervention, a transformed language interpretation can be paired with `h` while preserving trajectory prediction and text likelihood.

A componentwise diffeomorphism is therefore not always semantically harmless. It can change metric, threshold, and comparative meanings while preserving the dynamical identifiability guarantee.

Consequently, RQ-001 must distinguish:

- coordinate recovery modulo diffeomorphism;
- ordinal or metric grounding of linguistic predicates;
- naming or denotation of parameter coordinates.

## Consequence for interactive language grounding

Interaction can remove residual ambiguity only if it introduces an observation whose distribution is not invariant under the candidate permutation or diffeomorphism. Merely collecting more trajectories from the same reachable state-action regime cannot separate `p1` and `p2` in Counterexample B.

A potentially informative interaction must be preregistered as a symmetry-breaking probe, for example:

- a controlled intervention whose physical actuator identity is fixed independently of language;
- a calibrated measurement with externally fixed units and orientation;
- a query whose answer is scored against a non-linguistic sensor contrast not derived from the benchmark target ID;
- a held-out state region where candidate parameters have different local influence patterns.

These are possible anchors, not a demonstrated new architecture or a proven sufficient condition for the full RQ.

## Mandatory controls introduced by C058

Before RQ adoption, the baseline and preregistration must include:

1. recovery of the finest parameter partition supported by local state-dependent causal influence;
2. comparison against the partition supported only by the global union graph;
3. explicit reporting of residual permutation and diffeomorphism groups;
4. a language-blind local-causal system-identification baseline;
5. a trajectory-blind language baseline;
6. parameter-coordinate permutation controls;
7. monotone and non-monotone componentwise reparameterization controls where allowed;
8. simultaneous utterance/parameter/interface recoding controls;
9. held-out states designed to separate globally aliased but locally distinct parameters;
10. direct evaluation of `Q`, `P`, and `d` rather than only prediction or control;
11. separate tests for nominal, ordinal, metric, and threshold language;
12. disclosure of simulator parameter names, units, actuator IDs, sensors, and metadata leakage;
13. proof that each proposed interaction removes a specified element of the residual automorphism group;
14. failure cases where no reachable interaction breaks the symmetry.

## Public-code availability audit

The PMLR record, arXiv record, and inspected author publication page expose the paper and publication metadata. No paper-specific public repository or code link was located in those primary records during C058. Public search results likewise did not establish an author-maintained implementation repository.

Classification:

> Primary paper and theorem are publicly available; a paper-specific official public implementation was not confirmed in C058.

No unofficial reimplementation was started. A public baseline reproduction cannot be claimed without a confirmed implementation or a separately preregistered faithful reimplementation protocol.

## Decision

**NARROWED BEYOND LOCALLY IDENTIFIABLE DYNAMICAL-SYSTEM PARAMETERS — NOT ADOPTED**

Reason:

- trajectory-based system-parameter identification using local sparse causal structure is established prior art;
- the theorem recovers parameters only up to permutation and componentwise diffeomorphism;
- those ambiguities are directly relevant to nominal, comparative, threshold, and metric language;
- locally indistinguishable parameters permit different semantic refinements with the same complete observed law;
- a simultaneous utterance/parameter/interface recoding preserves trajectory, prediction, and task metrics;
- no external cross-system anchor or theorem for joint recovery of `Q`, `P`, and `d` is supplied.

## Surviving candidate after C058

> After recovering the finest dynamical-parameter partition identifiable from all reachable local state-dependent causal influence graphs, and after separately recovering the finest raw-language equivalence supported by legitimate language dynamics, determine whether preregistered cross-system interventions with independently fixed actuator, sensor, order, or metric orientation eliminate every residual parameter permutation and diffeomorphism and thereby jointly identify `Q`, the residual target partition `P`, and denotation `d` without semantic-label leakage.

## Adoption gate after C058

RQ-001 remains not adopted. Adoption requires at least:

1. a formal observation model including language, trajectories, controls, local influence graphs, and allowed interventions;
2. computation of the residual automorphism group after the strongest non-language local-causal identification result;
3. explicit separation of nominal denotation from ordinal and metric predicate grounding;
4. a theorem showing that the preregistered anchor family reduces the residual group to the permitted trivial equivalence;
5. a countermodel pair when each anchor assumption is removed;
6. a confirmed public baseline or preregistered faithful reproduction before architecture changes;
7. direct partition and denotation metrics;
8. immutable commands, dependencies, assets, checksums, and three seeds when experiments begin;
9. model size, peak RSS, wall time, and inference time when experiments begin.

## Status

- RQ-001: further narrowed, not adopted
- local sparse causal system-parameter identifiability: established prior art
- raw-language equivalence recovery: not established here
- joint target-partition and denotation recovery: not established
- official public code: not confirmed
- public baseline reproduction: not started
- experiment: not started
- model size / RSS / time / three seeds: not yet applicable
- new architecture: none
- old A–E toy mechanism: none
- novelty claim: none
- intelligence-principle claim: none
- capability-progress claim: none
