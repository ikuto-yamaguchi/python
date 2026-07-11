# Phase 10d: grounded external knowledge, provenance, contradiction, and abstention

## Goal

Language is useful because it transports observations and abstractions that the
agent did not experience directly. The concept-first architecture therefore must
accept textual knowledge without confusing the text itself with the world state.

Phase 10d represents an external statement as

```text
(subject, relation, value, source, provenance)
```

and keeps source trust separately. Contradictory claims are not overwritten.
They remain competing hypotheses whose evidence can be inspected and retracted.

## Source trust

For each source, calibration outcomes are summarized by two counters:

```text
(successes, failures)
```

With a Beta(1,1) prior, posterior reliability is

```text
(successes + 1) / (successes + failures + 2)
```

and evidence weight is the log odds

```text
log(p / (1 - p)).
```

The full calibration history is not needed for routine inference once the
sufficient statistics are established, although auditable provenance may be
retained outside the active state.

## Indexed retrieval

Claims are indexed by grounded concept key

```text
(relation, subject)
```

rather than scanned as raw documents for every query. This separates two costs:

1. building and maintaining the index,
2. reading evidence required by the current decision.

Index construction is not free and its bits are included in the static knowledge
cost.

## Contradiction

Claims with the same key and different values coexist. Their provenance and
weighted support are retained. The machine can therefore report disagreement,
change its answer when a source is corrected, or require more evidence.

A fluent generated sentence is never treated as stronger evidence than its source
claim. Generation is downstream of evidence selection.

## Abstention

The machine abstains when posterior confidence is below a required threshold.
This converts an always-answer accuracy metric into a selective-risk problem:

```text
quality = accuracy among answered queries
coverage = answered queries / all queries
```

Higher required confidence can increase selective accuracy while reducing
coverage. The threshold should be selected from decision loss, not to maximize a
single benchmark number.

## Adaptive evidence reading

Claims are read in descending learned reliability. After each read, the machine
computes a lower bound on the current leader's confidence under the worst case in
which all unread evidence supports the strongest competitor.

If even that worst case exceeds the confidence threshold, further reads cannot
change the decision under the bounded model and retrieval stops.

This is not a claim of optimal web search. It is an exact stopping condition for
the supplied finite evidence set and trust model.

## Experiment

- 400 supervised source-calibration outcomes
- four sources with different reliability
- 4,000 held-out claims
- 1,000 known subjects
- 100 unknown queries
- 700 subjects with contradictory claims

Policies compared:

1. scan every claim in the corpus,
2. read every indexed claim for the key,
3. read adaptively and abstain,
4. always answer after indexed exhaustive evidence.

The adaptive policy preserves the exhaustive abstaining policy's final selective
accuracy and coverage while reducing claim reads.

## Stage-C interpretation

This phase raises the synthetic knowledge evidence from level 1 to level 2 because
it tests held-out subjects, source shift, contradiction, and abstention. It does
not reach level 3 because:

- proposition extraction is bypassed,
- the corpus is synthetic,
- no public open-domain QA benchmark is used,
- source reliability is stationary,
- claims concern one relation.

## Next steps

1. extract propositions from raw documents into the shared event/concept graph,
2. preserve quoted spans and document offsets as provenance,
3. model time-dependent and topic-dependent source reliability,
4. detect copied sources so correlated evidence is not double-counted,
5. use VOI to choose additional documents, tools, or experiments,
6. evaluate on a public retrieval QA corpus with matched open-model baselines,
7. measure index bytes, peak RSS, latency, read bandwidth, and energy.
