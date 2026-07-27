# RESET-E081 — R0 Research Reconstruction integration

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. A〜Dは公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。新しいtoy仮説、別branch、新規機構族は作らない。既存stacked draft PRはnegative-results archiveとして扱う。

## Verified repository state

- PR #409 is open, draft and mergeable.
- PR head before this integration: `fdcf349199fc79a9dd6697fecc6f8244a8831f88`.
- Exact one-step resume-equivalence evidence remains accepted: run `30300067389`, job `90090542489`, artifact `8666312079`.
- Official SILG 100M-frame reproduction remains **0 completed**.
- Seed-1 / entropy-0.05 first 1M checkpoint remains **submitted / result unconfirmed** because the push-run job, artifact and checkpoint qualification were not independently observable in this integration.
- J-CRe3 numerical reproduction remains **0**.

## Evaluation-contract correction

The only visible failing PR workflow was `R0D core normalized cell identity`. The workflow mixed verification with repository mutation: it generated a report, committed, and pushed from a pull-request-triggered job. That design can fail through concurrent branch movement even when the normalized-cell regression itself passes.

The workflow was changed to a read-only, fail-closed CI check:

- permissions reduced from `contents: write` to `contents: read`;
- automatic report generation, commit and push removed;
- the historical patch applicator is run only to prove idempotence;
- any unexpected diff in `evaluation_contract.py` fails the job;
- production core, patch helper and focused regression are compiled and executed.

This is an evaluation-infrastructure correction, not a model, benchmark, split, control or capability change.

## Controls and evidence

No new official-horizon ability artifact was produced. Therefore no new values are recognized for Correct, random, language-blind, state-only or shuffle controls. The latest accepted short-horizon negative archive remains run `30240410850`, artifact `8644560521`:

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct mean return `-1.7679994`
- Random mean return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- answer leakage `false`
- qualification rejected

These values remain short-horizon negative evidence and are not an official SILG baseline failure.

## Prior-art boundary

Fresh primary-source review found no basis to adopt RQ-001. In particular, 2026 work already covers learning causal DAG coarsenings from interventional data with unknown targets, nonlinear causal reductions for explaining RL policies, and finite-sample recovery of representations and unknown intervention targets. These results narrow the remaining claim space but do not constitute an official executable baseline reproduction for this repository.

Formal decision:

> **RQ-001: FURTHER NARROWED — NOT ADOPTED**

## Formal status

- immutable R0.1 short-horizon artifacts: **8**
- exact one-step resume-equivalence artifacts: **1 accepted**
- official SILG 100M-frame reproduction: **0 completed**
- official-horizon matched controls: **0**
- competent external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejected / maintained**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none found**
- capability progress: **not recognized**
- high-school-level intelligence: **unmet**
- next stage: **not proposed**
