# RESET-E066 — R0 Research Reconstruction Integration

Date: 2026-07-27
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope control

- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 公開benchmark再現、prior-art audit、D015〜D035 evaluation contract、hidden intervention-target ablationの既存境界だけを累積する。
- 既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。
- 外部baseline再現前に新規知能原理、能力進歩、高校生級到達を認定しない。

## 1. Latest primary literature and official-code duplication audit

ACL Findings 2026のTRACEを一次論文で確認した。

TRACEは、multi-turn dialogueを通じたunderlying causal graphのonline reconstructionを問題化し、二段階RLを用いる。

1. exploration phase: surface-to-deep causal graph reconstructionをreward化する。
2. intervention phase: irrational beliefへのtargeted restructuringをreward化する。

したがって、次の要素だけではRQ-001の新規性を認定しない。

- dialogueからの逐次的causal-graph exploration
- causal-graph reconstruction reward
- 言語対話で介入対象を深掘りすること
- explorationとtargeted interventionを二段階RLで接続すること

ACL Anthologyの一次論文は確認済みである。一方、今回の監査ではauthor-official repository、exact commit、dependency、dataset、公式commandを固定できなかった。よって公式code再現は0件であり、TRACEの論文値を本研究の能力証拠へ流用しない。TRACEはcounseling-domainのcausal dialogue/interventionであり、SILGのinteractive grounded-policy competenceまたはJ-CRe3の日本語実世界reference resolutionを代替しない。

RQ-001 decision:

> **FURTHER NARROWED BEYOND DIALOGUE-DRIVEN CAUSAL-GRAPH EXPLORATION AND TARGETED INTERVENTION — NOT ADOPTED**

## 2. SILG / J-CRe3 reproduction progress

### SILG / RTFM

Active single-factor screening:

- factor: `unroll_length: 20 → 80`
- run: `30226976064`
- job: `89867137085`
- execution commit: `344002bc8e5130cbb9a302fda1a2115baa8edb1c`
- status: `in_progress`

Completed steps:

- checkout
- Python setup
- immutable provenance
- pinned SILG / RTFM install
- official-stateful harness patch
- unroll-80 patch
- generator schema verification
- canonical random control and schema probe

Current step:

- `Train official stateful multi with unroll 80`

Artifacts and numerical performance are not yet available. This run is not counted as reproduction success or capability progress. No duplicate run is dispatched while this job is active.

### J-CRe3

- official numerical reproduction: **0件**
- exact commit / dataset checksum / official command fixation: **未完了**
- SILG interactive-policy baselineを代替しない。

## 3. Matched controls

The active SILG contract requires identical-instance evaluation for:

- Correct
- Random
- Language-blind
- State-only
- Language-shuffle

No control result from the active unroll-80 run is available yet. Existing stateful evidence remains Correct `2/60`, Random `4/60`, Language-blind `2/60`, State-only `1/60`, Language-shuffle `2/60`; it remains a rejected baseline.

## 4. Model / RSS / runtime / seed / split

The active run keeps fixed:

- SILG commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit `58f17955595b5a127c96d045d896fcbcc7d4b570`
- model family `multi`
- `stateful=true`
- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- requested frames `131072`
- seeds `1/7/19`
- fixed train/test split and matched instances

The run must preserve model/checkpoint bytes, peak RSS, training wall time, CPU latency, actual frames, seed, split, dependency lock, raw logs and SHA-256. None is accepted until artifact completion and qualification.

## 5. Leakage and evaluation contract

- D015〜D035 remain frozen.
- No new auditor is added without a concrete false pass or false failure from a real artifact.
- The active run must preserve leakage=false and prediction provenance.
- Official continuous-stream / fresh-instance parity and the unchanged qualification gate remain mandatory.

## 6. RQ-001 adoption / narrowing / rejection conditions

- broad RQ-001: **rejected**
- narrow RQ-001: **further narrowed, not adopted**

Adoption still requires all of the following:

1. competent external public baseline reproduction;
2. language-specific additional information after strongest applicable non-language baselines;
3. explicit countermodel pair;
4. externally fixed denotation law eliminating joint recoding;
5. preregistered claim, counterexample and stopping rule;
6. qualified model/resource/control/leakage evidence.

## Non-termination and next action

The current run is training; no model factor is changed and no duplicate is dispatched.

After completion:

- validate factor routing (`--stateful`, `--unroll_length 80`, LSTM weights, non-zero recurrent state);
- retrieve all matched controls and resources;
- run parity, leakage and qualification;
- if Correct beats Random in win rate and return, verify three-seed minimum and resource cost;
- otherwise reject unroll shortage as the sole cause and select exactly one next factor from learning rate, gradient clipping or optimizer/checkpoint restore using preserved evidence.

A negative result alone does not close the iteration.

## Formal status

- immutable R0.1 artifacts: **5件**
- competent external baseline reproduction: **0件**
- active unroll-80 screening: **training中**
- J-CRe3 numerical reproduction: **0件**
- qualified R0.2: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- central claim preregistration: **未完了**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- high-school-level intelligence: **未達**
- next-stage proposal: **なし**
