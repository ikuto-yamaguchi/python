# Phase 13c results: generic unary-scope correction

Failure diagnostics showed that multiplication followed by a negative operand was the common structural failure. Five independent interactions distinguish prefix unary scope from binary precedence; no benchmark example is used.

## Anti-specialization checks

- independent scope interactions: **5**
- exact benchmark prompt overlap: **0**
- benchmark examples used for calibration: **0**
- benchmark-specific handlers / grammar rules: **0 / 0**
- induced precedence: **`*=2, neg=2, +=1, -=1`** with unary right-associativity

## Public accuracy before and after

| axis | Phase 13b | Phase 13c |
|---|---:|---:|
| boolean expressions | 100.0% | 100.0% |
| direct arithmetic | 100.0% | 100.0% |
| multistep arithmetic | 42.5% | 100.0% |
| object counting | 0.0% | 0.0% |
| word sorting | 100.0% | 100.0% |

Overall: **68.5% → 80.0%**

Coverage: **75.5% → 80.0%**

Multistep wrong / abstained: **0 / 0**

## Claim boundary

This is a generic grammar correction inside a bounded algebra, not evidence of open-ended representation learning or parity with an LLM. The remaining object-counting gap requires lexical-semantic category knowledge that is not identifiable from syntax alone.
