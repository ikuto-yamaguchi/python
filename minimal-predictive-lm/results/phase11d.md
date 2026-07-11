# Phase 11d results: raw cross-modal primitive grounding and versioning

The learner receives raw Japanese, code diffs, tool traces, dialogue, and test
logs without task-family labels or pre-aligned StringTransformExample rows.

## Raw grounding

- observations: **8**
- channels: **5**
- discovered clusters: **2**
- cluster assignment accuracy: **100.0%**
- unrelated replacement clustered: **False**
- novel modality accuracy: **100.0%**

| cluster | primitive | support records | channels | bits |
|---|---|---:|---:|---:|
| P0 | offset -32 over 97–122 | 4 | 4 | 760 |
| P1 | offset 32 over 65–90 | 3 | 3 | 744 |

## Versioned residual repair

- Unicode accuracy before extension: **0.0%**
- Unicode extension accepted: **True**
- overbroad identity update rolled back: **True**
- learned context guard: **verbatim**
- context split accepted: **True**
- active version: **v3**
- final combined accuracy: **100.0%**

This removes task-family labels, but not all supervision: record boundaries,
quoted spans, channel metadata, and a bounded residual meta-grammar remain.

## Limitations

- individual message/log record boundaries and channel metadata are still supplied
- quoted or backticked spans provide a strong generic extraction cue
- the latent candidate language is limited to aligned codepoint offsets, residual replacements, and one lexical context guard
- the experiment contains only two reusable transformation clusters and one distractor
- Unicode residual corrections are exact replacements rather than a learned general Unicode case theory
- the context split relies on a repeated verbatim token and does not solve arbitrary pragmatic scope
- all evidence is synthetic and does not establish open-domain language grounding
