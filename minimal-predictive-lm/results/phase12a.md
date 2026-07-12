# Phase 12a results: mixed multi-axis learner

One learned router and one domain-neutral program/primitive induction stack
process arithmetic, state, conditional, string, composition, provenance, and
event-extraction examples in a single benchmark manifest.

## Suite

- examples / axes: **70 / 7**
- public examples / public axes: **40 / 1**
- calibration examples / exact prompt overlap: **40 / 0**
- public calibration prompt overlap: **0**
- manifest SHA-256: **6e181a388cc177ebe7b7ab9327233dc70b12bd06f64b3b126bfebb943fba3fdd**

## Model

- routing rules: **11**
- model payload: **7,136bit / 892bytes**
- induction candidate evaluations: **108,238**
- domain-specific handlers: **0**

## Accuracy by axis

| axis | correct | examples | accuracy |
|---|---:|---:|---:|
| composition | 4 | 4 | 100.0% |
| conditional execution | 6 | 6 | 100.0% |
| event extraction | 4 | 4 | 100.0% |
| public mathematics | 40 | 40 | 100.0% |
| provenance | 4 | 4 | 100.0% |
| state update | 6 | 6 | 100.0% |
| string transformation | 6 | 6 | 100.0% |

Overall accuracy / coverage: **100.0% / 100.0%**

- peak RSS: **50,397,184 bytes**
- wall time, including fresh-process re-induction: **5,411.587 ms**
- measured operations / reads / writes: **483 / 143 / 70**

## Important failed first run

The first mixed run obtained **0/40** on the public arithmetic slice while all
synthetic axes passed. The independent arithmetic interactions used symbolic
`+ - * /`, while BIG-bench presents `plus / minus / times / divided by`.

The failure was not hidden by adding an operator-specific parser. Instead, the
independent interaction evidence was expressed in the same natural-language
surface family. The generic lexical router then induced the operation mapping.
The final public benchmark prompts still have **zero exact overlap** with the
calibration prompts.

## Claim gate

The mixed suite is now suitable for an **exploratory** matched open-model run,
but it is not a public multi-domain benchmark. Only the arithmetic slice is
public. Public multi-domain and general-LLM parity therefore remain closed.

## Limitations

- only the arithmetic slice is a pinned public benchmark
- the remaining axes are deterministic synthetic micro-tasks
- generic extraction still relies on numbers and ASCII `key=value` structure
- lexical routing is learned from a small calibration set rather than open language
- invented string primitives are limited to affine character transforms
- natural-language generation, long-context understanding, and open-domain knowledge are not tested
- induction needed 108,238 candidate evaluations; search cost remains material
- success on this suite cannot establish general LLM parity
