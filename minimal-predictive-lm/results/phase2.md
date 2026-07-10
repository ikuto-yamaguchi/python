# Phase 2 results: factor the transition law, not only the state

A K-bit key-value memory has 2^K predictively distinguishable assignments.
Any exact predictor therefore needs at least K runtime bits. A flat causal-state
implementation meets that runtime-state bound with a state ID, but its transition
program still grows exponentially. The factored register machine stores K bits
and uses indexed read/write rules whose description length is constant in 2^K.

| K | lower bound bits | factored data bits | total runtime bits | flat ready states | flat sparse table bytes | factored parameter bytes | dense/factored write traffic |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 4 | 2 | 64 | 10 | 208x |
| 2 | 2 | 2 | 6 | 4 | 208 | 10 | 416x |
| 4 | 4 | 4 | 9 | 16 | 1472 | 10 | 832x |
| 8 | 8 | 8 | 14 | 256 | 55040 | 10 | 1664x |
| 16 | 16 | 16 | 23 | 65536 | 32636928 | 10 | 3328x |
| 32 | 32 | 32 | 40 | 4294967296 | 5600637353984 | 10 | 6656x |

With write/query/filler probabilities 0.4/0.4/0.2, the factored machine
touches only 0.153846 data bits per token for writes and the same for reads.
A dense FP32 K-dimensional recurrent state writes 32K bits every token.

## Lower-bound argument

For any two different memory assignments m and m', there is a key j where
their bits differ. The observed suffix `QUERY KEY_j` makes the next token
deterministically BIT_0 under one history and BIT_1 under the other. Therefore
the histories are in different predictive equivalence classes. There are 2^K
classes, so at least log2(2^K)=K state bits are required. The register machine
uses exactly K data bits and reaches this lower bound.

## Consequence

Minimizing causal-state count or Hankel rank alone is insufficient. The objective
must also penalize the description length of the transition law and dynamic memory
traffic. Compositional addressable memory can be exponentially smaller than a flat
table even when both have the same information-theoretic runtime-state requirement.
