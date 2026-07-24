# Reproduce D Memory Eligibility Cycle 003

```bash
python research/intelligence_swarm/tracks/D_memory_eligibility/factorized_memory_eligibility_cycle003.py > research/intelligence_swarm/tracks/D_memory_eligibility/MEASUREMENTS_CYCLE_003.json
```

Python 3.11+、外部依存なし。seedは1、7、19。介入後trajectory、scar、正解after、identity/operation label、span proposal、文字列retrieval、RAG、外部LLMは使用しない。

期待確認:

- `strict_seed_passes == 0`
- `semantic_memory_eligible_units == 0`
- heldではCorrect jointがshuffleを弱く上回る
- domainではCorrect jointがshuffleを上回らない
