# Phase 18d-3: latent task partition without task IDs

## Motivation

Phase 18d-1 still received explicit task episodes and opaque task IDs. That is not sufficient for LLM-like learning. Phase 18d-3 removes the task ID and declared task count.

## Setting

A shuffled stream contains supervised input/output records from several hidden deterministic programs. Numeric programs share the same two-number signature and field names; string programs share the same one-string signature. The learner:

1. enumerates short typed programs from the frozen Phase 18d-1 DSL,
2. records which stream examples each behavior explains,
3. deduplicates probe-equivalent behaviors,
4. finds the minimum-program, minimum-cost exact disjoint cover,
5. uses a local support input/output example—not a task name—to route held-out queries.

The hidden `gold` field is audit metadata only. Relabeling every audit field must leave the learned partition unchanged.

## Continual gate

After freezing the initial seven learned behaviors, five examples from one additional hidden behavior are appended in exactly the same record format. Repartitioning must discover one new behavior without changing old behavior fingerprints or source code.

## Negative controls

- fewer than five coherent examples cannot create a cluster,
- an uncovered contradictory outlier rejects the whole exact partition,
- a support example consistent with several learned behaviors causes abstention,
- stream order and audit labels are irrelevant.

## Claim boundary

This phase removes explicit task IDs in a controlled typed supervised stream. It does not remove supervised outputs, structured records, the human-designed type system, the fixed primitive DSL, the minimum-support hyperparameter, or the need for local support evidence at query time. It is not raw-text self-supervised pretraining or general intelligence.
