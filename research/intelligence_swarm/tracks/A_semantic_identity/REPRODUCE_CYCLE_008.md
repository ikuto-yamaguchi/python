# Reproduce Cycle 008

```bash
python -m py_compile research/intelligence_swarm/tracks/A_semantic_identity/permutation_symmetry_identifiability_cycle008.py
python research/intelligence_swarm/tracks/A_semantic_identity/permutation_symmetry_identifiability_cycle008.py \
  > research/intelligence_swarm/tracks/A_semantic_identity/MEASUREMENTS_CYCLE_008.generated.json
```

## Environment

- Python 3.11+
- 標準ライブラリのみ
- 外部ネットワーク不要

## Expected checks

- `summary.chance == 0.125`
- `summary.zero_shot_mean` がchance近傍
- `summary.all_indistinguishable_pairs == true`
- calibration budget増加に伴い平均正答率が上昇
- `strict_progress_gate == false`
- `answer_leakage == false`
- `post_treatment_final_input == false`
