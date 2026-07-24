# Reproduce Causal Grounding Cycle 006

```bash
python research/intelligence_swarm/tracks/C_causal_grounding/counterexample_born_commutator_cycle006.py \
  > research/intelligence_swarm/tracks/C_causal_grounding/MEASUREMENTS_CYCLE_006.json
```

Requirements:

- Python 3.10+
- NumPy
- External model/APIなし

Validation:

```bash
python -m py_compile research/intelligence_swarm/tracks/C_causal_grounding/counterexample_born_commutator_cycle006.py
```

実験はseed 1 / 7 / 19を固定して全方式・全domain・全表現条件を再実行する。
