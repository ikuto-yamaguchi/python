# Phase 9a: Raw event grounding without persistent template IDs

## 1. Goal

Phase 8g proved that conversation, writing, code, and tool events can share one
small stochastic operation vocabulary, but every surface expression still had a
persistent template ID. Phase 9a removes that ID and asks whether raw Japanese,
AST-like strings, test output, and tool traces can be grounded into the same
operation program.

The target is not a bag of domain parsers. The target is one boundary:

```text
raw observation
    -> minimum grounding program
    -> SET / VERIFY / RETRACT / EMIT
    -> one sparse task state
```

This is still a synthetic experiment. It is not open-domain language
understanding.

## 2. Labels are obtained from effects

The learner is not given an intent name attached to each phrase. An interaction
trace contains a before state, an after state, and whether the event was an
observation, an emitted output, or a restoration.

```text
state changed                         -> SET
state unchanged + observation         -> VERIFY
previous state restored               -> RETRACT
output crossed the external boundary  -> EMIT
```

These four categories remain observable anchors. Discovering the anchors
jointly with language and hidden world state is a later problem.

## 3. Candidate feature universe

The raw string is NFKC-normalized. The learner creates only generic features:

- Japanese character n-grams of width 2--5
- ASCII words and character n-grams of width 3--6
- a small set of literal structural symbols such as `+`, `*`, and `=`

There is no operation-specific keyword table. Features such as `報告`, `tes`,
`tor`, or `更新` survive only if the observed interaction traces justify them.

## 4. Minimum stable cover

For operation `o`, let `P_o` be its positive examples. A feature is admissible
only when:

```text
support(feature, P_o) >= 2
contamination(feature, examples outside P_o) = 0
```

The feature cost is:

```text
C(f) = description_bits(f) + 64 / payload_length(f)^2
```

The second term is an explicit expected-collision proxy. Without it, very short
fragments are cheap to store but produce fragile accidental matches.

The implementation greedily chooses the feature with the largest newly covered
positive examples per unit cost until all training examples are covered. This is
a set-cover approximation, not a proof of the globally minimum feature set.

At runtime, matching feature payload lengths are added to each operation score.
A unique positive maximum is required. A tie returns `unknown`; it is not broken
by an arbitrary operation priority.

## 5. Why sharing can be smaller than domain separation

The shared learner sees that:

```text
Japanese request:   テストを実行して
AST-like text:      pytest Call
Tool result:        PASSED 2 tests
```

all have the same observed `VERIFY` effect. Evidence pooled across boundaries
can therefore justify one stable feature family and one operation schema.

A domain-separated design must pay for:

- four grounding programs
- duplicated operation schemas
- routing between runtimes
- serialized state hand-offs

In the experiment:

```text
shared grounding program: 1,412 bits
four domain models:        1,881 bits
```

The shared model is also more accurate on the near held-out set because the
`test` evidence is pooled across conversation, AST, and tool output.

## 6. Residual acquisition and retention

Distant lexical shifts cannot be inferred from string form alone. After eight
new interaction traces expose four new lexical roots, the model is re-induced:

```text
follow-up before: 0 / 8
follow-up after:  7 / 8
added program:    387 bits
```

The 387 bits are not automatically permanent. The residual program is retained
only when expected future avoided grounding loss, avoided clarification, and
avoided external lookup exceed its storage and checking cost.

This is the learning rule:

```text
keep residual structure only when lifetime value > lifetime cost
```

## 7. Shared repair workflow

A raw Japanese request is split into six clauses and grounded as:

```text
SET -> VERIFY -> RETRACT -> SET -> VERIFY -> EMIT
```

The first candidate `x + 1` fails the tests, the shared state records the
failure, rollback restores the baseline, the second candidate `x * x + 1`
passes, and a report is emitted.

The shared runtime keeps one state object. A modeled domain-separated pipeline
requires two hand-offs per event, twelve internal representation conversions,
and 6,704 copied bits for the concrete JSON state used in this experiment.
This is a measured implementation boundary, not a universal lower bound.

## 8. Important failure: one string can contain multiple events

The generated final report says both:

```text
作業結果を報告します
全テストに成功しました
```

It therefore contains an `EMIT` speech act and `VERIFY` content. The current
single-label grounder produces a tie. Five of six generated artifacts are
re-grounded correctly; the mixed report is deliberately left unresolved.

Adding `EMIT > VERIFY` as a fixed priority would improve this benchmark while
hiding the real representational error. The next design must represent:

```text
outer speech act: EMIT
embedded proposition: VERIFY(test_status = PASS)
```

rather than forcing the whole string into one class.

## 9. What Phase 9a establishes

Within the restricted world:

- persistent surface IDs are unnecessary for near compositional variants
- cross-domain effect sharing can improve both description length and accuracy
- a raw request can drive a rollback-and-repair loop through one state boundary
- residual lexical knowledge can be acquired and charged explicitly

It does not establish:

- synonym understanding without interaction evidence
- morphology or syntax induction
- semantic role discovery from arbitrary text
- real-repository coding ability
- ordinary open conversation

## 10. Next phase

Phase 9b should replace one-label grounding with a sparse event graph:

```text
speech act
propositions
conditions
causal links
references
```

It should induce clause boundaries and nesting from state effects, preserve
multiple simultaneous meanings, and charge every extra node and edge. The
first evaluation should include mixed reports, conditional requests, quoted
text, negation, and a real small repository repair task.
