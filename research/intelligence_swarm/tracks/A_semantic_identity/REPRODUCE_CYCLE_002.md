# Reproduce A Semantic Identity Cycle 002

```bash
python research/intelligence_swarm/tracks/A_semantic_identity/pre_treatment_relational_change_cycle002.py \
  > research/intelligence_swarm/tracks/A_semantic_identity/MEASUREMENTS_CYCLE_002.generated.json
```

## Environment

- Python 3.11+
- standard library only
- seeds: 1, 7, 19
- no network access required

## Expected headline values

Small runtime variation is expected. Accuracy values are deterministic for the listed seeds.

- held joint: Correct 0.070833 / Shuffle 0.045833
- rename joint: 0.050000 / 0.033333
- word-order joint: 0.045833 / 0.041667
- omission joint: 0.054167 / 0.012500
- paragraph joint: 0.079167 / 0.041667
- free Japanese joint: 0.037500 / 0.029167
- domain joint: 0.062500 / 0.062500
- relation lesion target: 0.000000
- matrix: 32,768 bytes

## Leakage checks

The script reports all of the following as false:

- post-treatment observation used at test
- final test outcome used for training
- identity label used in training
- span boundary generation
- string retrieval
