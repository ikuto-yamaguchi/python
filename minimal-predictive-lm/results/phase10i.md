# Phase 10i results: matched SmolLM2 comparison

MPM and SmolLM2-135M-Instruct receive the same pinned public benchmark,
the same ten independent operator-grounding examples, output limit, no-tool
policy, deterministic decoding policy, scorer, and fresh-process resource
instrumentation.

## Benchmark and calibration

- name / examples: **bigbench-arithmetic / 200**
- manifest SHA-256: **cfd8bd98c597f5482df9724eb2750d293a443a1c6526630d4b0510a30723626d**
- public / license: **True / Apache-2.0**
- calibration examples / benchmark overlap: **10 / 0**
- calibration evidence matched: **True**

## Results

| system | accuracy | coverage | model bytes | peak RSS | wall time |
|---|---:|---:|---:|---:|---:|
| MPM | 100.000% | 100.000% | 53 | 41,754,624 | 131.393 ms |
| SmolLM2-135M-Instruct | 9.000% | 100.000% | 538,060,032 | 1,423,654,912 | 114790.750 ms |

## Fairness and claim gates

- fairness violations: **[]**
- narrow quality parity allowed: **True**
- narrow runtime Pareto allowed: **True**
- lifetime Pareto allowed: **False**
- general LLM parity allowed: **False**
- accuracy delta, MPM − SmolLM2: **91.000%**
- model-byte ratio, SmolLM2 / MPM: **10,152,076.08x**
- peak-RSS ratio: **34.10x**
- wall-time ratio: **873.65x**

The measured runtime Pareto result is valid only for this pinned reference
implementation and direct-arithmetic subset. It is not a lower bound on an
optimized SmolLM2 implementation: shared-prefix KV-cache reuse was not used.
Lifetime cost and general language-model parity remain unproven, and MPM
remains at 0% on GSM8K.

## Model metadata

- model: `HuggingFaceTB/SmolLM2-135M-Instruct`
- revision: `12fd25f77366fa6b3b4b768ec3050bf629380bac`
- torch: `2.7.1+cpu`
- transformers: `4.53.2`
- same calibration examples: **10**
- input / output tokens: **53,595 / 649**

## Limitations

- the comparison covers direct binary arithmetic rather than broad language intelligence
- both systems receive the same ten independent operator-grounding examples, but MPM compiles them once while SmolLM2 rereads them in context
- SmolLM2 runtime parameter bytes are measured after float32 loading, not compressed on-disk checkpoint bytes
- MPM model bytes count the induced executable program while peak RSS includes the Python runtime for both systems
- operation counts are unavailable for SmolLM2 and are excluded from the runtime Pareto gate
- training and induction costs are not available in one comparable lifetime ledger
- the reference SmolLM2 runner does not implement shared-prefix KV-cache reuse across independent benchmark questions
- energy is not measured
- the 0% GSM8K result remains the relevant evidence for multi-step word-problem reasoning
