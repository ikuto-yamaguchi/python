# Phase 11e results: continuous mixed-stream event induction

The learner receives one continuous mixed-style stream without record objects,
task-family labels, channel metadata, quotes, or backticks.

## Event and role induction

- inferred / expected events: **6 / 6**
- event precision / recall: **100.0% / 100.0%**
- candidate pair evaluations: **31**
- unrelated distractor ignored: **True**

## Shared primitive induction

- clusters: **2**
- event coverage: **100.0%**
- domain-specific parsers added: **0**

| cluster | interval | offset | support | bits |
|---|---:|---:|---:|---:|
| S0 | 65–90 | 32 | 3 | 744 |
| S1 | 97–122 | -32 | 3 | 760 |

## Unseen continuous stream

- events: **3**
- event precision / recall: **100.0% / 100.0%**
- primitive-cluster assignment: **100.0%**
- engine code changes: **0**

## LLM comparison gate

- narrow matched comparison already available: **True**
- multi-domain LLM parity ready: **False**

This removes supplied record and channel labels, but punctuation, a bounded role
cue inventory, ASCII identifiers, and a fixed offset transformation family remain.

## Limitations

- generic punctuation and line breaks still act as strong event-boundary cues
- role induction uses a bounded multilingual cue inventory for result, condition, and provenance
- candidate source and target values are restricted to nearby ASCII identifier-like tokens
- the transformation family remains constant codepoint offsets
- streams are synthetic and short
- the experiment does not establish public multi-domain or general LLM parity
