# Phase 18a-2: Continuous Japanese segmentation and grounding

## Removed shortcuts

Phase 18a-1 used whitespace-delimited tokens, a predicate-ending heuristic, and a
hiragana particle heuristic. Phase 18a-2 removes all three.

The learner receives:

- a continuous normalized Japanese character string with no whitespace;
- an anonymous numeric world state before the event;
- the anonymous state after the event.

No character span is labeled as an entity, action, particle, modifier, or word. The
learner is not given a morphological dictionary or a Japanese tokenizer.

## Declared finite hypothesis class

The candidate lexicon contains every recurring substring of one to six normalized
characters. The six-character ceiling is an explicit remaining prior and is included
in the claim boundary.

For a candidate substring `w`, collect all immediate left and right characters seen
around its occurrences. A segment is retained only when both sides have at least two
distinct observed contexts.

This boundary-diversity prior is language-neutral. It rejects many internal fragments
because an internal character sequence has a fixed neighbor on at least one side. It
also rejects many entity-plus-particle superspans because they occur in only a subset
of the entity's causal interventions.

The negative ablation removes this prior. Internal character fragments then tie with
the full entity lexemes, and the grounding is non-identifiable.

## Entity grounding objective

For each candidate substring `w`, define its observation-incidence signature

```text
s_w[i] = 1 iff w occurs in observation i.
```

For each anonymous coordinate `q`, infer whether it is the source or destination of
the observed copy intervention and define

```text
c_q[i] = 1 iff q participates in observation i.
```

The entity lexicon is the injective assignment minimizing

```text
sum_q Hamming(s_assignment(q), c_q).
```

Unlike Phase 17g, exact equality is not required. The training set contains one
omitted participant mention and one spurious participant mention.

The implementation performs exact branch-and-bound over the full declared finite
candidate space. The pruning lower bound ignores uniqueness for remaining
coordinates, so it is admissible. The reported best and second-best costs are exact
within this finite hypothesis class.

A unique minimum with a positive margin is required. Equal-cost assignments are
retained as non-identifiable.

## Action segmentation without morphology

After entity grounding, the learner keeps recurring substrings that can occur once
outside the two entity spans. It does not use:

- verb endings;
- script categories;
- character-length rules specific to particles;
- a list of Japanese function words.

Candidate action lexicons are enumerated as exact covers: every complete training
sentence must contain exactly one selected action substring.

Many false covers survive this stage. Examples include case markers, action
fragments, and action-plus-marker superspans. They are filtered by the semantic
factorization test below.

## Literal frame induction and semantic factorization

Given two entity spans and one candidate action span, the minimal character interval
covering those spans is converted to a literal template:

```text
アキがボブに渡す
E0 が E1 に A
```

Spaces above are explanatory only; none exist in the actual input.

The learner stores the resulting continuous templates as atomic frame hypotheses.
This is not yet a general grammar. It is deliberately more honest than calling a
handwritten particle parser learned language understanding.

Each observation yields one binary equation:

```text
action_bit XOR frame_bit = observed surface direction.
```

Repeated observations are majority-cleaned. The action-frame graph must be connected
and cycle-consistent. Candidate segmentations that create disconnected or
contradictory semantics are rejected.

Among surviving models, selection is lexicographic:

1. minimum training direction errors;
2. minimum declared description units.

A unique optimum is required.

## Noise design

The positive campaign contains ten identifying action-frame edges. Every edge is
observed 25 times, with two adversarially placed direction flips.

```text
empirical flip rate = 2 / 25 = 8%
```

The deterministic experiment does not itself satisfy an IID-noise assumption. For
reference, under independent Bernoulli flips with the same rate, a Hoeffding union
bound is reported for failure of any majority among the ten edges.

## Held-out evaluation

The held-out set contains all six action-frame combinations absent from training.
Each combination is evaluated as a role-reversal pair using:

- the same before-state;
- the same character multiset;
- different entity order and different correct state transition;
- prefixes and suffixes not used in training.

Therefore a classifier that receives only the unordered character multiset and the
before-state has an exact 50% upper bound.

The following baselines are also reported:

- exact sentence memorization;
- action-only majority;
- frame-only majority;
- seen action-frame-pair memorization.

## Negative controls

The campaign preserves these failures:

1. Removing boundary diversity leaves multiple best entity segmentations.
2. A recurrent substring deliberately given the same occurrence pattern as one
   entity leaves multiple best groundings.
3. A tied majority label is rejected.
4. A disconnected action-frame graph is rejected.
5. Unknown actions and unknown frames cause abstention.

These are not optimization failures. Under the declared observations and hypothesis
class, the data do not select one total semantic model.

## Resource accounting

The campaign reports separately:

- serialized acquired lexicon and factorization bits;
- Phase 18a-2 implementation source bytes;
- theoretical grounding assignments;
- exact branch-and-bound nodes and complete assignments evaluated;
- Python runtime and standard-library substrate as excluded.

The acquired payload must not be described as total model size.

## Claim boundary

A successful campaign supports only this statement:

> A small continuous-character Japanese micro-language can be segmented and grounded
> without whitespace, a morphological dictionary, predicate suffix rules, or
> particle script rules when causal interventions and sufficient boundary variation
> make the intended lexemes identifiable.

It does not establish:

- unrestricted Japanese tokenization;
- inflectional morphology;
- synonymy or polysemy;
- ellipsis resolution from discourse;
- negation, passive, causative, coordination, or recursion;
- reading comprehension;
- Japanese high-school-level intelligence;
- general LLM parity.

## Next gate

Phase 18a-3 should replace literal whole-frame storage with reusable local relation
units and should introduce:

- inflected action forms sharing one latent meaning;
- synonymous actions and particles;
- passive and causative alternations;
- omitted arguments recoverable from a short discourse;
- two events in one sentence;
- prospective held-out surface constructions;
- a sequence model baseline matched for total persistent bits and inference work.

The central question is whether the learner can compress multiple surface templates
into a smaller reusable relational grammar rather than accumulating one template per
construction.
