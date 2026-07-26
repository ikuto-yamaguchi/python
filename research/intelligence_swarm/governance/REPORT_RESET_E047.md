# RESET-E047 — Execute, do not close on governance

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

R0 Research Reconstructionだけを継続する。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## Evidence reviewed

- Current accepted SILG evidence remains the 32,768-frame run: Correct `1/60`, Random `4/60`, Language-blind / State-only / Language-shuffle `1/60`.
- Immutable 131,072-frame competent R0.1 bundle: `0`.
- J-CRe3 numerical reproduction: `0`.
- Qualified R0.2 result: `0`.
- Current canonical-head workflow successes observed during this integration are audit/test workflows only: artifact path containment, unified acceptance gate, prediction method topology.
- Audit/test CI is not a public benchmark reproduction and is not capability progress.

## Execution decision

A governance-only iteration is prohibited. This integration must end by updating `R01_RUN_REQUEST.json` so the canonical SILG/RTFM split-job workflow is requested from the post-governance head.

The R0.1 job must preserve, irrespective of qualification outcome:

- seeds `1,7,19` checkpoints and exact frame counts;
- Correct / Random / Language-blind / State-only / Language-shuffle same-instance results;
- action histogram, valid-action ratio, policy entropy, episode length, reward reach rate;
- pre/post-mask logits and invalid-action probability mass;
- gradient norm and policy/value losses;
- model/checkpoint bytes, peak RSS, training runtime, CPU inference latency;
- source commit, split, dependency freeze, raw logs and SHA-256 manifests;
- leakage findings and qualification result.

R0.2 remains blocked unless `qualified_for_r02=true`.

A failed R0.1 run remains open until it records a failure class, evidence-backed cause, one-variable correction, matched rerun, and adoption/rejection/stopping decision. At most six diagnostic screening runs are allowed before a preregistered stopping or reprioritization decision.

## Prior-art correction

LeGIT / “Can Large Language Models Help Experimental Design for Causal Discovery?” is retained as prior art for language-guided intervention selection and low-data warm-starting.

The project page displays a `Code` label, but the link did not resolve to a public repository during this audit, and the OpenReview records do not provide an official repository URL. The status is therefore corrected to:

> paper/project-page verified; official code unresolved; immutable reproduction unavailable.

No LeGIT numerical claim is imported as project evidence.

## RQ-001 decision

> **NARROWED BEYOND LANGUAGE-GUIDED INTERVENTION SELECTION — NOT ADOPTED**

Adoption still requires a reproduced strongest non-language baseline and LeGIT-type baseline, a residual countermodel pair, a fixed non-recodable denotational law, direct language-specific incremental evidence beyond target selection, and preregistered claim/counterexample/stopping rule.

## Formal status

- R0.1 competent external baseline: **not reproduced**
- J-CRe3: **not reproduced**
- R0.2: **not qualified**
- R0.3 hidden intervention-target track: **rejected**
- novelty matrix: **incomplete**
- central proposition preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
