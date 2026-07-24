# Reproduce Causal Grounding Cycle 003

```bash
python3 research/intelligence_swarm/tracks/C_causal_grounding/transformation_equivariant_grounding_cycle003.py \
  > research/intelligence_swarm/tracks/C_causal_grounding/MEASUREMENTS_CYCLE_003.generated.json
```

## Environment

- Python 3.11+
- standard library only
- seeds: 1, 7, 19
- no network access required

## Compared conditions

- Equivariant candidate-centered relation representation
- Absolute coordinate and object-index representation
- Shuffled Japanese-to-world pairing

## Test conditions

- held paraphrase
- rotation
- translation
- object permutation
- plan cancellation / counterfactual order
- free Japanese
- disjoint-domain vocabulary

## Leakage audit

- test after / completed trajectory / scar are not inputs
- final outcome is not used for training or ranking
- identity labels are not candidate-scoring features
- no span proposal, string retrieval, RAG or external LLM
