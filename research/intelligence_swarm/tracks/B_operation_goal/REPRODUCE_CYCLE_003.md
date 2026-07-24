# Reproduce Operation/Goal Cycle 003

```bash
python research/intelligence_swarm/tracks/B_operation_goal/cross_domain_consequence_cycle003.py \
  > research/intelligence_swarm/tracks/B_operation_goal/MEASUREMENTS_CYCLE_003.json
```

- Python 3.11+
- NumPy
- seed: 1 / 7 / 19
- Consequence-invariant / raw-effect / shuffled-effect
- Held / 未知語順 / 入れ子 / 複数段落 / 自由日本語 / 目的変更 / 失敗修正 / cross-domain B/C
- テスト時はbefore + raw Japaneseのみ
- after、completed trajectory、domain辞書、shared object ID、RAG、外部LLM不使用
- joint chance 1/32、inverse chance 1/8
