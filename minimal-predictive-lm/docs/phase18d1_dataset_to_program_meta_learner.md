# Phase 18d-1: dataset-to-program meta-learner

## Motivation

A system that requires a human to add one parser, relation, or solver at a time is not a practical intelligence. Phase 18d-1 changes the main gate: after the learner is frozen, new task families must be learnable from datasets alone, with zero task-specific source changes.

## Frozen substrate

The learner receives an opaque task id and structured input/output demonstrations. It enumerates short typed programs over one frozen DSL:

- numbers: negation, absolute value, add, subtract, multiply, divide, min, max;
- booleans: not, and, or, xor;
- numeric lists: length, sum, min, max, reverse, sort;
- strings: length, concatenate, upper, lower, reverse.

Programs are searched by increasing description length. All minimum-cost programs that fit the demonstrations are compared on a deterministic probe set. If multiple probe-distinct behaviors remain, the learner abstains instead of choosing one arbitrarily.

## Freeze protocol

Five development tasks are learned first. The learner source is then treated as frozen. Eleven further tasks are supplied only through `data/phase18d1_meta_tasks.json`, and one additional task is constructed at runtime. Task ids and input field names are opaque and absent from task-specific dispatch.

The CI requires:

- all development, post-freeze, and runtime-added held-out cases to be correct;
- zero source changes per post-freeze task;
- variable renaming and example-order invariance;
- old learned programs to remain unchanged after later learning;
- ambiguity, conflicting labels, and tasks outside the DSL to abstain.

## Claim boundary

This is a real correction away from hand-adding one solver per task, but it is not yet LLM-like learning. The type system, primitive DSL, episode boundary, task identity, and structured input/output representation are human-designed. The learner selects and composes existing primitives; it does not yet invent arbitrary new primitives, discover tasks from a raw stream, learn free language, acquire open-world knowledge, or reach high-school intelligence.

The next gate is data-driven library growth: repeated learned subprograms must become reusable primitives without human source edits, while held-out tasks test whether the new library reduces examples and search cost without corrupting old behavior.
