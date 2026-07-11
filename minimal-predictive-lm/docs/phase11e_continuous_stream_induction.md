# Phase 11e: continuous mixed-stream event induction

## Why this phase exists

Phase 11d removed task-family labels, but still received individual records,
channel metadata, and strongly quoted source/target spans. A system that requires
those boundaries to be supplied is not yet learning from ordinary experience.

Phase 11e therefore receives one continuous mixed-style stream and must infer:

- candidate event boundaries,
- source and result values,
- success or failure,
- whether the event is conditional,
- provenance identifiers,
- which events share one latent primitive.

No domain-specific parser is selected from a channel label.

## Current induction procedure

The current implementation deliberately uses a small, auditable meta-grammar:

1. split the stream at generic punctuation or line boundaries,
2. enumerate nearby identifier-like token pairs,
3. retain pairs whose changed characters share one codepoint offset,
4. score them by changed-character support and locality,
5. infer result, condition, and provenance roles from a bounded cue inventory,
6. group events by offset,
7. retain a primitive only when its support repays its description cost.

For event set \(E_p\) explained by primitive \(p\), the experimental selection
score is

\[
G(p)=|E_p|B_{evidence}-L(p).
\]

A primitive is kept only when \(G(p)>0\). This prevents every isolated residual
from becoming a permanent library entry.

## What was removed

Compared with Phase 11d, the learner is no longer given:

- a `RawResidualObservation` object for each event,
- task-family labels,
- channel metadata,
- quoted or backticked source/target spans.

The same event and primitive representation is used for Japanese-like,
repository-like, sensor-like, and CI-like surface text.

## What remains supplied indirectly

This is not unrestricted stream understanding. Generic punctuation still provides
strong segmentation evidence. Result, condition, and provenance roles are drawn
from a finite multilingual cue inventory. Source and target candidates are nearby
ASCII identifier-like tokens, and the latent transformation family is restricted
to constant codepoint offsets.

Consequently the experiment establishes a narrower result:

> Given a bounded transformation meta-grammar, record and channel labels are not
> necessary for recovering shared executable primitives from a continuous stream.

It does not establish open-domain event discovery or general language understanding.

## Relation to LLM comparison

The project can already perform a matched open-model comparison on one narrow
public arithmetic domain. Phase 11e reduces one major source of hidden supervision,
but a broad LLM comparison still requires:

1. a public multi-domain suite consumed from raw inputs,
2. the same learner and library across those domains without per-domain code,
3. candidate generation outside the fixed offset meta-grammar,
4. natural-language generation and semantic-quality evaluation,
5. matched resource accounting for both systems.

Phase 12a should therefore build a mixed-domain comparison suite rather than claim
parity from this synthetic stream experiment.
