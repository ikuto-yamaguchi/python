# Phase 10h results: public BIG-bench arithmetic baseline

Twenty public BIG-bench arithmetic subtasks are sampled deterministically
with ten examples per subtask. English operator words are grounded from ten
separate interactions that do not reuse benchmark examples.

## Benchmark

- examples / subtasks: **200 / 20**
- examples per subtask: **10**
- public / license: **True / Apache-2.0**
- manifest SHA-256: **cfd8bd98c597f5482df9724eb2750d293a443a1c6526630d4b0510a30723626d**

## Calibration

- independent interactions: **10**
- benchmark examples used: **0**

## MPM result

- correct / answered / total: **200 / 200 / 200**
- overall accuracy: **100.000%**
- coverage: **100.000%**
- model program bytes: **53**
- peak RSS: **41,672,704 bytes**
- wall time: **134.091 ms**
- feature reads / operations: **3,800 / 4,200**

## Comparison status

- matched open model executed: **False**
- parity claim allowed: **False**

This isolates the narrow public domain in which a compiled concept program
may be competitive. It does not repair the 0% GSM8K result.

## Limitations

- the subset is the first ten examples from each of twenty public arithmetic subtasks
- the English operator grounding uses ten independent calibration interactions
- the benchmark measures direct binary arithmetic rather than natural-language word-problem reasoning
- no matched open model has been executed yet
- energy is not measured
