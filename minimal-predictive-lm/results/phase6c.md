# Phase 6c results: local optimum versus lifetime global optimum

This experiment compares four ideas that are often conflated:

- memorize exact cases
- duplicate a small program per task
- synthesize one shared rule plus exact exceptions
- begin locally and migrate later

All reported costs include stored representation and the declared discovery or migration costs.

## Horizon-dependent winner

| queries per task | exact cache | duplicated program | shared hybrid | winner |
|---:|---:|---:|---:|---|
| 2 | 2,048 | 2,672 | 2,240 | exact_cache |
| 4 | 4,096 | 2,928 | 2,496 | shared_hybrid |
| 8 | 8,192 | 3,440 | 3,008 | shared_hybrid |
| 16 | 16,384 | 4,464 | 4,032 | shared_hybrid |
| 32 | 32,768 | 6,512 | 6,080 | shared_hybrid |
| 64 | 65,536 | 10,608 | 10,176 | shared_hybrid |

## Sixteen-query deployment

- myopic commit to exact caches: **16,384 cost units**
- re-optimize after committing: **7,152**
- select over the whole deployment distribution: **4,032**
- local/global ratio: **4.063x**

The rolling policy recovers the better representation but pays to read and rewrite the old cache.
Reversible early choices reduce this tax; irreversible local compilation increases it.

## Held-out tasks

For 32 unseen affine tasks with 16 queries each, exact caching costs **8,192 bits**,
while reusing the shared schema requires **320 bits** of new task parameters.
The ratio is **25.6x**.

## Interpretation

The globally selected machine is not a single universal representation chosen forever.
At two queries per task, exact caching is cheapest because rule discovery has not paid back.
At four or more queries, the shared rule plus exceptions wins. Therefore the optimizer must
select over workload, horizon, uncertainty, migration cost, and held-out transfer—not merely
minimize the cost of the current episode.

A local optimization is admissible only when it is either reversible or certified not to
increase the best known lower-bounded lifetime objective.
