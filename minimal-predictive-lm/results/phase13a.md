# Phase 13a results: frozen public multi-domain baseline

The Phase 12 model is frozen before seeing a fully public five-axis suite. Benchmark task names are used only by the scorer; the model receives raw prompts.

## Suite and anti-specialization checks

- public examples / axes: **200 / 5**
- exact calibration prompt overlap: **0**
- model fingerprint unchanged: **True**
- benchmark-specific handlers / primitives / calibration examples: **0 / 0 / 0**
- compiled payload: **7,136bit / 892bytes**
- manifest SHA-256: **e54edfb0054f950f1752be7d9738249fbf75874738f69966051816a66614f8db**

## Accuracy by public axis

| axis | correct | answered | examples | accuracy | coverage |
|---|---:|---:|---:|---:|---:|
| boolean expressions | 0 | 0 | 40 | 0.0% | 0.0% |
| direct arithmetic | 40 | 40 | 40 | 100.0% | 100.0% |
| multistep arithmetic | 0 | 0 | 40 | 0.0% | 0.0% |
| object counting | 0 | 0 | 40 | 0.0% | 0.0% |
| word sorting | 0 | 0 | 40 | 0.0% | 0.0% |

Overall accuracy / coverage: **20.0% / 20.0%**

Non-arithmetic accuracy: **0.0%**

The model made **zero wrong answers**: 40 correct direct-arithmetic answers and 160 explicit abstentions. This is useful calibration evidence, but not general capability.

## Resources

- model bytes: **892**
- peak RSS: **50,487,296 bytes**
- wall time including fresh-process re-induction: **5,499.036 ms**
- operations / reads / writes: **260 / 100 / 40**

## Claim gate

This is a valid frozen public baseline, not a parity result. Public multi-domain quality parity, runtime Pareto, and general LLM parity remain closed until a matched open-model run and non-benchmark-specific improvement are demonstrated.

## Capability gaps

- **boolean expressions**: recursive symbolic composition and precedence
- **direct arithmetic**: single-step lexical operation grounding
- **multistep arithmetic**: nested program parsing and execution
- **object counting**: entity selection, number-word grounding, and aggregation
- **word sorting**: variable-length sequence extraction and ordering

## Limitations

- the frozen model was calibrated on forty Phase 12 interactions rather than pretrained on open language
- direct arithmetic is represented in calibration while the four BBH capabilities are not
- the baseline intentionally does not learn from benchmark examples
- task axes are used only for evaluation and failure analysis, never for routing or execution
- no open-model comparison is included in Phase 13a
- natural-language generation, coding, long context, and open-domain knowledge remain untested
