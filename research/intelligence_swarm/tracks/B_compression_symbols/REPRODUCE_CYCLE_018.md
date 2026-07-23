# Reproduce Cycle 018

```bash
python research/intelligence_swarm/tracks/B_compression_symbols/counterexample_exception_cover_cycle18.py \
  --output research/intelligence_swarm/tracks/B_compression_symbols/results_cycle_018_full.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- train sizes: 48 / 144 / 432
- test: 120 examples / split / seed

構文検証:

```bash
python -m py_compile research/intelligence_swarm/tracks/B_compression_symbols/counterexample_exception_cover_cycle18.py
```

同じseedで再実行し、accuracy、candidate execution recall、wrong commit、program数、description bits、exception bitsが一致することを確認する。
