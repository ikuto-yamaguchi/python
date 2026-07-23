# Reproduce Cycle 032

```bash
python research/intelligence_swarm/tracks/C_causal_world/mechanism_family_equivalence_cycle32.py \
  --output research/intelligence_swarm/tracks/C_causal_world/MEASUREMENTS_CYCLE_032.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction 48 / independent probe 24 / final test 12件×10条件
- Surface / Family / Family graph / Shuffled-probe ablation
- Final test outcomeはfamily形成・rankingに使用しない
- `python -m py_compile research/intelligence_swarm/tracks/C_causal_world/mechanism_family_equivalence_cycle32.py` で構文確認
