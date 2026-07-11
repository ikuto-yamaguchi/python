# Phase 11a results: domain-neutral typed program induction

The same learner is used without domain labels or handwritten task handlers.
New tasks are supplied only as transition traces.

## Architecture

- domain-specific handlers: **0**
- fixed primitives used: **8**
- novel tasks added with engine code changes: **0**
- learner source size: **17,518 bytes**

## Task results

| task | group | train | held-out | program bits | trace/program | candidates |
|---|---|---:|---:|---:|---:|---:|
| addition | base | 100.0% | 100.0% | 408 | 5.49x | 222 |
| subtraction | base | 100.0% | 100.0% | 408 | 5.55x | 222 |
| multiplication | base | 100.0% | 100.0% | 408 | 5.45x | 222 |
| concatenate | base | 100.0% | 100.0% | 432 | 6.85x | 357 |
| set_location | base | 100.0% | 100.0% | 696 | 6.20x | 338 |
| conditional_decision | base | 100.0% | 100.0% | 800 | 3.91x | 88 |
| increment_state | novel | 100.0% | 100.0% | 912 | 3.35x | 1,237 |
| remaining_inventory | novel | 100.0% | 100.0% | 552 | 5.07x | 29,965 |

## Aggregate

- expressible tasks: **8**
- all held-out tasks solved: **True**
- total learned programs: **4,616 bits**
- training-trace memorization: **22,984 bits**
- aggregate compression: **4.98x**
- total candidate evaluations: **32,651**

## Boundaries

- missing primitive detected: **True**
- depth-three search failure detected: **True**
- depth-three candidate budget: **20,000**

The result removes per-domain handwritten algorithms only for tasks expressible
in the current grammar and reachable within the search budget. It does not remove
grounding cost, induction search, or representation invention.

## Limitations

- the learner receives already structured arguments and before/after states
- task boundaries are supplied rather than discovered
- the grammar cannot invent a missing primitive such as uppercase
- a depth-three revenue program exhausts the bounded search budget
- balanced expression trees and reusable learned macros are not yet supported
- the experiment is synthetic and does not establish broad language-model scalability
- human effort moved from task algorithms toward data, grounding, and primitive design; it did not become zero
