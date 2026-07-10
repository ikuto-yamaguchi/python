# Phase 6a results: scaling and lower-bound audit

This audit separates static program bits, active state bits, evidence reads,
and unavoidable sequential work. It does not claim that universality alone
produces an efficient intelligent system.

## Chain: flat ground rules versus a factorized transition

| length | state lower bound | flat program bits | factorized bits | required steps | compression |
|---:|---:|---:|---:|---:|---:|
| 8 | 4 | 88 | 33 | 8 | 2.67x |
| 16 | 5 | 208 | 35 | 16 | 5.94x |
| 32 | 6 | 480 | 37 | 32 | 12.97x |
| 64 | 7 | 1088 | 39 | 64 | 27.90x |
| 128 | 8 | 2432 | 41 | 128 | 59.32x |
| 256 | 9 | 5376 | 43 | 256 | 125.02x |

The factorized machine reaches the exact active-state lower bound, while
the flat ground program grows with every edge. The traversal still needs
one dependent step per edge: compression does not make an inherently
sequential computation constant-time.

## Boolean functions: arbitrary table versus parity

| input bits | arbitrary-map lower bits | parity program bits | active bits | required reads | compression |
|---:|---:|---:|---:|---:|---:|
| 8 | 256 | 25 | 1 | 8 | 10.24x |
| 12 | 4,096 | 25 | 1 | 12 | 163.84x |
| 16 | 65,536 | 27 | 1 | 16 | 2427.26x |
| 20 | 1,048,576 | 27 | 1 | 20 | 38836.15x |

Parity has a short algorithm and one-bit state, but every independent input
bit must still be observed. An arbitrary mapping has no assumed structure and
retains its table-sized information lower bound.

## Repeated reachability query: workload-specific storage

| queries | on demand | memo one query | full closure |
|---:|---:|---:|---:|
| 1 | 1,792 | 1,793 | 2,977 |
| 4 | 4,480 | 1,796 | 2,980 |
| 16 | 15,232 | 1,808 | 2,992 |
| 100 | 90,496 | 1,892 | 3,076 |

The best representation depends on the deployment distribution. A universal
full closure is wasteful when one endpoint query repeats; a single verified
memo is smaller. With a different query distribution, the crossover changes.

## Consequence for open-ended intelligence

The scalable target is not one fixed table. It is a compiler that detects
reusable structure, keeps active state near distinguishability lower bounds,
reads only evidence that can affect the result, and specializes storage and
indexes to the measured workload. Truly unstructured knowledge must still be
stored or reacquired, and irreducibly dependent reasoning steps must still run.
