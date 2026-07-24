# Intelligence Swarm Backlog

## P0 — Reproduce before inventing

### R0.1 SILG environment pinning

- 公式SILGのMessengerまたはRTFMを固定versionで導入する。
- dataset/environment checksum、Python依存、seed、train/dev/test splitを記録する。
- pretrained language modelを使わない公式または最小共有baselineを再現する。
- random policy、language-blind policy、state-only policyを必須対照にする。

### R0.2 Environment-first representation baseline

- 言語なしstate transitionからaction-conditioned latent representationを事前学習する。
- 同じparameter budgetでend-to-end baselineと比較する。
- held-out entity、held-out dynamics、held-out language formでsuccess rateとnext-state predictionを測定する。
- 内部表現の可視化だけではなく、外部instruction-following能力で比較する。

### R0.3 Intervention-target identifiability ablation

同じtrajectoryへ以下の条件を用意する。

1. intervention target既知
2. intervention targetの候補集合だけ既知
3. intervention target完全未知
4. target label shuffle
5. action/outcome shuffle

測定:

- prospective next-state prediction
- action selection
- inverse action/query
- entity/reference re-identification
- unseen dynamics transfer
- closed-loop task success

### R0.4 Japanese realism audit

- J-CRe3の利用条件とデータ取得手順を固定する。
- テキストだけ、視覚だけ、両方のblind baselineを再現する。
- 主語省略、指示表現、橋渡し照応、述語項構造を条件別に分離する。
- SILG結果とJ-CRe3結果を同一能力として平均しない。

## P0 — Benchmark contract

- `benchmarks/grounded_causal/evaluation_contract.py`を全実験で使用する。
- train/test正規化文の完全重複を禁止する。
- model inputへgold action、after state、completed trajectoryを含めない。
- 2 domain以上、3 seed以上を必須とする。
- Correct、random、language-blind、state-only、target-label shuffle、outcome shuffleを同じinstanceで比較する。
- metricsはdomain × seed × condition cellごとに保存する。
- 内部候補数をprogress metricへ使用しない。

## P1 — Prior-art and novelty audit

- causal representation learningのidentifiability assumptionを表形式で整理する。
- grounded instruction followingが前提として与えるstate/action/entity structureを整理する。
- raw languageとunknown intervention targetの共同同定を扱う論文を追加探索する。
- 同一問題が既に解かれている場合、RQ-001を棄却して別問題を選ぶ。
- 新規性は「見つからなかった」だけでなく、検索query、対象venue、期間、除外理由を保存する。

## P1 — Theory before new mechanism

R0再現後、次のどちらか一つだけを選ぶ。

- 識別不能性定理: どの観測対称性がraw language–causal alignmentを不可能にするか
- 十分条件定理: どのtrajectory diversityとintervention structureで共同同定できるか

定理または明確な反例がないまま新しいarchitectureを増やさない。

## P2 — New model gate

新規モデル実装を開始できる条件:

1. R0.1〜R0.3再現完了
2. baselineとの差分が1文で説明可能
3. 新規性監査で直接重複がない
4. 事前登録されたprimary metricと停止条件がある
5. 一つのcanonical branchと一つのbenchmarkを使用

## Frozen work

- opaque tokenだけの新規toy benchmark
- 新しい名称を付けたspan、slot、graph、tensor、assembly、attractor
- baseline未再現のままのAF-014派生
- memory、replay、sleep、forgetting最適化
- best seed、domain平均、一条件だけの陽性
- after-stateまたはcompleted trajectoryを使うprospective評価
- PRを積み上げるだけでcanonical baselineへ統合しない運用

## R0 completion rule

R0は次をすべて満たしたときだけ完了。

- 外部公開benchmark 1件以上のbaseline再現
- 言語blind/state-only/random対照の実測
- 3 seed以上の再現ログ
- CPU/RSS/model size測定
- novelty matrix完成
- RQ-001の採用または棄却
- 次段階の中心命題を一つだけ決定
