# Reproduce Cycle 033

```bash
python research/intelligence_swarm/tracks/B_compression_symbols/scope_compressed_symbol_productions_cycle33.py \
  --output research/intelligence_swarm/tracks/B_compression_symbols/MEASUREMENTS_CYCLE_033.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction 190 / independent probe 98 / final test別seed
- Graph / Global repair / Scoped repair / Shuffled scoped ablation
- Final test after/futureはscope生成・rankingに使用しない
