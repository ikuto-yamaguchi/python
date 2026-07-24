# Reproduce B Operation/Goal Cycle 002

```bash
python research/intelligence_swarm/tracks/B_operation_goal/four_way_factorized_operation_cycle002.py \
  > research/intelligence_swarm/tracks/B_operation_goal/MEASUREMENTS_CYCLE_002.json
```

依存:
- Python 3.11+
- NumPy

条件:
- seed 1 / 7 / 19
- Shared / Factorized / Contrast-channel shuffle / No-direction
- Held / Rename / 未知語順 / 入れ子 / 複数段落 / 自由日本語 / 別領域
- 32候補 target×move prospective
- 4候補 inverse
- goal変更
- failure repair
- テスト時post-treatment featureなし
- answer leakageなし
