# Reproduce A Cycle 013

```bash
python3 research/intelligence_swarm/tracks/A_semantic_identity/transformation_indexed_equivariance_cycle013.py \
  > research/intelligence_swarm/tracks/A_semantic_identity/MEASUREMENTS_CYCLE_013.json
```

Python 3.11+、標準ライブラリのみ。seedは1, 7, 19で固定。

```bash
python3 -m py_compile research/intelligence_swarm/tracks/A_semantic_identity/transformation_indexed_equivariance_cycle013.py
python3 -m json.tool research/intelligence_swarm/tracks/A_semantic_identity/MEASUREMENTS_CYCLE_013.json >/dev/null
```
