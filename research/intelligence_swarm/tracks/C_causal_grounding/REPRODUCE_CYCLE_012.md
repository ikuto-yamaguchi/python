# Reproduce C Cycle 012

```bash
python3 research/intelligence_swarm/tracks/C_causal_grounding/scope_arity_state_crossing_cycle012.py \
  > research/intelligence_swarm/tracks/C_causal_grounding/MEASUREMENTS_CYCLE_012.json
```

Python 3.11+、標準ライブラリのみ。

```bash
python3 -m py_compile research/intelligence_swarm/tracks/C_causal_grounding/scope_arity_state_crossing_cycle012.py
python3 research/intelligence_swarm/tracks/C_causal_grounding/scope_arity_state_crossing_cycle012.py >/tmp/c_cycle012.json
python3 -m json.tool /tmp/c_cycle012.json >/dev/null
```
