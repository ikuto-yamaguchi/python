# RESET-E064 — Stateful screening closure and unroll-80 continuation

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope guard

- No new toy hypothesis.
- No new mechanism family.
- No separate branch or stacked PR base.
- Existing stacked draft PRs remain a negative-results archive.
- Work remains limited to public benchmark reproduction, prior-art audit, evaluation contract, and the retained rejection of the hidden intervention-target empirical track.

## R0.1 official-stateful result

Primary workflow run `30221587227` completed training, factor verification, matched controls, recurrent diagnostics, evaluation parity, qualification, checksum freeze, and artifact upload.

Evidence:

- job `89844840438`
- artifact `8638198496`
- digest `sha256:ae28542e4bda4ca968de9d7ffc42b5ab4b4dadb518a26636a41d63b92131aa31`
- artifact size `91,615,915 bytes`
- execution commit `4b1dff1cd6cd3f6a2dc360d5689cb9968c6a4998`
- all seed commands contained `--stateful`
- all checkpoints contained LSTM `core.*` weights
- all seeds had non-zero recurrent-state norms
- all checkpoints reached `131,080` frames
- same-instance controls and official/fresh parity passed
- answer leakage was false

Matched aggregate:

- Correct: `2/60` (`0.0333`)
- Random: `4/60` (`0.0667`)
- Language-blind: `2/60`
- State-only: `1/60`
- Language-shuffle: `2/60`
- Correct mean return: `-1.8273327`
- Random mean return: `-1.1513333`

Resources:

- parameters: `6,200,115`
- state-dict: `24,828,505 bytes`
- trained model-state: `24,827,943 bytes` per seed
- CPU forward: `8.162 ms/step`
- peak RSS: `1,069,864 / 1,334,592 / 1,274,272 KiB`
- training wall: `1691.39 / 1569.14 / 1686.73 s`

Qualification rejected with:

- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

Decision:

> The official stateful path was genuinely activated but did not establish competent policy or language use. Missing stateful core is rejected as the sole cause.

The later run `30221650935` produced no job and is not counted as independent evidence. The complete primary artifact makes it unnecessary as fallback evidence.

## Next single-factor experiment

The next factor is the largest remaining official-default mismatch in the learner trajectory horizon:

- `unroll_length: 20 → 80`

Fixed:

- official `multi`
- `stateful=true`
- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- frames `131072`
- seeds `1/7/19`
- split and identical evaluation instances
- random / language-blind / state-only / language-shuffle

Added:

- `patch_silg_unroll80_screening.py`
- `.github/workflows/r01_silg_unroll80_screening.yml`

The workflow fails closed unless every command contains both `--stateful` and `--unroll_length 80`, all checkpoints contain the LSTM core, recurrent state is active, and immutable resource/provenance/control/leakage evidence is preserved.

A valid negative result does not end the iteration. It rejects unroll shortage as the sole cause and requires selection of exactly one learner-optimization cause from preserved code/log evidence.

## Prior-art audit

AAAI 2026 CTLD constructs a causal action/deferral target from potential-outcome bounds under hidden confounding. Therefore causal target construction and defer-policy learning under hidden confounding are not novel grounds for RQ-001. CTLD does not reproduce latent intervention-target grounding or SILG/J-CRe3 capability. The primary paper is confirmed; author-official code and exact commit remain unresolved.

RQ-001 decision:

> **FURTHER NARROWED BEYOND CAUSAL TARGET CONSTRUCTION FOR LEARNING-TO-DEFER UNDER HIDDEN CONFOUNDING — NOT ADOPTED**

## Formal state

- immutable R0.1 artifacts: **5**
- competent learned external baseline: **0**
- J-CRe3 numerical reproduction: **0**
- R0.2 qualified reproduction: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **not found**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
