# Reproduce Causal Grounding Cycle 010

```bash
python3 research/intelligence_swarm/tracks/C_causal_grounding/local_syntax_orbit_support_cycle010.py \
  > /tmp/causal_grounding_cycle010.json
python3 -m py_compile \
  research/intelligence_swarm/tracks/C_causal_grounding/local_syntax_orbit_support_cycle010.py
```

Expected qualitative checks:

- `local_active.true_support` is true for all seeds.
- `global_form.true_support` fails in two of three seeds.
- Local Active prospective and counterfactual metrics are above 0.93 on average.
- Local Active and Local Random are equal, so no active-selection progress is claimed.
- Outcome shuffle collapses the candidate version space and all external capabilities to zero.
- Argument shuffle lowers prospective, repair, mixed-order and counterfactual performance while operation inverse remains high.

The script uses Python standard library only. Final-test outcomes are not used for witness selection, candidate ranking or prediction.
