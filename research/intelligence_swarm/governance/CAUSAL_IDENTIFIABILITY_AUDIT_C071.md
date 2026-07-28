# Causal Identifiability Audit C071

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the declared observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes prior-art-matrix refinement and theorem/assumption comparison, and converts the C070 decision gate into a preregistered public-baseline program.
- Numerical execution is not started.

## Decision-relevant question

C070 established that a target ontology defined by complete controlled behavior is a causal-state or bisimulation quotient already covered by prior theory. It also required the next admissible step to be a language-blind quotient baseline with direct partition metrics.

C071 asks:

> What exact baseline, observations, metrics, controls, resource contract, and rejection rules are required before language can be credited with identifying anything beyond a controlled behavioral quotient?

The answer is recorded in `benchmarks/grounded_causal/PREREGISTERED_LANGUAGE_BLIND_QUOTIENT_BASELINE_LBQ001.md`.

## Primary prior art and guarantee boundary

### Causal-state representation

Zhang et al., *Learning Causal State Representations of Partially Observable Environments* (RLDM 2019 / arXiv:1906.10437), treat causal states as the coarsest partition of action-observation histories that preserves future controlled observation laws. Their learned approximation uses recurrent future prediction and connects continuous representations to bisimulation under stated assumptions.

Guarantee relevant to RQ-001:

- the operational target object is a controlled predictive quotient;
- the quotient is language-blind in definition;
- external names, units, directions, and conventional ontology are outside the guarantee.

### Bisimulation metrics

Ferns, Panangaden, and Precup, *Metrics for Finite Markov Decision Processes* (UAI 2004 / arXiv:1207.4114), define quantitative state-similarity metrics based on MDP bisimulation and relate them to optimal-value differences.

Guarantee relevant to RQ-001:

- reward-and-transition behavior supports a task-relative quotient and value guarantees;
- a reward-only quotient can be strictly coarser than an environment-level consequence quotient;
- task success is not a direct metric of raw-language equivalence or target-partition recovery.

### DeepMDP

Gelada et al., *DeepMDP: Learning Continuous Latent Space Models for Representation Learning* (ICML 2019), train latent models using reward and transition prediction losses and provide theoretical links between these losses, the environment model, and representation quality.

Guarantee relevant to RQ-001:

- practical continuous approximations of bisimulation-related structure are established prior art;
- representation or control gains do not establish recovery of `Q`, `P`, or denotation `d`;
- a faithful baseline can be selected without introducing a new architecture.

## Prior-art matrix refinement

| Object or claim | Existing coverage | Required C071 treatment |
|---|---|---|
| Coarsest partition preserving complete controlled futures | causal-state theory | language-blind target object |
| Reward/transition-preserving task quotient | bisimulation/state abstraction | explicit reward-only control |
| Continuous learned latent approximation | DeepMDP and related work | public/fidelity baseline candidate |
| Task success or value preservation | established downstream guarantee | secondary metric only |
| Raw-language partition `Q` | not provided by the above baselines | evaluate separately later |
| Relative language-target coupling `d` | not provided by a language-blind baseline | compare only after `P_LBQ` qualification |
| External semantic orientation | not provided | remain separate and unclaimed |

## Theorem/assumption comparison

| Baseline family | Observed variables | Core assumption or target definition | Guarantee | Failure mode relevant to RQ-001 |
|---|---|---|---|---|
| Causal states | action-observation histories and future actions | equality of complete controlled future laws | coarsest predictive history quotient | does not determine external semantic orientation |
| MDP bisimulation | state, action, reward, transition | equal reward and class-transition laws for every action | behavior/value-preserving quotient | task reward may under-partition physical distinctions |
| Bisimulation metrics | same as above, quantitatively | discounted metric fixed point / continuity conditions | state-similarity and value bounds | metric quality is not direct semantic partition recovery |
| DeepMDP | high-dimensional observations, action, reward, next observation | learnable latent reward and transition models | representation/model quality bounds under losses | success can coexist with incorrect block count or ontology |
| LBQ001 | preregistered non-semantic observation, action, cost, sensor and consequence family | direct recovery of quotient induced by declared controlled law | empirical baseline qualification only | cannot justify partitions finer than held-out controlled consequences |

## New decision progress: baseline semantics is fixed before execution

Earlier audits repeatedly observed that task success, prediction accuracy, latent similarity, or attention alignment can be high while `Q`, `P`, or `d` remain wrong. C071 closes that methodological ambiguity for the next experiment.

LBQ001 requires direct reporting of:

- adjusted Rand index;
- adjusted mutual information;
- pairwise same-block precision, recall, and F1;
- variation of information;
- block-count error;
- within-block and between-block held-out consequence discrepancies.

Task reward, success, value, and next-state prediction remain secondary. They cannot substitute for partition recovery.

## New decision progress: full-consequence and reward-only quotients are separated

C070 distinguished complete controlled behavior from task-relative behavior. C071 makes the distinction executable:

- B3 uses reward and transition only and is an explicit task-relative control;
- B4 uses the preregistered full non-semantic consequence family and is the principal language-blind comparator.

If B3 merges blocks that a held-out physical consequence separates, this is expected task-relative under-partitioning, not baseline failure. If B4 also merges them, either the estimator fails or the declared consequence family does not identify the proposed distinction.

## New decision progress: leakage contract is made falsifiable

LBQ001 forbids language or target-codebook information from the training view, including:

- utterance text and language embeddings;
- parser output and semantic slots;
- target names, masks, simulator variable names, entity roles;
- semantic reward, target-derived evaluator, reference structures;
- completed-trajectory labels revealing the target;
- pretrained embeddings trained on the same target names.

A semantic-leakage positive control deliberately exposes gold target identity, but it is marked as inadmissible evidence and used only to verify the metric ceiling.

This separates a functioning pipeline from a valid identification result.

## New decision progress: identifiability controls are preregistered

The following controls must be present when execution begins:

1. action shuffle;
2. consequence-channel shuffle;
3. intentional gold-target leakage positive control;
4. automated language/semantic-feature leakage audit;
5. reward-only quotient control;
6. held-out consequence test;
7. environment-label shuffle.

A baseline that remains strong after action or consequence shuffling does not demonstrate controlled-law recovery. A language model that proposes a finer partition without a held-out consequence that validates the split does not demonstrate a new target ontology.

## Resource and seed gate

Experiment execution has not begun, so no numerical resource result is reported in C071.

At execution start, every baseline must use fixed seeds `17`, `29`, and `43` and report:

- serialized model bytes;
- parameter count where applicable;
- peak RSS;
- training and evaluation wall time;
- hardware and software environment;
- dataset digest;
- exact command and commit;
- raw-result digest.

A run lacking any mandatory field is incomplete rather than negative.

## Public baseline reproduction status

C071 preregisters the baseline but does not falsely classify writing a protocol as numerical reproduction.

Status:

- theoretical baseline selection: completed;
- direct metric and control contract: completed;
- exact public implementation pin: still required before execution;
- dataset manifest and digest: still required;
- numerical run: not started;
- model size, RSS, time, and three-seed measurements: not yet applicable.

The implementation selection must prefer official/public code or a faithful minimal reproduction of the published objective. No architecture modification is allowed before selection and preregistration are complete.

## Decision

**NARROWED TO A PREREGISTERED LANGUAGE-BLIND QUOTIENT REPRODUCTION GATE — NOT ADOPTED.**

The remaining candidate RQ is:

> After a qualified language-blind baseline recovers the causal-state/bisimulation quotient induced by a preregistered full non-semantic consequence family, does raw language recover the same quotient more efficiently, or justify a different partition through an independent held-out consequence? A finer language partition without an independently observed separating consequence is not joint identification of a latent target ontology.

## Decision progress

C071 changes the next run from open-ended theory accumulation to a falsifiable baseline gate.

1. The baseline target object is fixed before implementation.
2. Reward-only and full-consequence quotients are separated.
3. Direct partition metrics replace task success as the central criterion.
4. Semantic leakage and shuffle controls are mandatory.
5. Three seeds and resource reporting become mandatory at numerical execution.
6. The next admissible work is exact public-code selection/pinning and execution, not a new architecture or another generic relabeling audit.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Baseline preregistration: completed as LBQ001.
- Public baseline numerical reproduction: not started.
- Exact public implementation pin for LBQ001: pending.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: mandatory at execution; not yet reported.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
