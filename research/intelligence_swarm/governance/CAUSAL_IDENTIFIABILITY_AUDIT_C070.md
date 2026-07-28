# Causal Identifiability Audit C070

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the declared observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes prior-art-matrix refinement, theorem/assumption comparison, public-code availability audit, and an identifiability boundary/counterexample.
- Numerical reproduction is not started.

## Decision-relevant question

C069 separated an identifiable sequential predictive-state process from the still-unresolved semantic quotient over those states. The next admissible question was:

> Is aggregation of histories or predictive states into a minimal behaviorally sufficient quotient itself already covered by causal-state or bisimulation theory?

The answer is substantially yes when the intended target partition is defined by equality of all future controlled observation laws, or by reward-and-transition equivalence for all actions. In that case the quotient is a predictive/behavioral quotient, not an unconstrained semantic ontology.

## Primary prior art

Amy Zhang, Zachary C. Lipton, Luis Pineda, Kamyar Azizzadenesheli, Anima Anandkumar, Laurent Itti, Joelle Pineau, and Tommaso Furlanello, **“Learning Causal State Representations of Partially Observable Environments”**, RLDM 2019 oral / arXiv:1906.10437.

Primary records:

- arXiv: https://arxiv.org/abs/1906.10437
- author publication page: https://amyzhang.github.io/publications/

The paper defines causal states as the coarsest partition of action-observation histories that induce the same conditional distribution over future observations under future actions. It learns approximate representations from recurrent predictors and connects continuous causal-state representations to bisimulation under stated regularity conditions.

A related established line of work defines MDP bisimulation and bisimulation metrics by equality or closeness of immediate rewards and action-conditioned transition distributions over equivalence classes. These abstractions preserve control-relevant behavior and support value-function guarantees.

## Formal objects

Let a history be

`h_t = (o_1, a_1, ..., a_{t-1}, o_t)`.

For a future action sequence `a_{t:\infty}`, define the controlled future law

`P(O_{t+1:\infty} | h_t, a_{t:\infty})`.

Two histories are causal-state equivalent when these laws agree for every admissible future action sequence:

`h ~_cs h'`

iff

`P(O_future | h, do(A_future=a)) = P(O_future | h', do(A_future=a))`

for all admissible future action sequences `a`.

This relation directly addresses the concern left by C069: it specifies which predictive states should be merged. The causal-state quotient is the coarsest history partition retaining the complete controlled predictive law.

For a fully observed MDP, bisimulation similarly groups states when, for every action, rewards agree and transition probability into every equivalence class agrees. Thus a target partition defined entirely through all admissible action-conditioned consequences is a behavioral quotient already formalized by established state-abstraction theory.

## What is already covered

The following are not independently novel:

- merging histories that have the same complete future controlled observation law;
- learning a coarsest predictive state abstraction from histories;
- defining target equivalence by equality of reward and transition behavior for all actions;
- using bisimulation to remove task-irrelevant state distinctions;
- proving that a behavioral abstraction preserves value or supports optimal control;
- claiming that context-refined HMM states should be merged when they have identical controlled futures;
- treating an intervention target as identifiable only up to its complete observable response law.

Accordingly, if `P` in RQ-001 is defined as the partition induced by all admissible interventions and consequences, then much of the proposed “semantic quotient” is not an open language-grounding problem. It is a controlled predictive equivalence or bisimulation quotient.

## Important correction to C069

C069 stated that identifying a predictive process does not automatically identify which recovered states must be quotiented together semantically. That remains true for an unconstrained human or external ontology.

However, for the narrower operational definition

> two histories or latent targets have the same meaning exactly when every admissible controlled future law is the same,

the quotient is no longer unspecified. It is the causal-state or bisimulation quotient, and established theory supplies the target object.

Therefore the remaining uncertainty must not be described generically as “semantic quotient identification.” It must specify a distinction not already exhausted by complete behavioral equivalence.

## Theorem/assumption comparison

| Setting | Equivalence object | Main guarantee | Residual issue for RQ-001 |
|---|---|---|---|
| Finite nonparametric HMM | latent Markov states | transition/emission model up to state permutation under rank/separation | state may over-refine controlled predictive equivalence |
| Causal states in a controlled partially observed process | histories with identical future controlled observation laws | coarsest complete predictive partition; approximate learned representation and control guarantees under assumptions | does not assign external names or distinctions beyond observable controlled futures |
| MDP bisimulation | states with equal reward and class-transition laws for each action | behavior/value-preserving state abstraction | task/reward dependent unless full consequence family is used |
| RQ-001 external semantics | raw-language class, latent target partition, and denotation | desired joint identification | must justify any distinctions finer than complete controlled behavior and any external orientation |

## Identifiability boundary 1: behavioral semantics is already a quotient of the controlled process

Suppose the semantic target partition is declared to be exactly:

`p ~ p'` iff every admissible intervention sequence produces the same distribution over every future sensor, action opportunity, reward, and outcome.

Then `P` is the maximal controlled behavioral quotient. Under access to the complete controlled process law, this quotient is defined without language.

Raw language may label or help estimate the quotient, but it does not create a new target ontology. A claim that language “discovers” this partition must be compared against a language-blind causal-state/bisimulation baseline.

## Identifiability boundary 2: distinctions finer than bisimulation are observationally unsupported

Consider two proposed targets `p_1` and `p_2` such that, under every admissible policy and intervention sequence, they induce exactly the same joint law over all future observations, rewards, costs, and action availability.

Model A uses one target class and treats utterances `u_1` and `u_2` as synonyms.

Model B uses two distinct semantic target classes and assigns one utterance to each, while duplicating the complete controlled process law.

No adaptive experiment using the declared interface can distinguish the models. Their complete policy-indexed transcript laws are identical.

Thus:

> A semantic ontology strictly finer than the complete causal-state/bisimulation quotient is not identifiable from that interaction interface.

Calling the duplicated classes different meanings requires an additional independently observable consequence, an external convention, or explicit supervision.

## Identifiability boundary 3: external orientation remains unresolved

Even if the causal-state quotient is perfectly recovered and language classes are relatively coupled to its blocks, a simultaneous permutation of:

- quotient-state labels;
- utterance-class labels;
- denotation entries;
- actuator/sensor bookkeeping and evaluation labels;

preserves the complete controlled process whenever the physical interface is recoded consistently.

Therefore causal-state/bisimulation theory identifies relative behavioral classes, not external names, units, directions, or human-conventional meanings.

Examples not supplied by the quotient alone include:

- which recovered dimension is physically called temperature;
- whether an orientation is clockwise or counter-clockwise;
- whether two behaviorally identical artifacts are conventionally different object kinds;
- whether a numeric coordinate is measured in one unit or another.

## Identifiability boundary 4: reward-bisimulation can under-partition language meaning

A reward-specific bisimulation may merge states that require the same optimal behavior for one task but differ in other physical consequences or other tasks.

Therefore a benchmark success metric or task reward cannot define the desired target ontology unless the RQ explicitly declares task-relative meaning.

To make a stronger environment-level claim, the quotient must use a preregistered, sufficiently rich family of sensors, interventions, costs, and held-out consequences rather than only the training reward.

## Consequence for interactive grounding

Adaptive clarification is useful only when a question induces a controlled future law that separates candidate blocks. If two candidates are already bisimilar under the enlarged query/action set, more dialogue cannot distinguish them.

This yields a concrete protocol requirement:

1. define the admissible intervention and clarification action family before learning;
2. define the full observed consequence vector, excluding semantic labels and evaluator leakage;
3. compute or approximate the language-blind controlled behavioral quotient;
4. evaluate whether language recovers the same quotient or a justified coarser partition;
5. reject any finer semantic partition unless a preregistered held-out consequence separates it;
6. evaluate external orientation separately from relative class coupling.

## Prior-art matrix refinement

C070 replaces the broad category “semantic quotient” with three distinct targets:

1. **controlled predictive quotient**: equality of all future controlled observation laws; covered by causal-state theory;
2. **task-relative behavioral quotient**: reward-and-transition equivalence for a declared task family; covered by bisimulation/state-abstraction theory;
3. **extra-behavioral semantic ontology and external orientation**: distinctions or labels not determined by the declared controlled process; not identifiable without additional independent observations or conventions.

This separation prevents an existing behavioral abstraction from being renamed as a new language-grounding principle.

## Public-code availability audit

The primary causal-state paper is publicly available and the author publication page identifies it as an RLDM 2019 oral. The inspected primary records do not provide a paper-specific official code link. A repository-title search for the exact paper title did not identify an author-managed implementation.

Classification:

> Primary paper and algorithm description are public; no paper-specific official immutable implementation was identified in this run.

No unofficial reimplementation or numerical experiment is started. A reproduction would require prior baseline selection and a preregistration that directly measures recovery of the controlled behavioral quotient, raw-language partition, target partition, and relative coupling.

## Decision

**NARROWED BEYOND CAUSAL-STATE AND BISIMULATION QUOTIENT IDENTIFICATION — NOT ADOPTED.**

The candidate RQ is narrowed to:

> After recovering the language-blind causal-state or bisimulation quotient induced by a preregistered complete family of interventions and consequences, can raw language identify a different quotient or denotation that is both observationally justified and not merely task-reward equivalence? Any claim finer than complete controlled behavioral equivalence must name an independently observed symmetry-breaking consequence; external semantic orientation must be evaluated separately from relative coupling.

## Decision progress

C070 materially narrows the remaining problem rather than repeating a generic relabeling argument.

1. Predictive-state aggregation under complete controlled futures is established prior art through causal states.
2. Reward/transition-preserving aggregation is established prior art through bisimulation and state abstraction.
3. The phrase “semantic quotient” is no longer admissible without specifying whether it means a controlled behavioral quotient, a task-relative quotient, or an extra-behavioral convention.
4. A semantic partition finer than the complete declared controlled process is non-identifiable unless an additional independent consequence is observed.
5. The next admissible experimental step is a preregistered language-blind causal-state/bisimulation baseline with direct partition metrics, not a new architecture.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code availability audit: completed.
- Identifiability boundary/counterexample: completed.
- Controlled causal-state quotient: established prior art.
- Task-relative bisimulation quotient: established prior art.
- Generic predictive-state-to-behavioral-quotient gap: substantially closed under the complete controlled-law definition.
- Extra-behavioral semantic ontology: not identifiable from the same interface without an additional independent observation or convention.
- External semantic orientation: not established.
- RQ-001: narrowed and not adopted.
- Public baseline reproduction: not started in this run.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
