# R0.2 Cycle 006 — fidelity and execution audit

## Scope

This cycle does not add a new operation/goal toy hypothesis, memory mechanism, architecture family, or branch. It audits the existing Environment-first baseline against Gaddy & Klein (ACL 2019), the authors' public implementation, and the fixed SILG/RTFM reproduction path.

## Primary sources

- David Gaddy and Dan Klein. *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*. ACL 2019. https://aclanthology.org/P19-1188/
- Official public implementation: https://github.com/dgaddy/environment-learning
- SILG public benchmark and fixed RTFM environment are retained from R0.1.

## Current public execution

GitHub Actions run `30121909415` was inspected at canonical head `507ef8abb0b7b00dcfa92089dda94853c47ec561`.

At inspection time:

- pinned-source installation: passed;
- canonical random/schema probe: passed;
- 32,768-frame recurrent training: running;
- matched recurrent controls: pending;
- R0.2 trajectory export and Environment-first comparison: pending;
- trajectory eligibility audit: pending.

No unfinished metric is incorporated as a result. The in-flight run is not restarted by this documentation-only commit.

## Fidelity audit

The paper's core causal ordering is represented correctly by the current harness:

1. learn an environment representation from language-free state transitions;
2. learn a language encoder that maps instructions into the pre-learned representation;
3. compare against an end-to-end instruction learner under matched data and inference parameter budgets.

However, `environment_first_baseline.py` is still a **continuous Gaddy/Klein-style adaptation**, not a faithful reproduction of the authors' default representation learner.

Material gaps:

1. **Representation type** — the current transition encoder emits one continuous vector. The public implementation uses a structured discrete message representation (multiple categorical variables).
2. **Alignment objective** — the current language stage trains only through next-state/action reconstruction. The public implementation includes direct matching between the transition-derived message and language-derived message.
3. **State objective** — the current code applies scalar MSE to a flattened RTFM vector containing continuous, binary, and categorical token-ID fields. This makes `next_state_mse` uninterpretable and it must not be counted as progress.
4. **Task success** — the current offline transition dataset cannot measure online RTFM task success.
5. **Transfer splits** — current exported rows expose holdout flags, but genuine held-out entity, dynamics, and language-form partitions have not yet been established by the public environment/export protocol.
6. **Source-policy competence** — R0.2 remains invalid unless each seed passes the existing trajectory anti-collapse and success gate.

## Locked interpretation

Until the above gaps are resolved, the current implementation must be named:

> `continuous_environment_first_adaptation_not_gaddy_klein_default_reproduction`

Its action accuracy can be retained as a pipeline diagnostic only. Internal representation appearance, dimensionality, and compression are not progress metrics.

## Next minimal change, conditional on the running artifact

1. Finish and inspect run `30121909415` without restarting it.
2. Verify seed 1/7/19 checkpoint, model, source, data, and raw-log digests.
3. Apply the trajectory eligibility gate before any Environment-first result is accepted.
4. If trajectories are ineligible, change only the official recurrent reproduction budget/condition.
5. If trajectories are eligible, implement the paper-faithful discrete-message and message-alignment baseline as a baseline correction, not as a new mechanism family.
6. Replace flat next-state MSE with a field-typed objective derived from the recorded SILG observation schema before reporting next-state prediction.
7. Add online task-success evaluation and real held-out entity/dynamics/language-form splits before claiming R0.2 reproduction.

## Status

- R0.2 formal reproduction: not complete
- public capability baseline: not reproduced
- novelty: not established
- intelligence principle: not claimed
- capability progress: not recognized
- high-school-level intelligence: not achieved
