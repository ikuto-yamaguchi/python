# Reproduce Cycle 041

```bash
python research/intelligence_swarm/tracks/C_causal_world/predictive_relation_axes_cycle41.py \
  --output research/intelligence_swarm/tracks/C_causal_world/MEASUREMENTS_CYCLE_041.json
```

- Python 3.11+
- 外部依存なし
- seed 1 / 7 / 19
- Literal / Rank-1 / Leave-one-world-out completion / Shuffled grouping
- 既知・未知語順・未知語彙・Rename・入れ子・主語省略・複数段落・計画変更・反実仮想
- final test after/futureはcandidate生成・rankingに不使用
- fixed ontology / handwritten slot / knowledge graph / RAG / external LLMなし
