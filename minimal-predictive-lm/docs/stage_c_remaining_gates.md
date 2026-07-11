# Stage-C remaining evidence gates

## Current evidence state

The readiness score is evidence maturity, not percentage intelligence.

| axis | current level | evidence |
|---|---:|---|
| conversation | 2 | held-out interaction adaptation, but distant free language remains weak |
| knowledge | 2 | synthetic raw-document extraction, contradiction, provenance, correlation, abstention, and VOI |
| mathematics | 2 | induced one-step arithmetic programs with shifted lexical calibration |
| code | 1 | synthetic one-function repair with test and rollback |
| long context | 1 | synthetic state-retention and indexed retrieval |
| creative writing | 0 | no blind open-ended quality evidence |

Current total: **8 / 24**.

## First narrow comparison against an open model

A fair axis-specific comparison becomes possible after three mandatory gates:

1. run a public benchmark from raw inputs without benchmark-specific answer leakage,
2. measure quality and resources together: model/program bytes, peak RSS, reads, operations, wall time, and energy where available,
3. run at least one small open model on exactly the same inputs, tools, stopping rules, and metric.

This can happen on one axis before the complete Stage-C system exists. Knowledge or mathematics is the shortest route because both are currently level 2.

## Meaningful multi-axis comparison

A useful comparison to a general small language model needs at least:

- public conversation or instruction following,
- public knowledge or retrieval QA,
- public mathematics,
- a real repository code benchmark,
- open long-context evaluation,
- one blind writing-quality evaluation,
- matched resource instrumentation across all runs.

Reaching public evidence on every axis means a minimum score of **18 / 24**. The current gap is **10 evidence points**.

## Full Stage C

Full Stage C requires every axis at level 4:

- public open-domain evidence,
- matched inputs and tools,
- quality at or above the selected open model,
- a resource Pareto comparison rather than quality alone.

The current gap is **16 evidence points**. This should not be interpreted as sixteen routine implementation tasks. One representation or learning breakthrough can raise several axes, while a failed public benchmark can reveal that an entire architecture needs revision.

## Planned gate order

1. benchmark and resource-measurement harness,
2. public retrieval/knowledge evaluation,
3. multi-step mathematics and public math evaluation,
4. small real-repository repair benchmark,
5. long-document state construction and public long-context evaluation,
6. freer dialogue grounding and public instruction-following evaluation,
7. constrained and open creative-writing evaluation with blind judging,
8. matched SmolLM/Qwen-class baseline runs,
9. Pareto analysis and failure-driven redesign,
10. only then a parity or superiority claim.

## Honest estimate in milestones

- **First narrow open-model comparison:** three mandatory gates remain.
- **Credible multi-axis comparison:** roughly six capability gates plus the shared measurement harness remain.
- **Full Stage C:** at least ten public-evidence upgrades and six matched parity tests remain from the present score.

These are milestone counts, not calendar estimates. The open research risk is dominated by free-language grounding, candidate generation, and broad compositional generalization rather than by test harness implementation.
