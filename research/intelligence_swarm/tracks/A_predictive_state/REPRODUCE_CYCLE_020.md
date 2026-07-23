# Reproduce Cycle 020

```bash
python research/intelligence_swarm/tracks/A_predictive_state/surprise_sync_cycle20.py \
  --output research/intelligence_swarm/tracks/A_predictive_state/results_cycle_020.json
python -m py_compile research/intelligence_swarm/tracks/A_predictive_state/surprise_sync_cycle20.py
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- train sizes: 24 / 72 / 144
- learner input: raw before / command / after / future strings
- hidden object/value labels: evaluator only
