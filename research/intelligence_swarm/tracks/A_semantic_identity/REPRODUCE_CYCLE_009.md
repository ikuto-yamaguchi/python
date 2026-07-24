# Reproduce A Cycle 009

```bash
python research/intelligence_swarm/tracks/A_semantic_identity/minimal_witness_boundary_orbit_cycle009.py \
  > /tmp/A_CYCLE_009.json
python -m py_compile \
  research/intelligence_swarm/tracks/A_semantic_identity/minimal_witness_boundary_orbit_cycle009.py
```

## Environment

- Python 3.11+ recommended
- Standard library only
- Seeds: 1, 7, 19
- No network access required

## Expected summary

- Initial hypotheses: 1,152
- Active remaining hypotheses: 2.0
- Active prospective unseen: 0.6923
- Random prospective unseen: 0.6154
- Outcome-shuffle prospective unseen: 0.0
- Active unknown-order: 0.75
- Strict progress gate: false

Small runtime differences are expected. Accuracy values are deterministic for the listed seeds.
