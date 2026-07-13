# Phase 18b-1: Text-only question answering with verified traces

## Question

Phase 18a-7 executes a bracketed recursive discourse when the initial state is
passed as a separate Python argument. Phase 18b-1 asks whether the initial
state, recursive procedure, and query can be supplied in one text string and
whether every answer can be accompanied by a derivation that an independent
checker replays.

This is the first explicit question-answer gate. It remains a controlled
state-tracking task rather than general Japanese mathematics.

## Input representation

Each problem contains exactly three top-level bracketed blocks:

```text
最初の値【アキ=1、ボブ=2、チカ=3、ダイ=4、エリ=5、フミ=6】。
実行する手順【続いて【...】【...】】。
最後に答える対象【ダイ】。
```

The surrounding labels vary. They are not listed in the parser. Block roles
are inferred from their contents:

- a complete set of entity-to-integer assignments;
- one valid recursive Phase 18a-7 program;
- one known entity used as the query target.

No initial-state tuple or query index is passed outside the text.

## Solution and trace

A solution contains:

```text
integer answer
ordered trace steps
```

Trace steps record sequence order, condition values and selected branch,
subtree suppression, resolved event roles, copied value, and overwritten
value. The solver and verifier use different execution functions.

The verifier parses the original problem, consumes the proposed trace one
step at a time, independently reconstructs every expected transition, and
accepts only when:

1. every trace step matches;
2. no extra or missing step remains;
3. the replayed final state yields the submitted answer.

A correct final integer with an empty, tampered, or inconsistent trace is
rejected.

## Frozen evaluation

- 72 calibration problem strings derived from the noisy Phase 18a-7 training
  family;
- 12 held-out recursive problems;
- unseen complete problem strings;
- varied outer labels;
- integer initial values embedded in text;
- one queried entity per problem.

For each held-out problem, the evaluation also searches for a one-coordinate
initial-state intervention that changes the answer or the verified trace.
This guards against a solver that emits an invariant canned explanation.

## Falsification gates

The campaign fails unless:

1. text-only answer accuracy and coverage are both 100%;
2. every answer trace is independently replayed successfully;
3. whole-problem memorization has zero held-out coverage;
4. returning the queried initial value without execution scores below 50%;
5. empty traces are rejected;
6. a single altered event value in the trace is rejected;
7. a wrong answer attached to an otherwise valid trace is rejected;
8. every problem has at least one verified one-coordinate counterfactual that
   changes its answer or trace;
9. trace length remains bounded by the number of executed control and event
   nodes.

## Resource accounting

The learned payload includes the Phase 18a-7 semantic factors, outer block
role schema, and trace schema. The report separately records serialized
held-out solutions and traces. Python, the fixed block parser, and verifier
source are excluded from learned payload and reported separately.

## Claim boundary

Passing Phase 18b-1 demonstrates controlled text-only state questions with
machine-checkable derivations. It does not establish:

- natural unbracketed Japanese word-problem parsing;
- arithmetic operation induction;
- algebra, geometry, statistics, or proof;
- factual reading comprehension;
- Japanese high-school-level intelligence.

The next mathematics gate should replace copy-only state transitions with
induced integer operations and evaluate unseen multi-step arithmetic word
problems under the same trace-verification discipline.
