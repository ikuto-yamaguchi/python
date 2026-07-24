# Reproduce D Memory Eligibility Cycle 008

```bash
python -m py_compile research/intelligence_swarm/tracks/D_memory_eligibility/independent_witness_consensus_cycle008.py
python research/intelligence_swarm/tracks/D_memory_eligibility/independent_witness_consensus_cycle008.py \
  > research/intelligence_swarm/tracks/D_memory_eligibility/MEASUREMENTS_CYCLE_008.json
```

想定環境:

- Python 3.11+
- 標準ライブラリのみ
- seed: 1 / 7 / 19

監査項目:

1. 第一の3-witness集合が576 causal worldsを1へ縮約する
2. 第一集合と重複しない第二の3-witness集合も独立に同じworldへ縮約する
3. 第一集合の1 outcomeを破壊すると、正常第二集合との統合version spaceが空になる
4. 矛盾を既存identityへの上書きではなく取得競合として検出する
5. 正常第二集合からprospective / inverse / closed-loopを測定する

禁止事項:

- final test outcomeによるwitness選択
- hidden mappingの直接参照によるranking
- replay / fast weights / consolidationの開始
- G1/G2通過の主張
