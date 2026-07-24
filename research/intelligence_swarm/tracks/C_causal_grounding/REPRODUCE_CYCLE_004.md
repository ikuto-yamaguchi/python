# Reproduce C Causal Grounding Cycle 004

```bash
python -m py_compile research/intelligence_swarm/tracks/C_causal_grounding/active_consequence_disambiguation_cycle004.py
python research/intelligence_swarm/tracks/C_causal_grounding/active_consequence_disambiguation_cycle004.py > /tmp/c_cycle004.json
```

- Python 3.11+
- NumPy required
- Seeds: 1, 7, 19
- No network, RAG, external LLM, string retrieval, span proposal or domain dictionary
- Selection uses only bootstrap-model disagreement before observing the selected outcome
- Test outcomes are never used for selection or training
