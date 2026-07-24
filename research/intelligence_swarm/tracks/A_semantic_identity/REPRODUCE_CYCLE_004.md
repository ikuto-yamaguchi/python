# Reproduce Cycle 004

```bash
python -m py_compile selective_consequence_consensus_cycle004.py
python selective_consequence_consensus_cycle004.py > MEASUREMENTS_CYCLE_004.json
```

- Python 3.11+
- NumPy
- Seed: 1 / 7 / 19
- 外部ネットワーク・外部LLM不要
- 実行時に正解afterを入力しない
- test outcomeを学習・rankingへ使用しない
