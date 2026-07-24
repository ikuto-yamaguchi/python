# Reproduce D Cycle 010

```bash
python research/intelligence_swarm/tracks/D_memory_eligibility/state_crossing_reconvergence_cycle010.py
```

Expected checks:

- Python standard library only
- seeds: 1, 7, 19
- `active_same_unique` is 1 for all seeds
- active prospective/program mapping are 1.0
- state-static survivor count remains 4.0 on average
- conflict union has zero survivors for all seeds
- `formal_memory_eligible_units` remains 0 because token boundary, binary interface, unary scope and finite operation family are oracle-provided

The script overwrites only `MEASUREMENTS_CYCLE_010.json` in the same track directory. Final test outcomes are not used for witness selection or candidate ranking.
