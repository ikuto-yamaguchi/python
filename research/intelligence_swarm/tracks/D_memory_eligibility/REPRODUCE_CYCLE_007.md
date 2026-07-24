# Reproduce D Memory Eligibility Cycle 007

```bash
python -m py_compile research/intelligence_swarm/tracks/D_memory_eligibility/intervention_residual_birth_cycle007.py
python research/intelligence_swarm/tracks/D_memory_eligibility/intervention_residual_birth_cycle007.py > /tmp/d_cycle007.json
python -m json.tool /tmp/d_cycle007.json > /dev/null
```

Python 3.11+ と NumPy を使用する。seedは1, 7, 19で固定される。テスト時にafter/completed trajectoryは入力へ渡さない。
