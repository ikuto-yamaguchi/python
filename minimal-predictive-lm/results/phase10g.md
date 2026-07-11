# Phase 10g results: public GSM8K baseline

The official GSM8K test split is downloaded from the OpenAI repository,
verified against a pinned Git blob SHA, and passed to the model without
targets or benchmark-specific tools.

## Benchmark

- examples: **1,319**
- public: **True**
- license: **MIT**
- source Git blob: **e4c2ff4942b9a78bd74f04141224c11e28d12dc9**
- manifest SHA-256: **b5491642f1c55e30fb3b15053b0fd944f3a88bf4b6d5fc6af40c1b2a553e9b0f**

## MPM result

- correct / answered / total: **0 / 30 / 1319**
- overall accuracy: **0.000%**
- selective accuracy: **0.000%**
- coverage: **2.274%**
- model program bytes: **116**
- peak RSS: **43,495,424 bytes**
- wall time: **279.509 ms**
- CPU time: **584.662 ms**
- feature reads / operations: **270,553 / 272,035**

## Stage-C evidence

- readiness points: **8 → 9 / 24**
- mathematics level: **2 → 3**
- matched open model executed: **False**
- parity claim allowed: **False**

Level 3 records public evidence maturity, not high performance. A poor
score is retained as the baseline that the next multi-step representation
must improve.

## Limitations

- the current MPM math system only induces five one-step binary arithmetic programs
- GSM8K requires multi-step linguistic and arithmetic reasoning
- the system is evaluated zero-shot without benchmark-specific training
- no calculator or external tool is allowed in this run
- energy is not measured
- public evidence maturity increases even if task accuracy is low; this is not a capability claim
