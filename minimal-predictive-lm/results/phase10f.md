# Phase 10f results: matched benchmark and resource harness

The harness sends prompts without targets to fresh model subprocesses,
checks benchmark checksums and run-policy equality, and records quality and
resource usage before allowing any parity or Pareto claim.

## Harness smoke run

- examples: **15**
- target leakage: **False**
- fresh subprocess: **True**
- overall accuracy: **100.0%**
- coverage: **100.0%**
- model program bytes: **116**
- peak RSS bytes: **33,816,576**
- wall time: **104.841 ms**
- CPU time: **302.762 ms**
- feature reads / operations: **284 / 314**

## Anti-overclaim gates

- non-public violations: **benchmark_not_public**
- non-public parity allowed: **False**
- policy mismatch violations: **benchmark_not_public, run_policy_mismatch**
- policy-mismatched parity allowed: **False**

## Comparison readiness

- public benchmark executed: **False**
- matched open model executed: **False**
- first narrow comparison ready: **False**
- Stage-C score: **8 → 8 / 24**
- mandatory evidence runs remaining: **2**

The infrastructure gate is complete, but no public comparison evidence is
claimed from the synthetic smoke run.

## Limitations

- the smoke benchmark is synthetic and is used only to validate the harness
- no open model is downloaded or executed in Phase 10f
- peak RSS includes the Python runtime and imported modules
- operation and read counters are model-specific and are not yet cross-model comparable
- energy is absent unless an external runner supplies a measured value
- a public benchmark and a matched open-model run are still required before comparison claims
