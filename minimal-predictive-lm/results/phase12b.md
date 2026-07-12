# Phase 12b results: exploratory mixed-suite SmolLM2 comparison

The same 70 prompts, output policy, scorer, and forty prompt-output
demonstrations are used for MPM and SmolLM2-135M-Instruct. The result is
exploratory because the suite is not fully public and state calibration
observability is not structurally identical.

## Overall

| system | accuracy | coverage | model bytes | peak RSS | wall time |
|---|---:|---:|---:|---:|---:|
| MPM | 100.0% | 100.0% | 892 | 50,737,152 | 4,328.707 ms |
| SmolLM2 | 35.7% | 100.0% | 538,060,032 | 1,856,081,920 | 174,367.688 ms |

The measured ratios are approximately **603,206×** in loaded model bytes,
**36.58×** in peak RSS, and **40.28×** in wall time. These are descriptive
measurements, not an authorized Pareto claim.

## Accuracy by axis

| axis | MPM | SmolLM2 | delta |
|---|---:|---:|---:|
| composition | 100.0% | 25.0% | +75.0% |
| conditional execution | 100.0% | 50.0% | +50.0% |
| event extraction | 100.0% | 100.0% | 0.0% |
| public mathematics | 100.0% | 32.5% | +67.5% |
| provenance | 100.0% | 100.0% | 0.0% |
| state update | 100.0% | 0.0% | +100.0% |
| string transformation | 100.0% | 0.0% | +100.0% |

SmolLM2 processed **76,862 input tokens** and emitted 609 output tokens. MPM
compiled the forty interactions into an 892-byte routing/program payload. MPM's
reported wall time includes fresh-process re-induction.

## Claim gate

- benchmark fully public: **False**
- prompt-output calibration count matched: **True**
- structured state-transition observability matched: **False**
- strict parity claim allowed: **False**
- runtime Pareto claim allowed: **False**
- public multi-domain parity allowed: **False**
- general LLM parity allowed: **False**

The explicit fairness violations are:

1. `benchmark_not_public`
2. `mixed_suite_not_fully_public`
3. `calibration_observability_mismatch_on_state_transition`

## Limitations

- six of seven axes are deterministic synthetic micro-tasks
- MPM sees structured state-transition evidence for state calibration while SmolLM2 sees prompt-output demonstrations
- SmolLM2 rereads all forty demonstrations for every query while MPM compiles them once
- shared-prefix KV-cache reuse is not implemented for the SmolLM2 reference runner
- model parameter bytes are measured after float32 loading
- training, induction, and pretraining costs are not in one lifetime ledger
- energy is not measured
- the run cannot authorize public multi-domain or general LLM parity
