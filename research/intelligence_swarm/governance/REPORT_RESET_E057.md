# RESET-E057 — Invalid entropy-screen diagnosis and corrected rerun

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

A〜Dは公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。新規toy仮説、別branch、新規機構族は禁止する。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにはしない。

## R0.1 finding

Workflow run `30208660095`は完了し、artifact `8634594371`、digest `sha256:aa2efd6a30d26074a4ddf39195b93f8dc046f164f87446a384e7d808bd5e5fbf`を保存した。

結果:

- Correct: `3/60 = 0.0500`
- Random: `4/60 = 0.0667`
- Language-blind: `3/60 = 0.0500`
- State-only: `1/60 = 0.0167`
- Language-shuffle: `3/60 = 0.0500`
- Correct mean return: `-1.6356662`
- Random mean return: `-1.1513333`
- Correct−Random return: `-0.4843329`
- same-instance controls: true
- answer leakage: false

しかし全seedのraw commandは `--entropy_cost 0.05` であり、事前登録した変更値 `0.005` は適用されていなかった。したがって、このrunをentropy仮説の反証または採用に使用しない。0.05条件の追加negative resultとしてのみ保存する。

## Root cause and repair

原因分類:

> `experiment-factor-routing_failure`

R01_RUN_REQUESTは0.005を宣言していたが、同じpath変更でgeneric reproduction workflowも起動し、generic workflowは`run_silg_recurrent_smoke.py`のdefault 0.05を使用した。

修正:

- `.github/workflows/r01_silg_entropy_screening.yml`を更新。
- training summary top-level、3 seed records、各seed commandの全てで0.005を検証する。
- 不一致ならmatched evaluation前にfail closedする。
- 修正commit: `54a1f1f3c09ed0a8d526ae4d877057cfa33cd3d6`

この修正は新機構ではなく、宣言済み単一要因screeningを正しく実行するための配線修復である。

## Controls and resources

次runでも以下を固定・保存する。

- Random / Language-blind / State-only / Language-shuffle
- same initial instance stream
- model/checkpoint bytes
- peak RSS
- training/runtime and CPU latency
- seeds `1/7/19`
- train/test split
- actual frames
- raw command and logs
- dependency freeze and checksums
- answer/schema/prediction leakage

## Prior-art audit

最新一次文献としてCVPR 2026 MCDRL、ACL 2026 CmIR、ICML 2025 C3 Regularization、および既存score-based/finite-sample/multi-view CRL境界を再確認した。language-guided target selection、multimodal causal invariance、text-defined confounder intervention、causal sufficiency/necessity regularizationのみではRQ-001を採用しない。

## RQ-001

- Broad RQ-001: rejected.
- Narrow RQ-001: further narrowed, not adopted.

採用には、再現済み外部baselineを差し引いても残るlanguage固有情報、明示的countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要である。

## Stage status

- valid immutable R0.1 competence bundle: 0
- immutable failed bundles: 2
- valid entropy=0.005 screen: pending
- J-CRe3 reproduction: 0
- qualified R0.2: 0
- R0.3: rejected and closed
- novelty matrix: incomplete
- central preregistration: incomplete
- new mechanism family: not recognized
- new intelligence principle: not found
- capability progress: not recognized
- high-school-level intelligence: not achieved
- next stage: not proposed
