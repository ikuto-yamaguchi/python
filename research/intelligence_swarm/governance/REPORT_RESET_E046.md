# RESET-E046 — R0 source-policy competence gate and LeGIT boundary

Date: 2026-07-25
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。今回の変更は公開benchmark再現、実行資格、prior-art境界、matched controls、resource/leakage保存、RQ-001判定だけに限定する。

## Problem found

従来のsplit-job workflowはR0.1 training/evaluation commandがexit 0であればR0.2へ進んだ。したがって、official source policyがRandom以下、success zero、frame未達、matched-instance不成立でも、下流R0.2が実行され得た。これは無能力なsource policyからrepresentation差を解釈する経路であり、性能研究と反証の双方を損なう。

## Implemented execution change

`research/intelligence_swarm/benchmarks/grounded_causal/qualify_r01_source_policy.py`を追加し、`.github/workflows/r0_silg_rtfm_probe.yml`のR0.1とR0.2の間へ接続した。

Qualificationは以下をfail-closedで検査する。

- pinned SILG/RTFM commit
- exact seeds `1,7,19`
- requested framesとcheckpoint actual frames
- 全seed training/checkpoint完成
- Correct / Random / Language-blind / State-only / Language-shuffle
- same initial instance stream
- answer leakage explicit false
- Correct win rate > Random win rate
- Correct return > Random return
- Correct success > 0

不合格時はR0.1 jobを失敗にしつつ、`if: always()`でcheckpoint、matched result、resource、raw log、pip freeze、checksums、qualification JSON/logを保存する。R0.2は`needs`により開始されず、仮にartifactを取得しても `qualified_for_r02=true` を再確認する。

## Non-termination contract

不合格JSONは次を保存する。

- concrete failure list
- `implementation_or_artifact_failure` または `optimization_or_policy_competence_failure`
- source pins、seeds、controls、architecture freeze
- official defaults/determinism patch差分
- action/valid-action/entropy/termination診断
- recurrent reset/detach、frame counting、optimizer/checkpoint診断
- one-cause-only change rule
- matched rerun requirement
- preregistered screening-budget stop rule

これにより「検証したが駄目だった」はiteration完了にならず、次の原因切り分けrunへ接続される。

## Latest primary prior-art audit

LeGIT / “Can Large Language Models Help Experimental Design for Causal Discovery?”（2025 arXiv、ICLR 2026 submission、2026-02改訂）は、変数の自然言語meta-informationとLLMの世界知識を使ってonline causal discovery初期のintervention targetを選択し、既存の数値手法をwarm-startする。Asia、Child、Insurance、Alarmでrandom、数値手法、人間と比較する。

したがって以下はRQ-001の新規性候補から除外する。

- language/meta-informationによるintervention targeting
- low-data初期局面でのLLM warm-start
- language/world knowledgeとnumerical causal discoveryのhybrid
- target-selection改善そのものを新しいgrounding原理とみなすこと

Project pageはpaper/code linkを示すが、本canonical branchではcode link先のexact commit、dependency、prompt、split、seed、raw output、checksumを固定したimmutable reproductionは未実施である。よってLeGITの性能値を本研究の能力進歩として認定しない。

## Six required checks

1. 最新一次文献・公式code: LeGITを追加境界として統合。official exact-commit reproductionは未完了。
2. SILG/J-CRe3: 新しいaccepted numerical artifactは0。SILG R0.1 workflowにはcompetence gateを実装。J-CRe3は未再現。
3. Controls: SILG Correct/Random/Language-blind/State-only/Language-shuffleをqualification必須入力にした。J-CRe3 controlsは未実行。
4. Resources: model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、logs、checksumsを引き続き必須保存する。
5. Leakage: answer leakage explicit falseとsame-instanceをqualificationで再確認。D015〜D035はfreeze維持。
6. RQ-001: broad rejected。narrow claimはLeGIT型target selectionを越える必要があり、not adopted。

## Formal status

- immutable R0.1 competence bundle: **0**
- learned external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **not found**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
