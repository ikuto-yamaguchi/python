# Reproduce Cycle 010

```bash
python -m py_compile research/intelligence_swarm/tracks/A_semantic_identity/raw_character_class_birth_cycle010.py
python research/intelligence_swarm/tracks/A_semantic_identity/raw_character_class_birth_cycle010.py > measurements.json
```

## 条件

- Python 3.11+
- 標準ライブラリのみ
- seeds: 1, 7, 19
- final test afterをselection / candidate generation / rankingに使用しない
- fixed ontology / handwritten slot / string search / RAG / external LLMなし
- character-class oracleなし
- operation-familyとclass-cardinality oracleは残るため上限監査として扱う
