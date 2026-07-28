# RESET-E058 — Corrected entropy screening dispatch

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dへ新規toy仮説、別branch、新規機構族を追加しない。公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## R0.1 evidence carried forward

### Immutable baseline run `30203026269`

- artifact `8633105142`
- Correct `0/60`
- Random `4/60`
- Language-blind `1/60`
- State-only `0/60`
- Language-shuffle `0/60`
- Correct return `-2.0749993`
- Random return `-1.1513333`
- same-instance controls: pass
- answer leakage: false
- classification: `optimization_or_policy_competence_failure`

### Invalid attempted entropy screening `30208660095`

- requested entropy cost: `0.005`
- actual entropy cost in every seed command: `0.05`
- Correct `3/60`
- Random `4/60`
- same-instance controls: pass
- answer leakage: false
- classification: `experiment-factor-routing_failure`

This run is retained only as an additional negative result at entropy cost `0.05`. It does not test the `0.005` hypothesis.

## E058 action

`R01_RUN_REQUEST.json` was updated to `R01-SCREEN-002-E058`. This push targets `.github/workflows/r01_silg_entropy_screening.yml`, which verifies before evaluation that the top-level training summary, every seed record, and every complete seed command use `entropy_cost=0.005`.

Only entropy cost may change. Architecture, source commits, dataset, train/test split, requested frames, seeds `1/7/19`, actors, batch size, unroll length, and matched evaluation instances remain fixed.

The previous head `1cbde2903447fa40f49088bbccc4053c9886b5d6` had four PR-associated workflow runs with conclusion `action_required` and no jobs. These are execution blockers, not model results. The entropy hypothesis remains undecided until the corrected push run yields a run ID, jobs, immutable artifact, qualification JSON, and complete commands.

## Required checks per iteration

1. Latest primary literature and official-code overlap audit.
2. SILG/RTFM and J-CRe3 reproduction status.
3. Random, language-blind, state-only, and applicable shuffle controls.
4. Model/checkpoint bytes, peak RSS, runtime, CPU latency, seed, split, and actual frames.
5. Answer, schema, outcome, and post-treatment leakage.
6. RQ-001 adopt, narrow, or reject conditions.

## Failure continuation

A failed corrected run does not close the cycle. If `0.005` is proven in every command and Correct still fails to exceed Random or has zero success, entropy cost is rejected as the sole cause and the next one-factor screening is official evaluation/default parity. Recurrent reset/detach and optimizer restore follow, then learning rate, gradient clipping, and unroll. The cycle continues up to the preregistered screening limit or stopping condition.

## Prior-art status

The boundary continues to include score-based and finite-sample causal representation learning, language-guided intervention selection, multimodal causal invariance, partially observed multi-view CRL, causal sufficiency/necessity regularization, text-defined confounder intervention, generative-representation causal inference, language-only causal-relation inference, and local-structure dynamical-system identification. The latest primary-source audit found no direct basis to adopt RQ-001.

Formal decision:

> **RQ-001: FURTHER NARROWED — NOT ADOPTED**

## Formal status

- immutable R0.1 bundles: **2, both unqualified**
- valid entropy `0.005` screening: **dispatched, result unconfirmed**
- learned external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained closed**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
