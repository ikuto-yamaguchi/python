# Reproduce C Cycle 013

```bash
python3 research/intelligence_swarm/tracks/C_causal_grounding/cross_expression_paired_repair_cycle013.py \
  > research/intelligence_swarm/tracks/C_causal_grounding/MEASUREMENTS_CYCLE_013.json
```

Validation:

```bash
python3 -m py_compile research/intelligence_swarm/tracks/C_causal_grounding/cross_expression_paired_repair_cycle013.py
python3 research/intelligence_swarm/tracks/C_causal_grounding/cross_expression_paired_repair_cycle013.py >/tmp/c_cycle013.json
python3 -m json.tool /tmp/c_cycle013.json >/dev/null
```

Python 3.11+ standard library only. Seeds: 1, 7, 19.
