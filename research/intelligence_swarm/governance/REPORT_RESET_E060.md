# RESET-E060 — Valid entropy screening recovery

Date: 2026-07-26  
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope guard

- A〜Dは公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。
- 新しいtoy仮説、別branch、新規機構族は作らない。
- 既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。
- 外部baseline再現前に新しい知能原理、能力進歩、高校生級到達を認定しない。

## R0.1 result recovered

Valid entropy screening:

- workflow run `30215555334`
- job `89830932884`
- source commit `cbd4af3d89718df76cc481f7c730ed80334ef223`
- artifact `8636643017`
- artifact digest `sha256:094ba8d6fba428c15e1dfa43298f3af9943d9fae840a072a691d3f420c5bcec2`
- artifact bytes `72,690,803`
- factor `entropy_cost=0.005` reached all seed commands
- actual frames `131,080` for seeds `1/7/19`

Matched results:

- Correct `0/60`, return `-2.1523326`
- Random `4/60`, return `-1.1513333`
- Language-blind `2/60`
- State-only `0/60`
- Language-shuffle `0/60`
- same initial instances: true
- chosen actions valid: `1.0`

Resources:

- parameters `4,916,915`
- state dict about `19.69 MB`
- CPU forward audit `7.564 ms/step`
- peak RSS `1,370,676 / 1,337,440 / 1,247,468 KiB`
- training wall `1447.61 / 1519.27 / 1436.77 s`

The numerical result does not reproduce a competent public baseline. Entropy reduction alone is a rejection candidate, not yet a formally closed result because qualification was skipped by an audit implementation failure.

## Failure classification

The job failed at `Compare official and matched evaluation semantics` with:

`RuntimeError: empty evaluation stream`

Root cause:

- `Environment.initial()` carries the SILG auto-reset boundary marker `done=True`.
- `run_silg_matched_eval.py` correctly uses a local `done=False` and takes at least one step.
- `audit_silg_official_eval_parity.py` incorrectly tested the initial marker before any step, producing zero records.

Classification:

> `evaluation_audit_zero_step_failure`

This is not a model-performance failure and does not invalidate the preserved training or matched-control artifact.

## Repair

- Corrected fresh-instance parity evaluation to start with local `done=False` and update it only after `env.step()`.
- Removed parity-audit source changes from the expensive entropy-training workflow push paths.
- Made qualification `if: always()` so an auxiliary audit failure cannot silently suppress the core competence verdict.
- Added `.github/workflows/r01_silg_entropy_requalify.yml` to download artifact `8636643017`, install pinned SILG/RTFM, rerun parity and unchanged qualification, preserve provenance/checksums, and upload an immutable addendum.
- No retraining is authorised for this repair.

## Prior-art audit

C038 records ACL 2026 `Learning Invariant Modality Representation for Robust Multimodal Learning from a Causal Inference Perspective`.

Existing territory includes:

- per-modality causal-invariant versus environment-specific spurious decomposition;
- invariance constraints across environments;
- mutual-information and reconstruction constraints to preserve input information;
- OOD and noisy-modality robustness.

The ACL Anthology primary publication is confirmed. No author-official code link was confirmed on the publication page. These ideas alone do not support RQ-001 adoption.

Formal decision:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL MODALITY-INVARIANT REPRESENTATION — NOT ADOPTED**

## Next mandatory action

1. Complete artifact-only requalification.
2. Record requalification run ID, artifact ID/digest, parity JSON and qualification JSON.
3. If the unchanged gate reports zero success and Correct below Random, formally reject entropy cost as the sole cause.
4. Use the parity result to choose exactly one next cause:
   - evaluation/default mismatch if official protocol is materially stronger;
   - otherwise recurrent-state/optimizer restoration.
5. Do not close the cycle without issuing that next matched screening contract unless a preregistered stop condition is met.

## Formal status

- competent external baseline: **0**
- qualified R0.1: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central proposition preregistration: **incomplete**
- new mechanism family: **not recognised**
- new intelligence principle: **not found**
- capability progress: **not recognised**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
