# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測・意味処理・仕事実行に必要な**最小記憶**と**最小計算**を、数学的下限と実測コストから逆算する研究です。

最終目標は、会話、文章作成、コーディング、ツール利用を伴うエージェント処理で、高性能LLMと同等以上の能力を、より小さい生涯総資源で実現することです。

現時点で高性能LLM級の能力を達成したという主張はしません。成功だけでなく、自由言語への失敗、候補探索の線形増加、Bell数の探索爆発も結果とCIへ固定します。

## 中心原理

過去全文を保持する必要はありません。同じ未来分布、または同じ将来意思決定価値を与える履歴は、同一状態へ圧縮できます。

```text
h ~ h'  iff  P(future | h) = P(future | h')
```

ただし状態だけ小さくしても、遷移表、検索、学習、検証、外部知識が巨大なら最小機械ではありません。次を同時に会計します。

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

## ランタイム方針

- 意味理解、記憶、推論をdense neural residualへ丸投げしない
- 最終バイナリにニューラル重みを残さない研究経路を優先する
- 記憶、推論、計画、創造、文章、コード編集を別ランタイムにしない
- 正準symbol、疎な事実状態、同じ書換え原理を共有する
- 汎用IRは部分評価、規則融合、状態最小化し、実行時overheadを消す
- cache、index、新命令は、生涯目的を改善した場合だけ採用する
- 探索・学習コストもモデル外へ隠さず、利用回数で償却する

## Phase 1: 最小予測状態

- IID過程: Hankel rank 1、因果状態1、実行時状態0bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態dense SVD: 576bytes、64 MAC/記号
- 離散因果状態: 48bytes、0 MAC/記号
- 特異値gapの誤判定を、分割data由来のnoise floorで修正

詳細: [`results/phase1.md`](results/phase1.md)

## Phase 2: 遷移法則の因数分解

- K個の独立bitを厳密予測するには最低K bit必要
- K=32の疎な平坦状態表でも約5.6TB
- 因数分解レジスタ機械は32bit＋定数規則
- dense FP32状態よりdata書込み量を約6656分の1へ削減

詳細: [`results/phase2.md`](results/phase2.md)

## Phase 3a: MDL構造探索

- 必要slot数を与えず0〜16slotを探索
- 100,000 tokenの8-key言語から8slot・offset 0を選択
- 15,486 QUERYを0誤り
- 少ないslotは誤り、多いslotは余分な記述bitで敗北

詳細: [`results/phase3a.md`](results/phase3a.md)

## Phase 4a: コンパイル済み超軽量バイトLM

- 学習625,748bytes、別seed test 155,073bytes
- 選択規則608、コンパイル状態696
- 実行時状態10bit
- `.mplm` binary 10,999bytes
- 0.468469605 BPB
- 平均1.015644遷移確認/byte

これは表層予測の橋渡しであり、open-domain意味理解の主張ではありません。

詳細: [`results/phase4a.md`](results/phase4a.md)

## Phase 4b〜4c: no-neural意味・創造機械

- 未知固有名詞をexact symbol tableへ一度だけ保存
- timestamp付き疎関係、更新、撤回、proof trace
- 創造性を意味program変形、候補生成、criticへ分解
- 外部知識、検索、候補探索も総コストへ含める

設計:

- [`docs/phase4b_minimal_semantic_machine.md`](docs/phase4b_minimal_semantic_machine.md)
- [`docs/phase4c_creative_semantic_machine.md`](docs/phase4c_creative_semantic_machine.md)

## Phase 5a: coding / writing / agentの統一基盤

次の5命令と一つのsymbol/state/rule/indexで、コード編集、文章構成、行動計画を処理しました。

```text
MATCH
DELETE
ADD
EMIT
CHOOSE_MIN
```

詳細:

- [`results/phase5a.md`](results/phase5a.md)
- [`docs/phase5_unified_work_machine.md`](docs/phase5_unified_work_machine.md)

## Phase 6: 数学的下限、スケーリング、生涯大域最適

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

## Phase 7a: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%
- 個別rewrite追加後も別系列で再び50%
- 10,000回の反復質問でもpersistent state量は増加なし
- 4,096事実でもindexed lookupは1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証のtask loopを実装
- コード候補探索は候補数に比例し、実repositoryには未達

詳細:

- [`docs/phase7_scaling_to_conversation.md`](docs/phase7_scaling_to_conversation.md)
- [`results/phase7a.md`](results/phase7a.md)

## Phase 8a: 残差駆動の意味program誘導

| parser | 未知組合せ | distractor拒否 | 未知言い換え |
|---|---:|---:|---:|
| exact surface | 0.0% | 100.0% | 0.0% |
| typed slot templates | 100.0% | 100.0% | 0.0% |
| induced feature program | 100.0% | 87.5% | 33.3% |

- entity/location各128: 表面列挙22,112,432bit → program＋symbol 13,989bit
- 約1,580.7倍削減
- 別の言い換え系列では16.7%で、open-domain理解は未達

詳細:

- [`docs/phase8_residual_semantic_program_induction.md`](docs/phase8_residual_semantic_program_induction.md)
- [`results/phase8a.md`](results/phase8a.md)

## Phase 8b: interaction traceから潜在操作・役割を誘導

- intent名やentity/location型を与えず9/9 operationを復元
- `SET(key,value) / GET(key)` を誘導
- key/value latent role purity 100% / 100%
- exact surface objective 4,130
- untyped symbols objective 1,964
- 2 latent roles objective 953、held-out 100%
- surface intent 202bit → state effect 163bit
- 新symbolは文字列bitだけを払い、追加rule 0bit

詳細:

- [`docs/phase8b_latent_roles_and_operations.md`](docs/phase8b_latent_roles_and_operations.md)
- [`results/phase8b.md`](results/phase8b.md)

## Phase 8c: 複数relation・部分観測・noise・遅延effect

- 27 traces、正解operation 24
- full SET 6/6、partial SET 3/3、delayed SET 3/3、GET 12/12
- raw recall 100%、precision 96%
- 偶然のexogenous changeを1本誤相関
- support 1 schema: held-out 94.7%、objective 5,007
- support 2＋confidence: held-out 19/19、objective 3,703
- 12-rule線形走査12 checks/input → cue index平均0.789 checks/input
- index pointer 48bitもdescription lengthへ含む

詳細:

- [`docs/phase8c_multi_relation_semantics.md`](docs/phase8c_multi_relation_semantics.md)
- [`results/phase8c.md`](results/phase8c.md)

## Phase 8d: anonymous sensorからrelation partitionを発見

relation channelを与えず、entity-local anonymous sensor、utterance、value、短いtimelineだけから2 relationとlag 1/2を復元しました。

| hypothesis | clusters | train errors | bits | new-entity validation | objective |
|---|---:|---:|---:|---:|---:|
| merged one relation | 1 | 7 | 35 | 50% | 5,667 |
| best three relation | 3 | 0 | 101 | 50% | 2,149 |
| flat four relation | 4 | 0 | 132 | 0% | 4,228 |
| selected two relation | 2 | 0 | 66 | 100% | 66 |

正しい因数分解だけが、relationごと1回のcalibrationから未観測paraphraseへ100%転移しました。

ただし全partition探索はBell numberで爆発します。

| templates | partitions |
|---:|---:|
| 4 | 15 |
| 8 | 4,140 |
| 12 | 4,213,597 |
| 32 | 128,064,670,049,908,713,818,925,644 |

詳細:

- [`docs/phase8d_latent_relation_partition.md`](docs/phase8d_latent_relation_partition.md)
- [`results/phase8d.md`](results/phase8d.md)

## Phase 8e: 残差衝突だけからrelationをsplit

全partition列挙を廃止し、各templateの最小残差署名から次だけを提案します。

```text
lag split
anonymous-cell-rank split
lag + cell-rank split
高残差templateの少数isolation
cluster merge
```

最初のsplitへ局所commitせず、bounded beamで複数仮説を保持します。4・8 templateでは全探索oracleも実行し、大域目的gapを測りました。

| templates | hidden relations | Bell partitions | evaluated | fit checks | exact partition | held-out | oracle gap |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 2 | 15 | 13 | 1,404 | yes | 100% | 0 |
| 8 | 3 | 4,140 | 35 | 15,995 | yes | 100% | 0 |
| 12 | 3 | 4,213,597 | 55 | 37,455 | yes | 100% | n/a |
| 32 | 4 | 128,064,670,049,908,713,818,925,644 | 101 | 318,352 | yes | 100% | n/a |

8 templateでは全探索の約118分の1のpartition評価で同じ大域解へ到達しました。12・32 templateはhidden generatorを評価にだけ使い、oracle列挙は実行していません。

探索はcompile時に一度だけ支払い、実行時modelから消します。ただし検索費用を隠さず、1・100・10,000 deploymentでの償却値も保存しています。32 templateの318,352 checksは10,000利用なら平均31.8352 checks/useです。

これはBell爆発を回避する明確な前進ですが、固定beamが一般に大域解を保証するわけではありません。

詳細:

- [`docs/phase8e_residual_partition_search.md`](docs/phase8e_residual_partition_search.md)
- [`results/phase8e.md`](results/phase8e.md)

## 次の実験

Phase 8fでは、残差署名が一意に定まる決定論的世界を外します。

1. effect成功率を100%から60〜95%へ変化
2. sensor欠測と誤観測
3. 2〜16 stepの可変遅延
4. contradiction、retraction、時間変化
5. 追加観測のValue of Informationを計算
6. 観測費用が期待regret削減を上回る場合だけtool / sensorを読む
7. 小世界oracleとのgap、search/state/read/write/operationを同時計測

その後、会話だけでなく文章、コード、tool actionのtraceを同じ潜在relation探索へ混在させます。

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .

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
python -m unittest discover -s tests -v
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub Actionsで全テストと全実験をゼロから再現します。
