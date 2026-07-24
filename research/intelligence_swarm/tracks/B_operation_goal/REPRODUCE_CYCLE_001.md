# Reproduce B Operation/Goal Cycle 001

```bash
python research/intelligence_swarm/tracks/B_operation_goal/witness_conditioned_operation_cycle001.py \
  > research/intelligence_swarm/tracks/B_operation_goal/MEASUREMENTS_CYCLE_001.json
```

- Python 3.11+
- 外部依存なし
- seed 1 / 7 / 19
- Correct pairing / episode-level shuffled pairing
- prospective / inverse / goal change / failure repair
- held paraphrase / rename / 未知語順 / 入れ子 / 複数段落 / 自由日本語 / 別領域
- operation ID、goal slot、identity labelはモデルへ不使用
- span proposal、文字列retrieval、RAG、外部LLMなし
- final test outcomeは学習に不使用
