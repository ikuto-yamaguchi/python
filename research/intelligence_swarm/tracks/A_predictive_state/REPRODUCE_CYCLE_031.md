# Reproduce Cycle 031

```bash
python research/intelligence_swarm/tracks/A_predictive_state/probe_grounded_operator_birth_cycle31.py \
  --output research/intelligence_swarm/tracks/A_predictive_state/MEASUREMENTS_CYCLE_031.json
```

- Python 3.11+
- 外部依存なし
- seeds: 1 / 7 / 19
- induction / independent probe / final test分離
- Family / Carry / Correct probe / Shuffled probe比較
- final test outcomeは候補生成・rankingに不使用
- `python -m py_compile` 成功
