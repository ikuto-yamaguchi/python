# RESET-E062 — Official stateful fidelity correction

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. No new toy hypothesis, branch, mechanism family, or stacked PR base is introduced.

## Evidence closed in this iteration

Artifact-only requalification of entropy screening completed:

- source run `30215555334`
- source artifact `8636643017`
- requalification run `30219453396`
- job `89839257839`
- addendum artifact `8636783476`
- digest `sha256:f752a62497362a38aeda76e3917210d1eb6eb31903743f7ee08232fc75104f12`
- corrected official/matched parity audit: passed
- unchanged qualification: rejected

Matched controls remain Correct `0/60`, Random `4/60`, Language-blind `2/60`, State-only `0/60`, Language-shuffle `0/60`. Official continuous-stream evaluation recovered only `1/60` total wins. Entropy reduction and evaluation protocol mismatch are rejected as sufficient main causes.

## New concrete root cause

Primary SILG source inspection established:

- `exp_utils.py` defines `--stateful` as an opt-in flag with default false.
- `model.multi.Model` creates `self.core = nn.LSTM(...)` only when `flags.stateful` is true.
- `initial_state()` returns an empty tuple when stateful is false.
- all prior R0.1 commands omitted `--stateful`.
- preserved policy diagnostics show recurrent-state L2 norms of `0.0` for every seed and episode.

Therefore prior artifacts were incorrectly described as recurrent. They are official `multi` non-stateful runs and do not reproduce the official recurrent capability path.

## Action taken

Added:

- `research/intelligence_swarm/benchmarks/grounded_causal/patch_silg_stateful_screening.py`
- `.github/workflows/r01_silg_stateful_screening.yml`

The next screening changes only `stateful: false → true`. It freezes entropy `0.05`, actors `2`, threads `1`, batch `2`, unroll `20`, frames `131072`, seeds `1/7/19`, source commits, split, matched instances and controls.

Fail-closed acceptance requires:

- `--stateful` in every training command
- `core.*` LSTM weights in every checkpoint
- non-zero recurrent-state norm for every seed
- random/language-blind/state-only/language-shuffle matched controls
- model/checkpoint bytes, RSS, runtime, CPU latency, seed, split, actual frames, logs and checksums
- leakage false
- parity and unchanged qualification outputs

If stateful remains incompetent, the next single factor is official `unroll_length: 20 → 80`; the iteration does not terminate at failure.

## Prior-art audit

ACL 2026 CAIR treats rationales as causal mediators and optimizes their interventional utility with a causal mediation reward and adaptive information bottleneck. Causal-mediator reward optimization, rationale faithfulness and multimodal emotion reasoning are therefore excluded from RQ-001 novelty. No direct evidence supports adoption of RQ-001.

## Formal status

- competent external baseline reproduction: **0**
- immutable R0.1 artifacts: **4**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained**
- broad RQ-001: **rejected**
- narrowed RQ-001: **not adopted**
- novelty matrix: **incomplete**
- central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
