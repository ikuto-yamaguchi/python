# Reproduce D Memory Eligibility Cycle 004

## Environment

- Python 3.11+
- NumPy
- Linux/macOS/WSL

## Command

```bash
cd research/intelligence_swarm/tracks/D_memory_eligibility
python lexicon_disjoint_eligibility_cycle004.py
```

The script writes `MEASUREMENTS_CYCLE_004.json` beside itself.

## Fixed conditions

- seeds: 1 / 7 / 19
- 2 fully lexicon-disjoint opaque domains
- 16 adaptation records/domain
- 96 tests/condition
- 64 contradictory interference records
- 32 prospective target×move candidates
- 8 inverse choices
- correct / shuffled-outcome / post-interference comparison

## Leakage controls

- test outcomes are never used for adaptation, ranking, or eligibility construction
- post-treatment outcomes are used only in the explicitly observed adaptation episodes
- no shared domain dictionary
- no shared object ID
- no handwritten semantic slot or ontology
- no string retrieval, RAG, or external LLM
