# Reproduce D Memory Eligibility Cycle 001

## Requirements

- Python 3.11+
- external dependencyなし

## Run

```bash
python research/intelligence_swarm/tracks/D_memory_eligibility/symmetry_breaking_eligibility_cycle001.py \
  --output research/intelligence_swarm/tracks/D_memory_eligibility/MEASUREMENTS_CYCLE_001.json
```

## Syntax check

```bash
python -m py_compile \
  research/intelligence_swarm/tracks/D_memory_eligibility/symmetry_breaking_eligibility_cycle001.py
```

## Fixed conditions

- seeds: 1, 7, 19
- behaviorally identical twin pairs: 24
- objects: 48
- held-out surface forms: 5 Japanese paraphrase templates
- domain transforms: 90/180/270 degree sensor-frame rotations
- interference: 96 behavior-equivalent identity-distinct records
- no string retrieval
- no fixed ontology
- no handwritten semantic slot
- no RAG / external LLM
- final identity is used only for evaluation
