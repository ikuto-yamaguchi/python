# Phase 13d results: generic quantified reduction with semantic abstention

A generic quantifier extracts variable-length owned-item sequences, grounds quantity words, and reduces a query only when its concept membership is identifiable. No benchmark item-category dictionary is added.

## Anti-specialization checks

- independent quantity groundings: **12**
- induced universal concepts: **`objects`**
- public-worker membership entries: **0**
- benchmark-specific handlers / item lexicon: **0 / 0**
- exact calibration prompt overlap: **0**
- quantifier payload: **228 bytes**

## Public accuracy before and after

| axis | Phase 13c | Phase 13d |
|---|---:|---:|
| boolean expressions | 100.0% | 100.0% |
| direct arithmetic | 100.0% | 100.0% |
| multistep arithmetic | 100.0% | 100.0% |
| object counting | 0.0% | 30.0% |
| word sorting | 100.0% | 100.0% |

Overall: **80.0% → 86.0%**

Object counting correct / wrong / answered: **12 / 0 / 12**

Answered query concepts: **`objects` only**

## Information boundary

For an ungrounded category, the inferred count interval is **[0, 6]** and the model abstains. Syntax determines the quantities, but membership such as `apple ∈ fruit` is additional information.

## Claim boundary

This phase demonstrates generic quantified reduction and calibrated semantic abstention. It deliberately does not copy the benchmark's fruit, animal, vegetable, or instrument vocabulary and therefore does not solve open-world concept acquisition or establish LLM parity.
