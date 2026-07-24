# Reproduce Cycle 041

```bash
python research/intelligence_swarm/tracks/D_memory_learning/interference_assembly_memory_cycle41.py \
  --output research/intelligence_swarm/tracks/D_memory_learning/MEASUREMENTS_CYCLE_041.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- Base / Interference assembly / Slow assembly / Shuffled assembly
- 既知・未知語順・Rename・別状態表現・入れ子・主語省略・複数段落・自由日本語
- final test outcomeは候補生成・rankingに不使用
- fixed ontology / handwritten slot / vector DB / RAG / external LLMなし
