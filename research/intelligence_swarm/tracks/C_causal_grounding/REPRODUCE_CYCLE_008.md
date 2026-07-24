# Reproduce Causal Grounding Cycle 008

## Environment

- Python 3.11+
- NumPy
- Linux/macOS/WSL

## Run

```bash
python research/intelligence_swarm/tracks/C_causal_grounding/structure_expanding_residual_birth_cycle008.py \
  > /tmp/c_cycle008.json
```

## Syntax check

```bash
python -m py_compile \
  research/intelligence_swarm/tracks/C_causal_grounding/structure_expanding_residual_birth_cycle008.py
```

## Expected audit fields

- `seeds`: `[1, 7, 19]`
- `summary.base`
- `summary.weight`
- `summary.expand`
- `summary.shuffle`
- `strict_gate_by_seed`: all false in the recorded run
- `answer_leakage`: false
- `post_treatment_test_input`: false
- `fixed_ontology`: false

The compact recorded result is stored in `MEASUREMENTS_CYCLE_008.json`.
