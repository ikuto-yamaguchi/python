# Reproduce Causal Grounding Cycle 011

```bash
python3 research/intelligence_swarm/tracks/C_causal_grounding/state_crossing_operation_family_cycle011.py \
  > research/intelligence_swarm/tracks/C_causal_grounding/MEASUREMENTS_CYCLE_011.generated.json
python3 -m py_compile \
  research/intelligence_swarm/tracks/C_causal_grounding/state_crossing_operation_family_cycle011.py
```

Expected qualitative checks:

- Active reaches one surviving operation-program mapping for every seed.
- Random leaves multiple mappings for at least one seed.
- State-0-only witnesses retain the `constant-1` versus `negation` and `constant-0` versus `identity` aliases.
- Outcome-shuffled witnesses yield an empty or externally unusable version space.
- No final test outcome is used during witness selection or candidate ranking.
