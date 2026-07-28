# Causal Identifiability Audit C091

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, exact full-consequence intervention-target quotient `P`, and denotation relation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, and (d) an identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C090 established that paired multimodal shared-factor recovery does not by itself identify denotation, because pairing may be explained by episode, instance, context, policy, or another shared nuisance.

C091 asks a narrower question:

> If utterances and physically present candidate targets are paired only at the scene or episode level, can cross-situational recurrence identify the language–target relation without semantic labels, and which assumptions turn co-occurrence learning into identification rather than a selection heuristic?

## Primary prior art

### Cross-situational word learning

Siskind (1996) formalized lexical acquisition under referential uncertainty and gave an implemented cross-situational algorithm that can learn homonymous lexicons from noisy multi-word observations under its declared assumptions. Yu and Smith (2007) experimentally showed that adults can recover word–referent mappings by accumulating cross-trial statistics even when each individual trial contains multiple words and multiple candidate objects.

Smith, Smith, and Blythe (2011), Blythe, Smith, and Smith's large-lexicon analyses, and subsequent finite-memory analyses study when repeated ambiguous exposures permit lexicon acquisition and how learning time depends on ambiguity, frequency, and memory assumptions. Blythe, Smith, and Smith (2016) additionally formalize learning under infinite referential uncertainty and show that learning can remain possible when candidate meanings have even a weak plausibility ranking.

Therefore the following broad claims are excluded from novelty:

- semantic-label-free scene-level co-occurrence can never support lexical mapping;
- referential ambiguity at each exposure makes lexicon learning impossible;
- accumulating statistics over repeated scenes is a new grounding mechanism;
- weak priors or plausibility rankings cannot make an otherwise unbounded candidate space learnable.

These are established positive results for declared lexical-learning models.

### Mutual exclusivity and competition

A large literature studies mutual exclusivity (ME), one-to-one word–referent assumptions, and competition between words and meanings. Computational analyses show that competition or ME can accelerate recovery under particular corpus correlations, while behavioral work also shows that learners can relax one-to-one mappings when evidence supports synonymy or one-to-many relations.

Thus ME is not an observation supplied by raw interaction. It is a linking assumption or inductive bias whose validity depends on the language and semantic level. It cannot be silently inserted into the candidate RQ and then counted as discovered denotation structure.

### Referential-intent assumption

Wang and Mintz (2018) held cross-situational co-occurrence information fixed while manipulating whether participants had reason to treat the novel signals as referential. Learners failed to acquire the mappings when the referential interpretation was undermined. This separates statistical recurrence from the assumption that the signals are labels or references at all.

For C, this means that a scene-level joint law may identify an association matrix while still failing to identify a denotation relation unless the observation model states why utterances are referential acts toward elements of the declared target quotient.

## Theorem / assumption / guarantee comparison

| Object | Observations | Key assumptions | Positive guarantee | Not guaranteed |
|---|---|---|---|---|
| Siskind-style cross-situational lexical acquisition | utterance word sets and candidate meaning sets over situations | declared lexicon model, contrast/competition assumptions, noise model, candidate-meaning representation | recovery of mappings within the model class | that candidate meanings equal exact controlled target blocks; validity of ontology or referential intent |
| Yu–Smith cross-situational learning | repeated ambiguous word/object scenes | stable statistical regularities and referential task | empirical recovery of trained word–object mappings | population point-identifiability of unrestricted `Q/P/d`; synonymy/polysemy/context relations |
| Mathematical large-lexicon / infinite-uncertainty analyses | repeated word exposures with candidate meaning rankings | exposure process, ambiguity model, memory or plausibility assumptions | conditions and learning-time behavior for lexicon acquisition | physical grounding of the candidate meaning inventory |
| Mutual-exclusivity / competition models | ambiguous word–referent co-occurrences | one-to-one or competitive mapping bias, or a mechanism approximating it | faster or better recovery in matching regimes | correctness under synonyms, hierarchical labels, polysemy, bilingual overlap, or many-to-one `d` |
| C087–C090 governed object | language law, exact controlled target quotient, and admissible cross-system observations | no semantic leakage; exact `P`; identified-set semantics | invariant must/cannot/may relations over compatible `(Q,P,d)` models | completion by co-occurrence score or ME alone |

## Proposition C091.1: scene-level recurrence identifies denotation only modulo the automorphisms of the incidence law

Let each episode expose:

- a set or multiset of raw linguistic forms `U_e`;
- a set or multiset of physically present target candidates `T_e`, where target identity is defined only through the C087 exact controlled quotient;
- no within-episode pointer, gaze, action consequence, temporal onset, or other observation linking an individual form to an individual target.

Let the population observation be the joint law of `(U_e, T_e)` over episodes. Suppose a nontrivial pair of permutations `(pi_Q, pi_P)` preserves this complete incidence law and all declared language-only and target-only observations.

Then replacing a candidate denotation relation `d` by

`d' = pi_P ◦ d ◦ pi_Q^{-1}`

produces an observationally equivalent model. Hence denotation is not point identified unless the scene distribution or an additional admissible linking channel breaks every nontrivial relative automorphism relevant to `d`.

Proof sketch:

1. Language-only observations are unchanged by `pi_Q` within their admitted equivalence class.
2. Target-only controlled observations are unchanged by `pi_P` within their admitted equivalence class.
3. By assumption, the episode incidence law is invariant under the paired transformation.
4. All observed probabilities are therefore identical although at least one language–target assertion changes.
5. The correct object is the orbit or identified set of denotation relations, not an arbitrarily selected matching.

This is an application of the residual joint-automorphism criterion to cross-situational incidence data, not a new intelligence principle.

## Counterexample 1: permanently confounded co-occurrence blocks

Let `Q={q1,q2}` and `P={p1,p2}`. Every episode that contains either language form contains both forms, and every such episode contains both targets:

`U_e={q1,q2}`, `T_e={p1,p2}`.

The following lexicons generate exactly the same observations:

- model A: `q1 -> p1`, `q2 -> p2`;
- model B: `q1 -> p2`, `q2 -> p1`.

Infinite data, exact co-occurrence probabilities, perfect language clustering, and perfect target quotient recovery do not distinguish them. A Hungarian assignment, random initialization, frequency ordering, or embedding similarity merely selects one completion.

The positive cross-situational path therefore requires a sufficiently asymmetric episode design, not merely more samples from an invariant design.

## Counterexample 2: mutual exclusivity creates a point answer by assumption

Suppose `q1` has already been linked to `p1`, while a new form `q2` occurs with `p1` and `p2`. Under one-to-one ME, the learner assigns `q2 -> p2`.

But the same observations are compatible with:

- synonymy: `q1 -> p1` and `q2 -> p1`;
- hierarchical reference: one form denotes a type and the other a subtype or instance;
- context-indexed polysemy: `q2` denotes `p1` in one context and `p2` in another;
- nonreferential usage: `q2` marks an action, discourse state, or speaker intention.

ME removes these models because of an extra lexical-structure assumption. It does not derive their impossibility from the observed scene law. A result that depends on ME must report the identified set under ME separately from the set under unrestricted many-to-many or context-indexed denotation.

## Counterexample 3: candidate-object recurrence can identify the wrong ontology

Let every utterance about a controllable button occur in scenes containing:

- the button instance;
- a persistent color patch attached to it;
- a location marker;
- the episode-specific background.

Cross-situational recurrence may isolate any feature that is perfectly stable across those scenes. Even when the learned referent is a real shared property, it need not equal the exact full-consequence target block `P`.

For example, color may be more statistically stable than actuator response. A learner can achieve perfect held-out scene retrieval and still fail every intervention-based target test. This is the scene-level analogue of C090's shared-nuisance shortcut.

A candidate referent inventory is admissible only when its elements are generated from the preregistered non-semantic controlled observation family, not from object IDs, visual annotations, simulator names, or evaluator labels.

## Counterexample 4: referential recurrence versus causal instruction

An utterance can co-occur reliably with a target because it:

- names the target;
- requests an action on the target;
- describes an effect caused by the target;
- warns against touching the target;
- marks the speaker's uncertainty about the target;
- refers to another entity that is systematically present with the target.

The same word–target incidence matrix can be produced by these distinct speech-act and semantic models. Thus statistical association may identify a relation but not its denotational type or direction.

Interactive grounding must preregister whether `d` is:

- object denotation;
- action/target argument structure;
- effect description;
- context-indexed relation;
- a more general typed relation.

Without typed observations, a high association score does not establish `d:Q->P`.

## Positive identifiability path retained

C091 does not conclude that scene-level grounding is impossible. It narrows the admissible positive path.

A cross-situational episode law can reduce or point-identify `d` when all of the following are justified:

1. **Candidate target validity**: candidate elements are blocks or measurable consequences of the exact non-semantic controlled quotient, not semantic object labels.
2. **Referential-act model**: the observation model states why the linguistic event is linked to one or more candidates and which typed relation is being learned.
3. **Incidence separation**: distinct denotation completions induce different population episode laws; equivalently, the relevant relative automorphism group is trivial or explicitly quotiented out.
4. **Cardinality/form declaration**: bijection, many-to-one, synonymy, polysemy, null reference, and context-indexed relations are declared rather than silently excluded.
5. **Nuisance control**: episode, speaker, template, instance, background, location, policy, and frequency cues are randomized, conditioned on, or tested with counterfactual shuffles.
6. **Direct intervention validation**: a mapping must predict held-out action-conditioned physical consequences, not only scene retrieval or object selection.
7. **Identified-set reporting**: unresolved symmetric completions remain `may-denote`; they are not collapsed by an optimizer or ME prior and reported as identified.

## Required negative controls for any future cross-situational baseline

- episode-level permutation preserving marginal word and target frequencies;
- within-scene target permutation;
- nuisance-preserving scene shuffle;
- same co-occurrence matrix with denotation swapped;
- synonym control violating one-to-one ME;
- polysemy/context control;
- nonreferential-signal control with identical co-occurrence counts;
- target-ID-generated candidate-set leakage scan;
- held-out intervention consequence test;
- direct must/cannot/may-denote evaluation.

A baseline that succeeds after the denotation-swapped incidence control or fails to distinguish referential from nonreferential generation cannot support a joint-identification claim.

## Prior-art matrix update

| Prior art / object | Positive guarantee or evidence | Critical assumption | What remains outside guarantee | C091 classification |
|---|---|---|---|---|
| Siskind 1996 | implemented cross-situational lexical acquisition under noisy ambiguity | declared candidate meanings and lexical/contrast model | physical validity of candidate meanings and unrestricted denotation form | lexical mapping prior art |
| Yu & Smith 2007 | humans recover trained mappings from repeated ambiguous trials | referential experimental task and structured recurrence | general population identifiability and external causal quotient | empirical cross-situational prior art |
| Smith/Smith/Blythe analyses | feasibility and learning-time results for large lexicons | exposure, ambiguity, memory, and ranking assumptions | joint `Q/P/d` orientation | theoretical lexical-learning prior art |
| Wang & Mintz 2018 | same co-occurrence statistics do not induce mapping when referential interpretation is removed | learner's referential goal/assumption | formal causal-target identification | evidence that co-occurrence alone is not semantic typing |
| ME / competition literature | faster mapping or competition under suitable regimes | one-to-one or competitive lexical bias | synonyms, hierarchy, polysemy, many-to-many relations | assumption-sensitive prior art |
| C088 identified set | invariant denotation assertions over compatible models | explicit observation and assumption set | concrete symmetry-breaking scene law | governing partial-identification contract |
| C090 paired shared-factor audit | paired views can identify shared latent information | multimodal generative assumptions | whether shared information is denotation | paired-view boundary retained |

## Public-code availability audit

The reviewed primary literature contains implemented algorithms and computational models, but this run did not confirm a paper-specific, author-maintained immutable repository satisfying the canonical reproduction contract for the exact cross-situational theorem/experiment selected here.

In particular, no candidate was promoted without all of:

- immutable commit and provenance;
- exact corpus/scene generator and digest;
- explicit candidate-target construction;
- denotation-form assumptions;
- seeds `17 / 29 / 43`;
- deterministic configuration;
- model size and parameter count;
- peak RSS and wall time;
- direct `Q/P/d` and must/cannot/may metrics;
- incidence-automorphism and ME-violation controls.

Therefore C091 completes prior-art and identifiability auditing, not public numerical reproduction.

## Decision

> **NARROWED BEYOND CROSS-SITUATIONAL WORD–REFERENT LEARNING — repeated ambiguous scene statistics, weak plausibility rankings, mutual-exclusivity/competition models, and implemented lexical acquisition are established prior art. Scene-level semantic-label-free pairing can shrink the denotation identified set only when its incidence law breaks the relevant language–target automorphisms and when referential type, candidate-target validity, synonymy/polysemy/cardinality, and nuisance structure are explicitly modeled. Mutual exclusivity or optimizer-selected matching is an assumption-driven completion, not identification. RQ-001 remains NOT ADOPTED.**

## Next decision gate

The next useful audit is not another generic co-occurrence learner. It is one of:

1. a primary theorem that gives point or partial identifiability of a typed lexicon/referential relation from ambiguous sets under explicit rank, expansion, separability, or intervention assumptions; or
2. a public baseline whose scene generator is semantic-label-free and whose population incidence matrix can be audited for residual automorphisms; or
3. an active grounding protocol in which the learner chooses a physical intervention/query and the response law provably breaks a denotation symmetry without target-indexed supervision.

Until one of these gates is met, cross-situational association remains a baseline signal rather than evidence for a new joint-identification result.

## Current status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Identifiability counterexample: completed.
- Cross-situational lexical mapping: existing prior art.
- Mutual exclusivity/competition: existing assumption-sensitive prior art.
- Referential intent from co-occurrence alone: not identified.
- Scene-incidence automorphism criterion: applied and fixed as a decision test.
- Public numerical reproduction: not started.
- New architecture: none.
- Legacy A–E toy mechanisms: none added.
- Novelty: not established.
- Intelligence principle: not claimed.
- Capability progress: not claimed.
