# Phase 15c results: shared event-sourced state runtime

Four raw formats compile into one initial-state / event-list / query-projection runtime. The runtime contains stack, vector, mapping, and partial-order state, while date understanding is intentionally left unsupported.

## Adaptation disclosure

- public surface formats inspected: **true**
- strict zero-shot claim: **false**
- human-designed surface compilers: **4**
- benchmark task-name branches: **0**
- shared runtime: **true**

## Shared runtime

- runtime payload: **223 bytes**
- runtime operations: `push`, `pop`, `turn`, `move_relative`, `move_absolute`, `swap`, `less`, `rank`
- cross-domain held-out: **8/8**

## Unseen public accuracy before and after

| axis | Phase 15b | Phase 15c | answered | wrong |
|---|---:|---:|---:|---:|
| date understanding | 0% | 0% | 0 | 0 |
| logical ordering | 0% | 100% | 40 | 0 |
| spatial navigation | 0% | 100% | 40 | 0 |
| stack completion | 0% | 100% | 40 | 0 |
| state permutation tracking | 0% | 100% | 40 | 0 |

Overall: **0% → 80%**. Answered/correct: **160/160**. The original Phase 14b public suite remains **200/200**.

## Claim boundary

This is benchmark-informed surface adaptation with a shared runtime. The four compilers were human-designed after the public formats were inspected, so this is not autonomous grammar induction or evidence of a general-purpose reasoning system.
