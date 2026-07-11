# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測・意味処理・仕事実行に必要な**最小記憶**と**最小計算**を、数学的下限と実測コストから逆算する研究です。

最終目標は、会話、文章作成、コーディング、ツール利用エージェントで高性能LLMと同等以上の能力を、より小さい生涯総資源で実現することです。現時点では未達です。成功値だけでなく、自由言語、分布外、候補探索、学習・検証費用の失敗もCIへ固定します。

## 最小化する総目的

```text
prediction / task loss
+ static program bits
+ static knowledge bits
+ dynamic state bits
+ bits read / written
+ primitive operations
+ external effects
+ induction / training / compiler amortization
+ verification / migration / rollback
+ representation-boundary cost
+ held-out and shifted-task regret
```

状態だけを小さくして、巨大な遷移表、外部知識、検索、学習、tool呼出しへ費用を隠すことは許しません。

## ランタイム方針

- 意味理解、記憶、推論をdense neural residualへ丸投げしない
- 最終バイナリにニューラル重みを残さない経路を優先する
- 記憶、推論、計画、文章、コード編集を別ランタイムにしない
- 正準symbol、疎な事実状態、同じ書換え原理を共有する
- 汎用IRは部分評価、規則融合、状態最小化し、実行時overheadを消す
- cache、index、新命令は、生涯目的を改善した場合だけ採用する
- 学習・探索費用も利用回数で償却し、無料扱いしない

## Phase 1〜3: 最小状態と構造探索

- IID過程: Hankel rank 1、因果状態1、実行時状態0bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態dense SVD 576bytes・64 MAC/記号に対し、離散因果状態48bytes・0 MAC/記号
- K=32の疎な平坦状態表約5.6TBを、32bit＋定数規則へ因数分解
- MDL探索が100,000 tokenの8-key言語から8slot・offset 0を自動選択

詳細:

- [`results/phase1.md`](results/phase1.md)
- [`results/phase2.md`](results/phase2.md)
- [`results/phase3a.md`](results/phase3a.md)

## Phase 4: コンパイル済みLMとno-neural意味設計

実バイトLM:

- 学習625,748bytes、別seed test 155,073bytes
- 選択規則608、コンパイル状態696
- 実行時状態10bit
- `.mplm` binary 10,999bytes
- 0.468469605 BPB
- 平均1.015644遷移確認/byte

これは表層予測の橋渡しであり、open-domain意味理解ではありません。

意味・創造機械は、exact symbol、timestamp付き疎関係、撤回、proof trace、意味program変形、候補criticを設計しました。

詳細:

- [`results/phase4a.md`](results/phase4a.md)
- [`docs/phase4b_minimal_semantic_machine.md`](docs/phase4b_minimal_semantic_machine.md)
- [`docs/phase4c_creative_semantic_machine.md`](docs/phase4c_creative_semantic_machine.md)

## Phase 5: coding / writing / agentの統一基盤

```text
MATCH
DELETE
ADD
EMIT
CHOOSE_MIN
```

一つのsymbol table、state、rule、疎index、MDL探索器で、コード編集、文章構成、行動計画のmicro-taskを処理しました。

- [`results/phase5a.md`](results/phase5a.md)
- [`docs/phase5_unified_work_machine.md`](docs/phase5_unified_work_machine.md)

## Phase 6: 数学的下限と生涯大域最適

- 256段chain: 平坦規則5,376bit → 因数分解43bit
- 位置状態は理論下限9bit
- 20bit parity: 任意表1,048,576bit → 規則27bit＋状態1bit
- 必要な20bit読取りと256依存stepは不可避として残す
- Value of Computationで、判断を変える期待値が費用を上回る場合だけ追加思考
- 16-query workload: 局所commit 16,384、生涯大域選択4,032

詳細:

- [`docs/phase6_scaling_and_open_ended_intelligence.md`](docs/phase6_scaling_and_open_ended_intelligence.md)
- [`docs/phase6b_minimal_choice_machine.md`](docs/phase6b_minimal_choice_machine.md)
- [`docs/phase6c_global_optimization.md`](docs/phase6c_global_optimization.md)
- [`results/phase6a.md`](results/phase6a.md)
- [`results/phase6c.md`](results/phase6c.md)

## Phase 7: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%
- 個別rewrite追加後も別系列で再び50%
- 10,000回の反復質問でもpersistent state量は増加なし
- 4,096事実でもindexed lookup 1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証のtask loopを実装
- コード候補探索は候補数に比例し、実repositoryには未達

- [`docs/phase7_scaling_to_conversation.md`](docs/phase7_scaling_to_conversation.md)
- [`results/phase7a.md`](results/phase7a.md)

## Phase 8a〜8b: 表面記憶から潜在操作へ

- typed slotは未知symbol組合せ100%
- entity/location各128で表面列挙22,112,432bit → program＋symbol 13,989bit
- 別の言い換え系列では16.7%
- intent名やentity/location型を与えず、interaction traceから `SET / GET` を9/9復元
- key/value latent role purity 100% / 100%
- exact surface objective 4,130、untyped 1,964、two latent roles 953
- surface intent 202bit → state effect 163bit

詳細:

- [`docs/phase8_residual_semantic_program_induction.md`](docs/phase8_residual_semantic_program_induction.md)
- [`docs/phase8b_latent_roles_and_operations.md`](docs/phase8b_latent_roles_and_operations.md)
- [`results/phase8a.md`](results/phase8a.md)
- [`results/phase8b.md`](results/phase8b.md)

## Phase 8c〜8d: 複数relationとrelation partition発見

Phase 8c:

- full SET 6/6、partial SET 3/3、delayed SET 3/3、GET 12/12
- raw recall 100%、precision 96%
- support 1 schema: held-out 94.7%、objective 5,007
- support 2＋confidence: held-out 19/19、objective 3,703
- 12-rule線形走査12 checks/input → cue index平均0.789 checks/input

Phase 8dではrelation channelも外し、anonymous sensorから2 relationとlag 1/2を復元しました。正しい2-relation因数分解だけが、新entityで1回のcalibrationから未観測paraphraseへ100%転移しました。

ただし全partition探索はBell numberで爆発します。

| templates | partitions |
|---:|---:|
| 4 | 15 |
| 8 | 4,140 |
| 12 | 4,213,597 |
| 32 | 128,064,670,049,908,713,818,925,644 |

詳細:

- [`docs/phase8c_multi_relation_semantics.md`](docs/phase8c_multi_relation_semantics.md)
- [`docs/phase8d_latent_relation_partition.md`](docs/phase8d_latent_relation_partition.md)
- [`results/phase8c.md`](results/phase8c.md)
- [`results/phase8d.md`](results/phase8d.md)

## Phase 8e: 残差駆動partition探索

全partition列挙をやめ、lag・anonymous-cell-rankの残差衝突からsplit候補だけを作り、bounded beamとmergeで局所commitを避けます。

| templates | hidden relations | Bell partitions | evaluated | fit checks | exact partition | held-out | oracle gap |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 2 | 15 | 13 | 1,404 | yes | 100% | 0 |
| 8 | 3 | 4,140 | 35 | 15,995 | yes | 100% | 0 |
| 12 | 3 | 4,213,597 | 55 | 37,455 | yes | 100% | n/a |
| 32 | 4 | 128,064,670,049,908,713,818,925,644 | 101 | 318,352 | yes | 100% | n/a |

4・8 templateでは全探索oracleと同じ目的値・partitionに到達しました。固定beamは一般の大域最適を保証しないため、oracle可能な世界でgapを測り続けます。

- [`docs/phase8e_residual_partition_search.md`](docs/phase8e_residual_partition_search.md)
- [`results/phase8e.md`](results/phase8e.md)

## Phase 8f: 確率effect・欠測・Value of Information

成功率60〜90%、1〜16stepの遅延、結果欠測、lag欠測、sensor誤観測を導入しました。

履歴を再生せず、relationごとにBeta成功/失敗カウンタとDirichlet lagカウンタだけを保持します。

- training episodes: 1,200
- missing outcomes: 389
- successful outcomes with missing lag: 154
- active sufficient statistics: 126bit
- compact raw event code: 10,800bit
- history/stat ratio: 85.71x
- learned Brier: 0.157493、uniform: 0.25

一回だけ追加観測できる二値判断では、positive / negative / missingの全分岐を厳密列挙し、Bayes risk低下がsensor費用を上回る場合だけ観測します。

| policy | accuracy | probes | total objective |
|---|---:|---:|---:|
| none | 77.6% | 0 | 43,072 |
| always | 87.9% | 3,000 | 35,232 |
| VOI | 87.9% | 1,873 | 30,724 |

VOIは常時観測と同じ精度で、1,127回・37.6%のsensor readを削減しました。

矛盾・撤回ではappend-only provenanceとresolved active viewを分離します。512 claims / 32 keysで、ledger 86,272bitに対し、撤回期間確定後のsnapshotは2,992bitでした。確定前にledgerを捨てることはできません。

詳細:

- [`docs/phase8f_probabilistic_effects_and_voi.md`](docs/phase8f_probabilistic_effects_and_voi.md)
- [`results/phase8f.md`](results/phase8f.md)

## 次の実験

Phase 8gでは、Phase 8fで与えていた構造をさらに外します。

1. relation partition、成功率、lag分布、sensor reliabilityを共同推定
2. 非定常性をchange pointとして検出し、古い統計を無限に保持しない
3. 複数probeをbounded VOIで停止
4. 小世界POMDP oracleとのregret gapを測定
5. 会話、文章、コード編集、test結果、tool actionを同じevent modelへ混在
6. belief bit、read/write、branch、tool、移行、rollbackを全て会計

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .

python -m unittest discover -s tests -v
mpm-phase1
mpm-phase2
mpm-phase3a
mpm-phase4a
mpm-phase5a
mpm-phase6a
mpm-phase6c
mpm-phase7a
mpm-phase8a
mpm-phase8b
mpm-phase8c
mpm-phase8d
mpm-phase8e
mpm-phase8f
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub ActionsでPhase 1〜8fの全テスト・全実験をゼロから再現します。
