# Phase 1 results: mathematical state lower bounds

The experiment deliberately starts with processes whose minimum predictive state is known.
A finite Hankel rank identifies the minimum *linear* predictive dimension; exact future-distribution
equivalence then crystallizes that dense representation into an O(1) causal-state table.

| case | true states | Hankel rank | causal states | dense bytes | table bytes | dense state bits | table state bits | dense MAC/symbol | table MAC/symbol |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| iid | 1 | 1 | 1 | 16 | 4 | 32 | 0 | 1 | 0 |
| modulo-2 | 2 | 2 | 2 | 48 | 12 | 64 | 1 | 4 | 0 |
| modulo-3 | 3 | 3 | 3 | 96 | 18 | 96 | 2 | 9 | 0 |
| modulo-4 | 4 | 4 | 4 | 160 | 24 | 128 | 2 | 16 | 0 |
| modulo-5 | 5 | 5 | 5 | 240 | 30 | 160 | 3 | 25 | 0 |
| modulo-6 | 6 | 6 | 6 | 336 | 36 | 192 | 3 | 36 | 0 |
| modulo-7 | 7 | 7 | 7 | 448 | 42 | 224 | 3 | 49 | 0 |
| modulo-8 | 8 | 8 | 8 | 576 | 48 | 256 | 3 | 64 | 0 |

All exact reconstruction errors were below 1e-10 over every binary word up to length 9.
The table figures use FP16 probabilities and the minimum whole-byte state index.
Runtime state bits report the mathematical state requirement separately from model storage.

## Trial-and-error finding: rank selection

For a true rank-5 process with 100,000 sampled prefixes:

- largest-singular-gap heuristic: **rank 1** (failed)
- split-noise operator threshold: **rank 5** (recovered)
- estimated operator-norm noise floor: `0.0071023`

The failure occurs because the normalization/mean component dominates the first singular value.
Comparing two independent empirical Hankel matrices estimates noise directly and avoids treating
that dominant component as the meaningful model-order gap.

## Current interpretation

Minimum predictive dimension is not yet minimum compute. Spectral factorization discovers the
dimension, but its arbitrary dense basis costs r^2 MACs per symbol. Causal-state crystallization
changes coordinates to a discrete state ID, reaching zero MACs and two table reads per symbol on
these finite processes. The next phase is to preserve this event-driven table core while adding
a sparse residual memory only when prediction surprise proves that the finite state is insufficient.
