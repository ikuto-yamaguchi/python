# Reproduce Cycle 031

```bash
python research/intelligence_swarm/tracks/C_causal_world/target_boundary_competition_cycle31.py \
  --output research/intelligence_swarm/tracks/C_causal_world/MEASUREMENTS_CYCLE_031.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction 190 / independent probe 98 / final test別seed
- target after/futureはcandidate生成・rankingに不使用
- `python -m py_compile research/intelligence_swarm/tracks/C_causal_world/target_boundary_competition_cycle31.py` 成功
