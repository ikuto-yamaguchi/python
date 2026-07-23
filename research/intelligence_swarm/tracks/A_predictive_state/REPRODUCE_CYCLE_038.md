# Reproduce Cycle 038

```bash
python research/intelligence_swarm/tracks/A_predictive_state/sensor_causal_state_cycle38.py \
  --output research/intelligence_swarm/tracks/A_predictive_state/MEASUREMENTS_CYCLE_038.json
```

- Python 3.11+
- 外部依存なし
- seed 1 / 7 / 19
- Separated / Object-target birth / Selective-lesion causal / Shuffled object residual
- 既知・未知語順・未知語彙・入れ子・主語省略・複数段落・計画変更・反実仮想
- final test after/futureはcandidate生成・rankingに不使用
- fixed ontology / handwritten slot / classifier / dictionary / RAG / external LLMなし
