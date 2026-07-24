# Reproduce Cycle 004

```bash
python research/intelligence_swarm/tracks/B_operation_goal/cross_lexicon_selective_consequence_cycle004.py \
  > research/intelligence_swarm/tracks/B_operation_goal/MEASUREMENTS_CYCLE_004.json
```

- Python 3.11+ / NumPy
- seed: 1, 7, 19
- 完全語彙非共有domain D/E/F
- Full / Consensus / Shuffled consensus
- held / 未知語順 / 自由日本語 / goal変更 / failure repair
- test時after・完成trajectory不使用
- domain辞書、shared ID、手書きslot、固定ontology、RAG、外部LLMなし
