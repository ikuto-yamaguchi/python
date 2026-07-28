# Causal Identifiability Audit C092

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, exact full-consequence intervention-target quotient `P`, and typed/context-indexed denotation relation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (d) an adaptive-identifiability counterexample, and a public-code provenance pin.
- Numerical execution is not started; model size, parameter count, peak RSS, wall time, exact commands, raw-result digests, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C091 established that passive cross-situational recurrence identifies denotation only modulo automorphisms of the scene-incidence law.

C092 asks the narrower active question:

> Can a learner break the residual `Q`–`P` automorphism by choosing clarification questions or physical interventions adaptively, without receiving target-indexed semantic supervision, and what must be true of the admissible query/answer channel for the resulting alignment to count as identification rather than oracle codebook acquisition?

## Primary prior art

### Opportunistic active learning for grounded descriptions

Thomason et al. (CoRL 2017), *Opportunistic Active Learning for Grounding Natural Language Descriptions*, place active learning inside an interactive robot object-identification task. The robot may ask users about meanings of words, including questions that are not immediately necessary for the current object-selection task. The reported real-robot experiments show that inquisitive behavior improves future object identification.

Padmakumar, Stone, and Mooney (EMNLP 2018), *Learning a Policy for Opportunistic Active Learning*, learn a reinforcement-learning policy that trades off completing the current interaction against asking questions that improve the grounding model for future interactions.

She and Chai (ACL 2017), *Interactive Learning of Grounded Verb Semantics towards Human-Robot Communication*, likewise use proactive questions and reinforcement learning to acquire grounded verb models from human demonstrations and answers.

Therefore the following broad claims are excluded from novelty:

- robots can improve grounded lexical or verb models by asking questions;
- active learning can trade off immediate task completion against future grounding accuracy;
- clarification and concept-learning queries can be selected by a learned policy;
- off-topic questions can improve later object identification;
- interactive human answers can reduce uncertainty in an existing supervised grounding model.

These are established algorithmic and empirical results.

### Active learning with richer query languages

Kontonis, Ma, and Tzamos (COLT 2024), *Active Learning with Simple Questions*, formalize region queries that ask whether all examples in a selected region have a chosen label. They quantify the trade-off between query complexity and the number of interaction rounds.

This excludes another overly broad novelty claim: that stronger, structured questions can reduce the number of active-learning rounds. However, their target label and concept class are part of the learning problem definition; the result does not derive a physical target ontology or a denotation type from unlabeled interaction.

### Clarification systems

Recent clarification work evaluates whether a system should ask, which interpretation to clarify, and whether the resulting answer improves task accuracy. These systems establish that clarification can reduce ambiguity under a declared intent inventory. They do not by themselves show that the intent inventory equals the exact controlled target quotient or that the answer channel is semantic-label-free.

## Theorem / assumption / guarantee comparison

| Object | Chosen query | Answer channel | Positive guarantee/evidence | Not guaranteed for RQ-001 |
|---|---|---|---|---|
| Thomason et al. 2017 | ask whether a perceptual word applies to an available object/property example | human-provided concept label/confirmation | improved object identification over time | discovery of `P`; denotation without label supervision; exact joint identified set |
| Padmakumar et al. 2018 | policy-selected clarification or active-learning action | simulated/task-defined answer and reward | learned trade-off between current task and future model gain | that reward or answers are independent of a semantic codebook |
| She & Chai 2017 | robot-selected questions about demonstrated verb semantics | human answer/demonstration in a predefined verb/action representation | improved grounded verb acquisition | identification of an unrestricted typed `d` or unknown exact target quotient |
| Kontonis et al. 2024 | region query over an already defined domain and label | labeler truth value under target concept | query-complexity/round-complexity results | construction of the label ontology, physical target partition, or referential type |
| C087–C091 governed object | admissible physical intervention or clarification generated without target IDs | non-semantic consequences or explicitly modeled human act | shrinkage of the joint `(Q,P,d)` identified set | point completion when two models induce the same adaptive transcript law |

## Proposition C092.1: adaptive interaction identifies only up to policy-wise observational equivalence

Let a model `M` specify candidate `Q`, exact controlled `P`, typed denotation `d`, and the law of answers and physical consequences. At round `t`, an adaptive policy chooses query/action

`A_t = pi_t(H_t)`

from the previous transcript `H_t`, and observes response `Y_t`.

Suppose two candidate models `M` and `M'` have different denotation relations, but for every admissible history and every admissible query/action,

`Law_M(Y_t | H_t, A_t) = Law_M'(Y_t | H_t, A_t)`.

Then every adaptive policy induces the same distribution over complete transcripts under `M` and `M'`.

Proof sketch:

1. The empty-history distribution is identical.
2. If the history distribution is identical through round `t`, the policy selects the same distribution over `A_t` because it is a function of that history.
3. By assumption, the conditional response law is identical for every selected action.
4. Hence the extended history distribution is identical.
5. Induction gives equality of every finite adaptive transcript law, despite different `d`.

Therefore:

> Adaptivity cannot break a symmetry that is preserved by every admissible query/answer channel. More interaction helps only when at least one physically and procedurally admissible query has a response distribution that differs across the remaining denotation completions.

This is the active analogue of C091's incidence-law automorphism boundary. It is not a new intelligence principle.

## Counterexample 1: symmetric yes/no clarification

Let `Q={q1,q2}` and `P={p1,p2}`. Consider two models:

- `M_A`: `q1 -> p1`, `q2 -> p2`;
- `M_B`: `q1 -> p2`, `q2 -> p1`.

The learner may ask only symmetric questions of the form:

- “Does this utterance refer to one of the two active controls?”
- “Will acting on the referred control change the lamp?”
- “Is the requested target present?”

Suppose both targets are present and have the same coarse lamp consequence, although they differ under a held-out consequence not available to the query interface. Every allowed answer is identical under `M_A` and `M_B`.

An adaptive learner can ask forever but cannot orient `q1/q2` relative to `p1/p2`. Query count and policy sophistication do not matter. The missing ingredient is a separating query, not another architecture.

## Counterexample 2: label-oracle clarification breaks symmetry by supplying the answer

Suppose the system may ask:

> “Does `q1` mean target `p1`?”

and the human answers truthfully using the benchmark's gold target codebook.

This query does break the symmetry, but it does so because its syntax and answer channel already name both sides of the unknown relation. It is direct denotation supervision.

Renaming `p1` to `channel-17` does not remove the supervision when the human and evaluator know that `channel-17` is the gold target identity. Likewise, asking whether a word applies to a bounding box whose identity was created from a gold object annotation is target-indexed supervision through the query graph.

Such a run is useful as:

- an oracle positive control;
- an annotation-cost baseline;
- an upper bound on interactive sample efficiency.

It is not evidence that raw language and a latent intervention partition were jointly identified from semantic-label-free observations.

## Counterexample 3: truthful answers can still identify the wrong relation type

A human may truthfully answer “yes” when asked whether `red` applies to an object. This can identify a perceptual predicate-object relation.

But the candidate RQ may concern:

- object denotation;
- an action's target argument;
- an effect description;
- a warning/prohibition relation;
- a context-indexed reference.

A question-answer channel trained around attribute applicability can be perfectly accurate while leaving the target of an imperative unresolved. Interactive accuracy does not establish that the learned relation has the required type.

## Counterexample 4: shared human convention is an assumption, not a physical observation

Two humans can answer the same clarification consistently because they share a naming convention. The answer channel may therefore point-identify a community lexicon even when the physical controlled law admits a target permutation.

This is a valid route to conventional linguistic meaning if the study's estimand is explicitly the human community's codebook. It is not a language-blind physical identification of `P`, and it must not be reported as discovering an extra-behavioral ontology from causal consequences alone.

The audit must distinguish:

- **physical target identification** from controlled consequences;
- **conventional label acquisition** from a human teacher;
- **joint grounding** that links the two under an explicit teacher-response model.

## Positive active-identifiability path retained

Active interaction can shrink or point-identify the joint set only if all of the following are fixed and audited:

1. **Query admissibility**: the learner can physically or linguistically issue the query without reading target IDs, parser slots, simulator object names, target masks, or evaluator labels.
2. **Separating family**: for every pair of remaining incompatible `(Q,P,d)` completions, at least one admissible query induces different response/consequence laws.
3. **Teacher/response model**: honesty, noise, competence, pragmatic behavior, refusal, and context dependence are declared; answers are not treated as noiseless facts by default.
4. **Relation typing**: the query distinguishes the required object/action/effect/speech-act relation rather than only an easier correlated predicate.
5. **Physical anchoring**: target candidates are generated from the preregistered non-semantic controlled consequence family.
6. **Nuisance control**: query wording, position, object instance, speaker, template, episode, and answer-frequency shortcuts are randomized or counterfactually tested.
7. **Identified-set update**: an answer removes only models that assign zero or sufficiently bounded likelihood under the declared response model; optimizer preference is not identification.
8. **Abstention**: if no admissible separating query exists, the output remains `may-denote`/unresolved.
9. **Held-out intervention validation**: the inferred mapping predicts action-conditioned physical consequences not used to generate teacher labels or rewards.

A useful positive theorem or baseline must state the separating-query condition explicitly. “The policy asks informative questions” is not enough unless informative means that the complete admissible transcript law distinguishes all claimed alternatives.

## Required controls for future active grounding execution

- **Gold-label oracle control**: direct target/attribute questions, reported only as supervised upper bound.
- **Semantic-label-free physical-query condition**: no human target-name answer; only preregistered consequences.
- **Symmetric-query control**: all available questions preserve a known denotation swap; correct output must remain unresolved.
- **Unavailable-separator control**: the only distinguishing action is removed; the policy must abstain.
- **Teacher-noise control**: declared stochastic answer model with calibrated identified-set update.
- **Adversarial pragmatics control**: truthful but nonliteral/cooperative answer policies that preserve multiple denotation models.
- **Question-template permutation**: destroys lexical shortcuts while preserving query semantics.
- **Object/instance permutation**: tests instance-ID and screen-position leakage.
- **Answer-frequency equalization**: prevents majority-answer shortcuts.
- **Held-out controlled consequence test**: mapping must predict unseen action-conditioned effects.
- **Must/cannot/may-denote metrics**: not only task success or object retrieval.

## Prior-art matrix update

| Prior art / object | Positive contribution | Critical supervision/assumption | Remaining outside guarantee | C092 classification |
|---|---|---|---|---|
| Thomason et al. 2017 | opportunistic questions improve grounded object identification | human supplies applicability labels for selected word/example queries | unknown `P`, semantic-label-free `d`, exact identified set | interactive supervised grounding prior art |
| Padmakumar et al. 2018 | learned policy trades task completion against future active-learning gain | predefined predicates, answer simulator/task reward, supervised concept updates | identifiability under residual automorphisms | dialog-policy prior art |
| She & Chai 2017 | proactive questions improve grounded verb acquisition | predefined demonstrations, question types, teacher semantics | unrestricted typed relation and unknown causal quotient | interactive verb-learning prior art |
| Kontonis et al. 2024 | richer region queries reduce active-learning interaction complexity | known domain, label space, target concept, truthful labeler | construction/orientation of `Q/P/d` | query-complexity prior art |
| C091 passive scene law | denotation identified only modulo incidence automorphisms | declared scene and relation model | active separator characterization | inherited boundary |
| C092 adaptive transcript law | no policy can distinguish models identical under every admissible query response | full policy-wise response model | concrete semantic-label-free separating protocol | governing active-identifiability criterion |

## Public-code provenance audit

An author-maintained public implementation was confirmed for Padmakumar, Stone, and Mooney's EMNLP 2018 policy work:

- repository: `aishwaryap/rl_for_oal`
- immutable commit: `56130967e6ac418c059d27f2dc683e841af48202`
- README pipeline includes static-policy creation/testing, learned-policy creation, initialization from static-policy episodes, training, testing, and bulk evaluation;
- the implementation depends on a separately preprocessed Visual Genome dataset and an external preprocessing repository/commit.

The code is valuable as a public interactive-active-learning baseline candidate, but it is not promoted to canonical numerical reproduction in this run because the current contract still lacks:

- dataset archive and preprocessing digests;
- dependency/runtime lock and container;
- exact answer-simulator and gold-label provenance audit;
- target-candidate construction from C087 non-semantic controlled consequences;
- semantic-label-free separator condition;
- seeds `17 / 29 / 43`;
- deterministic configuration;
- model size and parameter count;
- peak RSS and train/evaluation wall time;
- raw-result digests;
- direct `Q/P/d` and must/cannot/may metrics;
- denotation-swap and unavailable-separator controls.

Thus this run pins public code and completes suitability auditing, but does not start numerical reproduction.

## Decision

> **NARROWED BEYOND INTERACTIVE CLARIFICATION AND OPPORTUNISTIC ACTIVE GROUNDING — asking users concept questions, learning a dialog policy, and improving object or verb grounding through interaction are established prior art. Adaptive interaction point-identifies denotation only when the admissible query/answer family separates every remaining joint completion under an explicit teacher/response model. A query that names a gold target, asks for predicate applicability to a gold object, or receives a target-indexed answer breaks symmetry by supplying semantic supervision and is only an oracle control. If every semantic-label-free admissible query preserves a denotation automorphism, no adaptive policy can remove it. RQ-001 remains NOT ADOPTED.**

## Next decision gate

The next useful run is not another query-policy architecture. It should do one of:

1. identify a primary theorem for active experiment/query design whose separating-family or version-space condition can be instantiated for typed `Q/P/d`;
2. preregister a semantic-label-free physical query protocol in which candidate actions and responses are generated solely from C087's exact controlled consequence family, then prove whether its adaptive transcript law has a trivial residual automorphism group;
3. reproduce the pinned `rl_for_oal` baseline strictly as a supervised oracle control after freezing dataset provenance, runtime, three seeds, model size, RSS, wall time, and direct relation metrics;
4. construct an impossibility certificate showing that the current physical interface lacks any admissible separator for at least one denotation orbit.

Until one gate is met, active question selection is evidence of improved supervised grounding efficiency, not evidence of a new joint-identification principle.

## Claims discipline

- No novelty claim is made.
- No intelligence principle is claimed.
- No capability progress is claimed.
- No new architecture is proposed.
- No legacy toy mechanism is added.
- RQ-001 remains not adopted.