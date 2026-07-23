# Reproduce Cycle 026

```bash
python research/intelligence_swarm/tracks/C_causal_world/success_conditioned_event_identity_cycle26.py \
  --output research/intelligence_swarm/tracks/C_causal_world/results_cycle_026.json
```

- Python 3.11+
- 外部依存なし
- seed: 1 / 7 / 19
- train sizes: 48 / 144 / 288
- 学習器はraw `before / command / after / future`と環境IDのみ使用
- hidden object・field・old/new labelは評価器のみ使用
