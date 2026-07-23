# Reproduce Cycle 033

```bash
cd research/intelligence_swarm/tracks/C_causal_world
python boundary_faithful_mechanism_cycle33.py
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- induction / independent probe / final test分離
- Surface / Minimal-support / Shuffled-probe / Family-removal ablation
- final testのafter/futureはfamily形成・rankingに不使用
