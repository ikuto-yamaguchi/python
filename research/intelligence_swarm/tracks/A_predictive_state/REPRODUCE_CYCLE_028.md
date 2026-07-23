# Reproduce Cycle 028

```bash
cd research/intelligence_swarm/tracks/A_predictive_state
python cross_encoded_residual_routing_cycle28.py --output results_cycle_028.json
```

- Python 3.11+
- 外部依存なし
- seed 1 / 7 / 19
- Transformer / attention / RAG / external LLMなし
- current-turn after/futureはroute選択に未使用
- direct lexical overlapはroute scoreに未使用
