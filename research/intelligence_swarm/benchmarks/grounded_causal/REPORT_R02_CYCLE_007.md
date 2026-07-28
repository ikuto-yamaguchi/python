# R0.2 Environment-first baseline — cycle 007

## Scope

This cycle does not introduce a new operation/goal toy hypothesis, architecture family, memory mechanism, branch, or PR chain. It preserves the pinned SILG/RTFM environment and the official pretrained-LM-free `multi` recurrent source policy used by R0.1.

## Blocking evidence from the 131,072-frame staged run

GitHub Actions run `30128469496` failed before matched evaluation and R0.2 trajectory export. Dependency installation, the random/schema probe, artifact freezing, and bundle upload completed. The failure occurred inside `run_silg_recurrent_smoke.py` while training seed 1.

The official learner command was terminated by the harness after exactly 1,200 seconds:

- requested frames: `131072`
- seed: `1`
- exception: `subprocess.TimeoutExpired`
- fixed per-process timeout: `1200 s`
- elapsed at termination: about `1202 s`
- matched controls: skipped
- trajectory export: skipped
- R0.2 comparison: not executed

This is classified as a harness resource-bound failure, not a model-capability result. The 32,768-frame run required roughly 342–347 seconds per seed, so a fourfold frame budget can legitimately exceed the old fixed 1,200-second process limit without implying a learner defect.

## Minimal correction

`run_silg_recurrent_smoke.py` now scales the per-seed process timeout with the declared frame budget:

```text
max(1200, ceil(frames / 32768) * 600)
```

For `131072` frames this yields `2400 s` per seed. The workflow-level timeout remains unchanged and still bounds the complete three-seed job.

The correction also:

- records `seed_timeout_seconds` in the summary and each seed run;
- catches `TimeoutExpired` and writes captured stdout/stderr plus a structured harness error to the raw log;
- assigns return code `124` and `timed_out: true` rather than losing the reproducibility bundle through an uncaught exception;
- leaves the official SILG model, optimizer, loss, action/observation schema, seed mapping, split, data budget, and pretrained-LM condition unchanged.

Commit: `743e25c1478d45fbb55adcf38617d011e9308d0f`.

## R0.2 decision

No Environment-first result is recognized from run `30128469496` because no competent source-policy trajectory was exported. The earlier low-competence/collapsed trajectory remains ineligible. The continuous adaptation remains non-equivalent to the Gaddy & Klein default structured discrete-message baseline, and flat MSE over mixed-type RTFM fields remains invalid as a formal next-state metric.

R0.2 may proceed only after the corrected 131,072-frame run completes and the source trajectories satisfy the preregistered success and anti-collapse gate. If they do not, only a verified official-reproduction mismatch or declared resource ceiling may be addressed; the Environment-first representation model must not be tuned around an incompetent behavior policy.

## Status

- public capability baseline: not reproduced
- corrected 131,072-frame run: relaunched by canonical-branch update, result pending
- formal R0.2 reproduction: not completed
- task success / typed next-state / action accuracy / held-out transfers: not yet validly measured
- novelty, intelligence principle, and capability progress: not claimed
- high-school-level intelligence: not achieved
