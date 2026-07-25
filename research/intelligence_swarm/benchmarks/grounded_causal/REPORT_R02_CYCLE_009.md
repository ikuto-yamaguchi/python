# R0.2 Cycle 009 — typed structured-message baseline implementation

## Scope

This cycle adds no operation/goal toy hypothesis and no new architecture family. It implements the fixed Gaddy & Klein 2019 method contract on the canonical reconstruction branch, while refusing to treat the existing flattened SILG trajectory export as valid typed transition data.

Method reference remains the authors' public implementation at commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`.

## Completed implementation

Added `gaddy_klein_typed_baseline.py` with:

1. language-free transition pretraining from `(state_before_fields, state_after_fields)`;
2. a structured discrete message with 20 categorical variables and 30 symbols per variable;
3. straight-through Gumbel-Softmax sampling;
4. a shared typed decoder for next-state fields and low-level action;
5. an LSTM language encoder connected to the same message space;
6. direct symmetric message-distribution matching with weight `0.01`;
7. decoder freezing during language training by default;
8. field-specific losses:
   - categorical: cross entropy,
   - binary: binary cross entropy,
   - continuous: mean squared error;
9. canonical seed enforcement for `1, 7, 19`;
10. train/test episode-disjointness checking;
11. dataset SHA-256, parameter bytes, training wall time and peak RSS output.

The implementation rejects legacy rows containing only flattened `state_before` and `state_after`. It requires:

- `state_before_fields`
- `state_after_fields`
- `state_schema`

This fail-closed behavior is intentional. Treating categorical IDs, binary masks and continuous quantities as one float vector with a single MSE is not a faithful next-state objective.

## Not yet completed

The new entry point has not been executed in this cycle because the active 131,072-frame R0.1 workflow is still training and its current exporter writes only flattened state vectors. Updating that exporter while the run is active would launch another duplicate long workflow.

The following remain mandatory before this can be classified as a formal R0.2 reproduction:

- typed SILG trajectory export preserving field boundaries and cardinalities;
- three completed canonical-seed datasets from a competent, non-collapsed R0.1 policy;
- topology- and parameter-matched end-to-end control;
- state-only control;
- equal train examples, epochs and splits;
- online task-success evaluation in SILG;
- action accuracy and typed next-state metrics;
- real held-out entity, dynamics and language-form splits;
- CPU inference latency;
- raw logs, model files, dependency freeze and full checksums;
- fidelity-audit pass.

## Classification

`typed_discrete_message_method_path_implemented_dataset_and_online_evaluation_blocked`

This is implementation progress only. It is not evidence of task capability, novelty, an intelligence principle or high-school-level intelligence.
