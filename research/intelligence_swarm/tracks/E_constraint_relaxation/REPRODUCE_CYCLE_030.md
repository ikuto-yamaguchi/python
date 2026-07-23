# Reproduce Cycle 030

```bash
python research/intelligence_swarm/tracks/E_constraint_relaxation/probe_nudged_boundary_cycle30.py \
  --output research/intelligence_swarm/tracks/E_constraint_relaxation/results_cycle_030.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction / independent probe / final testを分離
- ablation: no probe / correct probe / shuffled probe
- final test outcomeはrankingへ不使用
