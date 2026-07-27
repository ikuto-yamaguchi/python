# RESET-E081 — R0 Research Reconstruction integration

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. A〜Dは公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。新しいtoy仮説、別branch、新規機構族は作らない。既存stacked draft PRはnegative-results archiveとして扱う。

## Verified repository state

- PR #409 is open, draft and mergeable.
- Exact one-step resume-equivalence evidence remains accepted: run `30300067389`, job `90090542489`, artifact `8666312079`.
- Official SILG 100M-frame reproduction remains **0 completed**.
- Seed-1 / entropy-0.05 first 1M checkpoint remains **submitted / result unconfirmed** because the push-run job, artifact and checkpoint qualification were not independently observable in this integration.
- J-CRe3 numerical reproduction remains **0**.

## Evaluation-contract correction

The only visible failing PR workflow was `R0D core normalized cell identity`.

First, the workflow was converted from a pull-request-triggered self-mutating commit/push job into read-only fail-closed CI:

- permissions reduced from `contents: write` to `contents: read`;
- automatic report generation, commit and push removed;
- the historical patch applicator is run only to prove idempotence;
- any unexpected diff in `evaluation_contract.py` fails the job;
- production core, patch helper and focused regression are compiled and executed.

The replacement run `30314975578`, job `90138521234`, proved that checkout, patch idempotence and compilation all passed; only the focused regression failed. The regression fixture declared `entity_holdout` without an `entity_id` or `entity_signature`. The production contract correctly rejected that nominally “valid” fixture. The fixture now provides split-specific entity identities so train/eval holdout identity remains disjoint.

This is an evaluation-test correction, not a model, benchmark, split, control, metric or capability change. The blocker is not closed until the next replacement check succeeds.

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
