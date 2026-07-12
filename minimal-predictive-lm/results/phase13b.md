# Phase 13b results: induced generic expression and sequence algebra

One bounded algebra is induced from independent operator, precedence, and ordering interactions. The public benchmark supplies no calibration examples, task names, or item lexicon to the model.

## Anti-specialization checks

- fully public examples / axes: **200 / 5**
- exact calibration prompt overlap: **0**
- benchmark examples used for calibration: **0**
- benchmark-specific handlers / item lexicon entries: **0 / 0**
- generic operator programs: **8**
- algebra payload / combined payload: **1,149 / 2,041 bytes**
- cross-domain held-out transfer: **100.0%**

## Public accuracy before and after

| axis | frozen Phase 12 | Phase 13b algebra |
|---|---:|---:|
| boolean expressions | 0.0% | 100.0% |
| direct arithmetic | 100.0% | 100.0% |
| multistep arithmetic | 0.0% | 42.5% |
| object counting | 0.0% | 0.0% |
| word sorting | 0.0% | 100.0% |

Overall: **20.0% → 68.5%**

Coverage: **20.0% → 75.5%**

The multistep slice exposed a general unary-scope bug: expressions containing multiplication by a negative operand accounted for every failure except one correct case. This is repaired separately in Phase 13c rather than hidden inside the Phase 13b result.

## Claim boundary

This phase measures public transfer of a shared bounded algebra. It does not authorize parity with an open model or a general LLM. The generic tokenizer, parser, and comparator candidate families remain human-designed, and object counting still requires open-world category grounding.
