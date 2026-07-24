# Reproduce Cycle 009

```bash
python -m py_compile research/intelligence_swarm/tracks/C_causal_grounding/joint_orbit_identifiability_cycle009.py

python research/intelligence_swarm/tracks/C_causal_grounding/joint_orbit_identifiability_cycle009.py \
  --output research/intelligence_swarm/tracks/C_causal_grounding/MEASUREMENTS_CYCLE_009.json
```

## Environment

- Python 3.11+
- Standard library only
- Seeds: 1, 7, 19
- No network access required

## Leakage rules

- final test outcome is not used for witness selection
- only calibration witness outcomes update the version space
- outcome-shuffle explicitly destroys query/result correspondence
- no domain dictionary, shared object ID, RAG, or external LLM
