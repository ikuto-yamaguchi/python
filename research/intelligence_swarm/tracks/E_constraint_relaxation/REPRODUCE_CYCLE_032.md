# Reproduce Cycle 032

```bash
python research/intelligence_swarm/tracks/E_constraint_relaxation/scope_gated_boundary_repair_cycle32.py \
  --output research/intelligence_swarm/tracks/E_constraint_relaxation/results_cycle_032.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction / independent probe / final test分離
- no repair / ungated / scope-gated / shuffled outcome ablation
- final test after/futureはcandidate生成・rankingに不使用
