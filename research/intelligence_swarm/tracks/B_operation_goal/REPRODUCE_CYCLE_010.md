# Reproduce B Operation / Goal Cycle 010

```bash
python3 research/intelligence_swarm/tracks/B_operation_goal/set_valued_operation_cycle010.py \
  > research/intelligence_swarm/tracks/B_operation_goal/MEASUREMENTS_CYCLE_010.json
python3 -m py_compile research/intelligence_swarm/tracks/B_operation_goal/set_valued_operation_cycle010.py
python3 -m json.tool research/intelligence_swarm/tracks/B_operation_goal/MEASUREMENTS_CYCLE_010.json >/dev/null
```

- Python 3.11+
- standard library only
- seeds: 1 / 7 / 19
- 2 opaque domains
- final test after is not used for candidate generation or ranking
