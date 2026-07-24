# Reproduce A Cycle 011

```bash
python3 research/intelligence_swarm/tracks/A_semantic_identity/nonparametric_alias_role_inventory_cycle011.py \
  > research/intelligence_swarm/tracks/A_semantic_identity/MEASUREMENTS_CYCLE_011.json
```

Requirements:

- Python 3.11+
- standard library only
- deterministic seeds: 1, 7, 19

Validation:

```bash
python3 -m py_compile research/intelligence_swarm/tracks/A_semantic_identity/nonparametric_alias_role_inventory_cycle011.py
python3 research/intelligence_swarm/tracks/A_semantic_identity/nonparametric_alias_role_inventory_cycle011.py >/tmp/a_cycle011.json
python3 -m json.tool /tmp/a_cycle011.json >/dev/null
```
