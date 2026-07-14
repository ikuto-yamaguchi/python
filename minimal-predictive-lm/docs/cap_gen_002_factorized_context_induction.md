# CAP-GEN-002-RII-003: factorized context-equivalence induction

## Problem attacked

RII-001 and RII-002 discovered raw span boundaries and executable transformations, but
only when the same complete `(left anchor, right anchor)` pair recurred many times.  That
is still a supplied-looking segmentation cue hidden inside the generated data.

RII-003 removes repeated full anchor pairs.  Each role has four left-context variants and
four right-context variants.  Training contains only off-diagonal combinations; frozen
evaluation contains only diagonal combinations.  Therefore no complete source or target
context pair seen during training occurs in evaluation.

The learner receives one `bytes` object.  Hidden boundaries, role identities, context
classes, program identities, and the train/evaluation combination split are scorer-only.

## Hypothesis

Exact context pairs are the wrong memory unit when left and right evidence vary
independently.  The learner should infer four sets per role:

```text
source-left class
source-right class
target-left class
target-right class
```

and recognize the cross-product rather than memorize each complete pair.

High-confidence exact program matches are first proposed from every raw source span and
every nearby target span.  In the chronological fit prefix, independently recurring
left/right contexts create candidate classes.  A later raw suffix calibrates which
variants genuinely compose.  The accepted model must then predict unseen left/right
combinations in a separate stream.

No context pair, variable, event, source, target, transformation, task, or domain label is
passed to the discovery API.

## Resource separation

For one role with `L` left variants and `R` right variants, complete-pair storage covers
the cross-product using `L*R` context records.  Factorized storage uses `L+R` anchors.
For balanced `L=R=k` and constant anchor width:

```text
exact pair storage: Theta(k^2)
factorized storage: Theta(k)
```

This is a standard factorization benefit, not a novelty theorem.  Its purpose here is to
remove a concrete quadratic bottleneck from the raw-boundary learner and to make unseen
combination transfer falsifiable.

The frozen experiment has four variants at every context position.  Across three roles:

- explicit complete cross-product contexts: 4,608 bits;
- factorized anchors, programs, and role framing: 1,251 bits.

Training search remains expensive and is reported separately.  The implementation tests
all raw source spans against 682 loop programs; no claim of optimal induction compute is
made.

## Chronological anti-overfit protocol

The first two off-diagonal combination blocks form the fit prefix.  A same-alphabet raw
bridge makes the fixed two-thirds byte split land before the third off-diagonal block.
The final block calibrates context variants and was not used to create their support
counts.

Frozen evaluation uses only diagonal combinations.  Every individual anchor variant was
seen during fit/calibration, but no complete left/right combination was seen.  This is
**combinatorial context transfer**, not grounding of new vocabulary or new context
features.

## Required controls

1. Recover every hidden training source/target boundary with precision and recall 1.0.
2. Discover three context roles and the three shared loop programs.
3. Predict every frozen diagonal-combination target exactly.
4. Produce zero paired predictions with an exact-pair memorizer.
5. Produce zero links with the RII-002 exact-anchor learner.
6. Reject an independent-target stream.
7. Use fewer model bits than explicit complete-cross-product storage.
8. Report raw span indexing, program executions, context scans, and program operations.

## Difference from prior phases

- Phase 11e split text with punctuation regexes and used word, outcome, condition,
  provenance, stopword, and offset hypotheses supplied in code.
- RII-001/002 proposed raw boundaries but required one exact left/right anchor pair to
  recur at least eight times.
- RII-003 allows every full pair to occur once and learns independent context classes
  from transformation-consistent evidence.

It still reuses the bounded loop VM from RII-002.  It does not solve unrestricted
operator invention.

## Claim boundary

Passing establishes only that a compact factorized role model can be induced from a raw
synthetic stream and transfer to unseen combinations of **already observed individual
context variants**.

It does not establish:

- recognition of a wholly unseen context variant;
- semantic equivalence of natural-language paraphrases;
- object or concept discovery in unrestricted experience;
- public reasoning-axis improvement;
- human-level or LLM-level intelligence.

## Next non-repetitive step

Do not increase the number of anchor variants or add another transformation.  The next
trial must address at least one of:

1. learn a representation that maps unseen surface contexts into an existing role class;
2. replace byte-exact context anchors with predictive context states;
3. use natural/public raw streams and prospective held-out contexts;
4. connect one frozen representation to multiple CAP-GEN public axes.
