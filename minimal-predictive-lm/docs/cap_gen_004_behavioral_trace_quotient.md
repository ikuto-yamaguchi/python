# CAP-GEN-004-BTQ-001: Behavioral Trace Quotient

## Purpose

The goal is a tiny learner that acquires reusable executable knowledge across heterogeneous domains. Unlike earlier validity gates, BTQ-001 must improve an actual capability: knowledge learned from string and integer-list programs must reduce synthesis cost in a held-out grid DSL while preserving exact solutions and unseen-example accuracy.

## Prior-art boundary

Program-library learning, DreamCoder, AbstractBeam, ReGAL, neural algorithmic reasoning, and trace-based synthesis are prior art. The unverified novelty candidate is narrower: quotient programs by source-agnostic execution-trace control structure, promote only templates independently supported by source-incompatible domains, then use that library to prune a new DSL before solving tasks in it.

## Hypothesis

Programs with unrelated syntax and data types may share a control skeleton. A trace template is represented as:

```text
prefix + motif^k + suffix
```

Source tokens, DSL names, task IDs, and domain names are excluded. A template enters the library only after support from at least two domains.

## Frozen experiment

Training domains are strings and integer tuples. The held-out domain is two-dimensional integer grids. The training solutions share zero source bigrams across domains but induce three common templates:

1. scan until a predicate succeeds, then emit the remainder;
2. read from the back and write;
3. read, apply a local operation, and write.

The grid DSL has 70 candidates. The learned library retains 22. Six held-out grid tasks must select the same exact solution under cold and guided search and achieve 100% accuracy on unseen examples.

## Resource accounting

Cold target search costs `70 x 3 x 6 = 1260` candidate executions.

Guided search charges target indexing and verification:

```text
index:        70 x 2 = 140
verification: 22 x 3 x 6 = 396
incremental total = 536
```

Charging training-domain search and trace extraction gives:

```text
training search = 369
trace extraction = 18
full total = 369 + 18 + 536 = 923
surplus = 1260 - 923 = 337
```

Code size, interpreter cost, peak memory, and natural-data acquisition remain uncharged.

## Falsification controls

The gate fails if source syntax explains transfer, a template has only one-domain support, guided search removes the exact program, unseen accuracy is below 100%, fully charged search is not cheaper, or an unseen skeleton such as transpose is falsely claimed.

## Claim boundary

BTQ-001 demonstrates a finite capability improvement: source-incompatible solved programs induce a behavioral library that transfers to a new representation domain and reduces fully charged search. It is not raw-stream learning, a public benchmark result, publication-level novelty, natural-language understanding, or evidence of human-level general intelligence.

The next gate must use a public dataset, noisy or partial traces, unseen compositions, or an induced trace alphabet. Adding more hand-written programs to these same DSLs is not research progress.
