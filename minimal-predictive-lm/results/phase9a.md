# Phase 9a results: raw event grounding and shared repair workflow

Persistent template IDs are removed. Raw Japanese, AST-like text, test output,
and tool traces are mapped into one `SET / VERIFY / RETRACT / EMIT` event program.

## Raw grounding

- training examples: **34**
- selected feature rules: **15**
- shared grounding program: **1,412 bits**
- exact-surface near-heldout: **0.0%**
- sparse raw grounder near-heldout: **100.0%**
- distant lexical shift: **6.2%**

## Shared versus domain-separated grounding

| model | description bits | near-heldout |
|---|---:|---:|
| shared event grounding | 1,412 | 100.0% |
| four domain models | 1,881 | 94.4% |

The separated description is **1.33x** the shared description.

## Residual lexical calibration

- calibration interactions: **8**
- follow-up before calibration: **0.0%**
- follow-up after calibration: **87.5%**
- added program: **387 bits**

The added lexical program is not automatically permanent. It must repay its bits
through future avoided errors or avoided external queries.

## End-to-end repair workflow

- induced plan: `SET → VERIFY → RETRACT → SET → VERIFY → EMIT`
- request-clause grounding: **100.0%**
- generated AST/test/tool/report grounding: **83.3%**
- final expression: `x * x + 1`
- final test: **PASS**
- rollback actions: **1**
- shared internal representation conversions: **0**
- domain-separated conversions: **12**
- concrete JSON hand-off copies: **6,704 bits/workflow**

The final report contains both an `EMIT` speech act and `VERIFY` content. The
single-label grounder ties instead of hiding the ambiguity with a priority rule.

## Limitations

- effect traces still identify whether an event wrote, observed, restored, or emitted
- near paraphrases share subword evidence with training
- distant lexical shifts remain mostly unresolved without new interaction evidence
- the workflow is a synthetic one-function repair rather than a real repository
- the feature learner does not yet discover morphology, syntax, or world knowledge
