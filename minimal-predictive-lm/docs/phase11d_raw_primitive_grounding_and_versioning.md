# Phase 11d: raw primitive grounding and versioned representation repair

## Motivation

Phase 11c could invent a compact string primitive from aligned input/output examples,
but the examples already declared their task family and source/target boundaries. That
is not a scalable learning interface. A broadly useful learner must discover that raw
Japanese messages, code diffs, tool traces, dialogue records, and test logs can require
the same latent computation without receiving one manually designed solver per domain.

Phase 11d removes the task-family labels and pre-built `StringTransformExample` rows.
The learner receives ordinary log/message records plus coarse channel metadata.
Individual record boundaries remain supplied.

## Generic raw evidence extraction

The current extractor recognizes generic quoted spans:

- `"..."`
- `'...'`
- `` `...` ``
- `「...」`

It preserves textual order and enumerates possible earlier-to-later span pairs inside
each record. It does not use labels such as `uppercase`, `lowercase`, `inventory`, or
`repository`.

For equal-length candidate pairs it summarizes the residual by the changed codepoints.
If all changed positions share one offset, the record contributes evidence for a latent
conditional affine primitive:

```text
if lower <= codepoint <= upper:
    codepoint += offset
```

Evidence is grouped by offset across records. A cluster is retained only when it has
support from multiple records and multiple channels. Repeated observations in one
record cannot create support by themselves. Unrelated replacements do not form an
affine residual cluster.

The normalized experimental score is:

```text
support * evidence_value
- primitive_description_bits
- false_pair_matches * false_match_cost
```

The coefficients are explicit experimental accounting constants, not a claim that a
CPU operation is physically equal to one information bit.

## Cross-modal clustering result

Eight raw records from five channels were provided:

- four lowercase-to-uppercase records
- three uppercase-to-lowercase records
- one unrelated replacement distractor

The learner discovered two clusters without task-family labels:

```text
P0: codepoint 97..122, offset -32
P1: codepoint 65..90, offset +32
```

The first cluster was supported by Japanese, code diff, test log, and tool trace records.
The second was supported by code diff, dialogue, and tool trace records. Cluster
assignment was 100%, the distractor remained unclustered, and the first primitive
transferred to previously unseen sensor and repository channels with 100% accuracy.

This is evidence for cross-domain reuse, but the records are synthetic and the quoted
spans are a strong structural cue.

## Versioned representation repair

A learned primitive must not be silently overwritten whenever new evidence arrives.
Phase 11d therefore stores parent-linked versions and stages every candidate before
activation.

### Version 1: shared ASCII offset

The initial active primitive is the raw cross-channel cluster:

```text
ASCII lowercase -> uppercase by offset -32
```

It scores 0% on `café déjà vu` and `straße`.

### Version 2: residual extension

The learner applies the active primitive, compares its output with new evidence, and
extracts the remaining edit spans. It proposed exact residual replacements:

```text
é -> É
à -> À
ß -> SS
```

The composite candidate preserved the old evidence and raised combined accuracy to
100%. Its normalized lifetime gain was positive, so version 2 was committed with a
parent link to version 1.

This is not a general theory of Unicode casing. It is a bounded residual extension and
must be reported as such.

### Rejected overbroad update

When records requiring unchanged lowercase text appeared, replacing the active
primitive with global identity was considered. On the combined evidence its accuracy
fell from 75% to 25%, so the candidate was rejected and the active version remained
unchanged. The rejection is recorded as a rollback decision.

### Version 3: context-conditioned split

The conflicting records shared the context token `verbatim`, which did not occur in the
successful transformation records. The learner proposed a guarded split:

```text
if context contains "verbatim":
    return input unchanged
else:
    apply version 2
```

This restored 100% accuracy on old, Unicode, and verbatim evidence and was committed as
version 3.

## Why this matters for scalability

The engine did not receive a Japanese solver, code-diff solver, tool solver, and test-log
solver. The same residual representation was induced across all channels, reused on a
new modality, and repaired through a common versioning mechanism.

This is the intended scaling direction:

```text
raw evidence
-> candidate state/argument spans
-> shared residual signature
-> cross-channel concept cluster
-> reusable primitive
-> versioned validation and rollback
```

The human engineering cost should move toward one generic learner rather than one
implementation per subject area.

## Remaining supervision and limits

Phase 11d is not open-ended grounding.

- message/log record boundaries are supplied
- coarse channel metadata is supplied
- quoted or backticked spans strongly expose candidate values
- the proposal language is limited to codepoint offsets, exact residual replacements,
  and one lexical context guard
- only two reusable clusters and one distractor are tested
- exact Unicode replacements can memorize exceptions
- the learned `verbatim` guard does not solve arbitrary pragmatic scope
- the evidence is synthetic

## Next phase

Phase 11e should weaken the remaining structural supervision:

1. segment continuous mixed streams into candidate events
2. infer source, result, condition, and provenance roles without quote dependence
3. align language, code, state change, and tool effects through causal consistency
4. compare joint grounding against separate per-channel parsers
5. measure how candidate search and human code changes scale as channels and tasks grow
6. split, merge, retire, or roll back primitive versions under distribution drift

A successful result must improve held-out behavior while keeping domain-specific engine
changes at zero. Synthetic accuracy alone must not increase the Stage-C score.
