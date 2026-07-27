# RESET-E069 — R0 Research Reconstruction integration

Date: 2026-07-27
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。公開benchmark再現、prior-art audit、D015〜D035 evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

## R0.1 learning-rate result

Primary run `30235108376` / job `89881341003` completed training, factor-routing verification, identical-instance controls, recurrent diagnostics, official/fresh evaluation parity, qualification and artifact upload.

Immutable artifact:

- artifact ID `8642403437`
- digest `sha256:882e92a17ba5da5836dcf78379a484cc7ed63827ed3bf0b18196c5b18c3d8917`
- size `91,609,969 bytes`
- execution commit `67556f067028edac502380c6d3de15575c996ffc`

The requested single factor reached every seed:

- `stateful=true`
- `unroll_length=80`
- `learning_rate=0.0001`
- complete LSTM `core.*` checkpoints
- actual frames `131,200` per seed

Matched results:

- Correct `0/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `1/60`
- Language-shuffle `0/60`
- Correct mean return `-2.1523326`
- Random mean return `-1.1513333`
- Correct−Random return `-1.0009993`

Qualification failures:

- `zero_source_policy_success`
- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

Resources:

- parameters `6,200,115`
- model-state bytes `24,827,943 / 24,827,943 / 24,828,026`
- peak RSS KiB `1,470,976 / 1,269,884 / 2,414,924`
- training wall seconds `1441.30 / 1404.99 / 1483.19`
- model-audit CPU forward `7.511 ms/step`
- chosen-action valid fraction `1.0` for every seed
- answer leakage `false`

Formal decision:

> `learning_rate=0.0001` is rejected as the sole cause of the reproduction failure. The factor was correctly routed, but Correct had zero success, remained below Random, and showed no language-dependent advantage.

The negative result does not close the iteration.

## Next single-factor screening

Pinned official SILG source hard-codes:

```python
nn.utils.clip_grad_norm_(model.parameters(), 40.0)
```

The next screening changes exactly this threshold:

- gradient clip norm `40.0 → 10.0`

All other conditions return to the accepted unroll-80 reference contract and remain fixed:

- official-default learning rate, with no explicit override
- `stateful=true`
- `unroll_length=80`
- entropy `0.05`
- actors `2`, threads `1`, batch `2`
- frames `131072`
- seeds `1/7/19`
- model family, split, instances and controls

Implementation added:

- `patch_silg_gradient_clip_screening.py`
- `.github/workflows/r01_silg_gradient_clip_screening.yml`
- patch commit `2c877197b275e9c11f018479909adfe8e2a82844`
- workflow commit `3f0c62430a27116722c22f69525b54631d93032b`

The workflow fails closed unless the pinned installed source contains clip `10.0` and no clip `40.0`, all commands retain stateful/unroll=80 without an explicit learning-rate override, all checkpoints are complete, and matched controls/resource/checksum/leakage/parity/qualification evidence is preserved.

If valid clip `10.0` remains at or below Random, gradient clipping is rejected as the sole cause and the iteration proceeds to optimizer/checkpoint restore integrity as one next factor.

## Prior-art audit

MagicBench, ACL 2026, diagnoses visual-agency loss and semantic dependency in multimodal LLMs. It reports that autonomous visual search can remain suppressed without linguistic triggers even under symmetric prompting, and uses spatial prompting and signal magnification as causal interventions to show that internal reasoning remains functional. Official code and dataset are exposed at `Ink-Dawn/MagicBench`.

Boundary consequence:

- language-triggered visual agency loss
- perceptual-access bottleneck diagnosis
- spatial-prompt or signal-magnification intervention
- recovery of visual grounding by those interventions

are not sufficient novelty for RQ-001. Exact commit, dependencies and immutable numerical reproduction remain incomplete, and MagicBench does not replace SILG interactive policy competence or J-CRe3 Japanese reference resolution.

Formal RQ decision:

> **FURTHER NARROWED BEYOND CAUSAL DIAGNOSIS OF LANGUAGE-TRIGGERED VISUAL AGENCY LOSS — NOT ADOPTED**

## Status

- immutable R0.1 artifacts: **7**
- competent external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejection retained**
- novelty matrix: **incomplete**
- successor central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **not discovered**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
