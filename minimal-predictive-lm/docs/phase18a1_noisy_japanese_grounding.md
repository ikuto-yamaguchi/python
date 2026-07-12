# Phase 18a-1: Noisy controlled-Japanese grounding

## Purpose

Phase 17g learned token roles and binary event semantics from anonymous world
interventions, but it still used artificial symbols and exact occurrence signatures.
Phase 18a-1 introduces a small Japanese case-frame language and two distinct kinds
of noise:

- bounded direction-label corruption on repeated action/frame observations;
- one omitted participant mention and one spurious participant mention in the
  entity-grounding evidence.

The goal is not to claim Japanese understanding. The goal is to determine whether a
reusable semantic factorization can still be recovered when exact matching no longer
works and when Japanese particles and word order are causally necessary.

## Controlled observation model

The learner receives:

- a whitespace-tokenized Japanese sentence;
- an anonymous four-coordinate state before the event;
- the anonymous state after the event.

Surface names never equal coordinate names. Entity identities are not supplied.
The training language contains:

- four surface entity aliases;
- four Japanese predicate tokens;
- five case/order frames using `が`, `に`, `は`, `へ`, `から`, and a zero-particle
  position;
- optional modifiers and punctuation;
- one binary copy event per complete sentence.

Morpheme boundaries are supplied by whitespace. This remains a major human-designed
bias.

## Robust entity grounding

For token `w`, define the occurrence vector

```text
s_w[i] = 1 iff w appears in observation i.
```

For anonymous coordinate `q`, define the causal-participation vector

```text
c_q[i] = 1 iff q is the inferred source or destination in observation i.
```

Unlike Phase 17g, Phase 18a-1 does not require exact equality. It exhaustively
searches all injective token-to-coordinate assignments and minimizes

```text
L(g) = sum_q Hamming(s_{g(q)}, c_q).
```

A grounding is accepted only when the minimum-loss assignment is unique. Equal-loss
aliases are retained as a non-identifiability result. The positive campaign includes
one omitted mention and one spurious entity mention, so the optimum loss is nonzero.

A negative control appends a new token whenever one true entity token appears. The
new token then has exactly the same occurrence signature and produces two equal-cost
groundings. The learner must reject uniqueness rather than choose one arbitrarily.

## Japanese case-frame factorization

After grounding entity aliases, the learner uses a deliberately small Japanese
morphology prior:

- candidate predicates end in `す` or `る`;
- a one- or two-hiragana token immediately following an entity is treated as a case
  particle candidate;
- otherwise the particle is `<ZERO>`.

Each complete sentence produces:

```text
action token
case-frame key = (particle after first entity,
                  particle after second entity,
                  action position among the two entities and action)
effective direction bit
```

The semantic model factorizes the direction as

```text
action_bit XOR case_frame_bit.
```

The observed action/frame pairs form a bipartite graph. After noise correction, a
total semantic model is accepted only when this graph is connected and
cycle-consistent. A disconnected control is rejected.

## Bounded label-noise recovery

Each identifying action/frame edge is repeated 21 times. Two labels per edge are
flipped, giving an empirical corruption rate of

```text
2 / 21 = 9.52%.
```

The learner takes the majority label for each repeated edge. A tied majority is a
hard failure.

Under independent Bernoulli flips with probability `eta < 1/2`, Hoeffding's
inequality gives the per-edge majority-error bound

```text
exp(-2 r (1/2 - eta)^2).
```

For `K` observed edges, a union bound gives

```text
K exp(-2 r (1/2 - eta)^2).
```

With `K=8`, `r=21`, and `eta=2/21`, the declared bound is below one percent. The
actual generated corruption is deterministic and bounded, not IID, so the bound is
reported as a theoretical reference under its explicit assumption rather than as a
probability guarantee for the deterministic generator.

## Frozen held-out evaluation

Training observes a spanning tree of eight action/frame combinations. Evaluation
contains every remaining action/frame combination, with adjacent role-reversal
pairs. The pair members share:

- the same anonymous before-state;
- the same positionless token multiset;
- the same action and case-frame inventory;

but require different state transitions.

The required comparisons are:

- full factorized learner;
- positionless token-multiset classifier;
- action-only ablation;
- frame-only ablation;
- exact action/frame-pair memorizer;
- exact sentence memorizer.

The action/frame-pair memorizer has zero held-out coverage by construction. The
factorized learner must transfer through separately learned action and frame bits.

## Claim gate

Phase 18a-1 passes only if all of the following hold:

- the noisy entity-grounding optimum is unique and has positive loss margin;
- the signature-collision control has multiple optima;
- incomplete/spurious mention rows do not become accidental semantic equations;
- every repeated edge recovers its clean majority label;
- the finite-sample reference bound is below one percent;
- tied-majority and disconnected-graph controls are rejected;
- unseen action/frame compositions achieve 100% accuracy and coverage;
- the positionless surface upper bound is exactly 50%;
- action-only and frame-only ablations remain imperfect;
- exact action/frame-pair memorization has zero coverage.

## Resource accounting

The campaign reports separately:

- serialized acquired entity/action/frame model bits;
- number of token-to-coordinate assignments searched;
- linear factorization operations;
- Phase 18a-1 source bytes;
- excluded Python runtime and standard-library substrate.

The acquired payload must not be described as total deployment size.

## Remaining limitations

This experiment is still far below ordinary Japanese comprehension.

- Segmentation is supplied by whitespace.
- Predicate and particle candidate shapes are handwritten.
- Repeated observations of the same latent action/frame edge are available.
- Complete semantic rows contain exactly two participants and one binary event.
- Ellipsis is present only in grounding evidence, not resolved at inference time.
- There is no synonymy, polysemy, negation, tense, aspect, quantification, discourse,
  anaphora, or multi-event composition.
- World supervision is an explicit anonymous state transition.

## Next gate

Phase 18a-2 should remove whitespace segmentation and the `-す/-る` predicate
heuristic. It should learn morpheme boundaries and reusable case markers jointly,
then test:

- kana/kanji surface variants;
- unseen synonyms and paraphrases;
- topic omission recoverable from short discourse;
- negation and passive/causative alternations;
- multiple events and argument sharing;
- probabilistic rather than repeated-identical observations;
- compact neural, finite-state, retrieval, and memorization baselines under matched
  resources.

Until those gates pass, this campaign supports only a claim of controlled,
noise-tolerant Japanese case-frame grounding.
