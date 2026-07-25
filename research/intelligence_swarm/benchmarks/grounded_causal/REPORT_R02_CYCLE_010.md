# R0.2 Environment-first Baseline — Cycle 010

## Scope

This cycle adds no operation/goal toy hypothesis and no new architecture family. It advances the faithful Gaddy & Klein 2019 transfer by removing the concrete dataset-schema blocker identified in Cycles 008–009.

Canonical branch: `research/intelligence-swarm-reconstruction-001`.

## Completed work

Added `export_silg_typed_policy_trajectories.py`, a separate typed SILG/RTFM trajectory adapter.

The legacy exporter flattened all non-language tensors into one float vector. That destroyed field boundaries and forced an invalid uniform MSE over categorical IDs, binary masks and coordinates. The new adapter preserves:

- `state_before_fields`
- `state_after_fields`
- `state_schema`
- categorical field cardinalities derived from public environment metadata
- binary semantics for `valid`
- continuous semantics for `rel_pos`
- canonical action label
- language tokens
- episode, seed, split and observation provenance
- dataset and schema SHA-256

Reward, termination, episode return, episode step and previous action are excluded from state inputs. They remain labels/provenance only. The adapter validates field width, categorical range and binary values and rejects any categorical field whose cardinality cannot be derived without inspecting evaluation rows.

## Why this is separate

The active R0.1 131,072-frame source-policy workflow is still in its official recurrent training step. The existing workflow watches `export_silg_policy_trajectories.py`; modifying that file would cancel and restart the long run. The typed exporter was therefore added under a new path not currently watched by the workflow. This preserves the active run while making the faithful typed data path ready for the next completed checkpoint.

## Fixed method contract

The downstream `gaddy_klein_typed_baseline.py` continues to require:

- language-free transition pretraining
- 20 categorical message variables × 30 symbols
- straight-through Gumbel-Softmax
- shared typed next-state/action decoder
- LSTM language encoder
- direct environment/language message alignment with weight 0.01
- decoder frozen during language training by default
- categorical CE, binary BCE and continuous MSE
- seeds 1, 7 and 19
- episode-disjoint train/test data
- parameter, data, split and resource accounting

No result is recognized until the typed exporter is executed against a completed, competent R0.1 checkpoint and online task success plus real held-out entity/dynamics/language-form transfer are measured.

## Remaining blockers

1. Complete the active 131,072-frame R0.1 source-policy run.
2. Verify source-policy task success and action anti-collapse for all three seeds.
3. Execute the typed exporter for seeds 1, 7 and 19.
4. Replace the legacy exporter invocation in the workflow only after the active run artifact is collected.
5. Define real entity and dynamics holdouts from public RTFM generation metadata; current boolean placeholders are not evidence.
6. Run Environment-first, parameter-matched End-to-end and State-only under identical data/splits.
7. Add online task-success evaluation and CPU latency/model/RSS/wall-time audit.

## Classification

`typed_export_path_implemented_source_policy_and_holdout_execution_blocked`

- formal R0.2 reproduction: incomplete
- capability progress: not recognized
- novelty: not established
- intelligence principle: none
- high-school-level intelligence: not achieved
