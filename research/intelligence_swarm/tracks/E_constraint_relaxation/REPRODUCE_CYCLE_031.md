# Reproduce Cycle 031

```bash
python research/intelligence_swarm/tracks/E_constraint_relaxation/counterexample_boundary_expansion_cycle31.py \
  --output research/intelligence_swarm/tracks/E_constraint_relaxation/results_cycle_031.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction / independent probe / final test分離
- no residual / correct residual / shuffled residual ablation
- final test outcomeはcandidate生成・rankingに使用しない
