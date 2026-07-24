# Reproduce D Cycle 009

```bash
python research/intelligence_swarm/tracks/D_memory_eligibility/independent_witness_local_syntax_cycle009.py \
  > research/intelligence_swarm/tracks/D_memory_eligibility/MEASUREMENTS_CYCLE_009.full.json
```

Python 3.11 standard library only. Expected seeds are 1, 7, 19. Confirm `upper_bound_reconvergence_seeds == 3`, `formal_memory_eligible_units == 0`, conflict detection 1.0, and memory optimization disabled.
