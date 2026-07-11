# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測・意味処理・仕事実行に必要な**最小記憶**と**最小計算**を、数学的下限と実測コストから逆算する研究です。

最終目標は、コーディング、文章作成、ツール利用を伴うエージェント処理までを、一つの最小実行基盤で扱い、高性能LLMと同等以上の能力をより小さい生涯総資源で実現することです。

## 中心原理

過去全文を保持する必要はありません。同じ未来分布を与える履歴は、予測上は同一状態へ圧縮できます。

```text
h ~ h'  iff  P(future | h) = P(future | h')
```

ただし、最小状態数だけでは不十分です。状態をKビットへ圧縮しても、遷移表が `2^K` に膨張すればモデル本体は最小になりません。

さらに、能力ごとに別の内部表現を追加すると、同じ事実・目標・進捗が複数モジュールへ重複し、変換・コピー・同期処理が増えます。

そのため、次を同時に最小化します。

```text
prediction / task loss
+ static program bits
+ static knowledge bits
+ dynamic state bits
+ bits read / written
+ primitive operations
+ external effects
+ induction / training / compiler cost amortization
+ verification / migration / rollback cost
+ representation-boundary cost
+ held-out and shifted-task regret
```

## ランタイム方針

- semantic understandingをdense neural residualへ丸投げしない
- 最終バイナリにニューラル重みを残さない研究経路を優先する
- 記憶、推論、計画、創造、文章、コード編集を別ランタイムにしない
- 一つの正準シンボル表、一つの疎な事実状態、一つの書換え原理を共有する
- 汎用IRは部分評価・規則融合・状態最小化し、実行時の抽象化overheadを消す
- 新命令・cache・indexは、生涯目的を改善した場合だけ採用する
- 成功値だけでなく、held-out失敗と探索爆発もCIへ固定する

## Phase 1: 最小予測状態

既知の確率過程からHankel行列を作り、最小線形予測次元と離散因果状態を復元しました。

- IID過程: Hankel rank 1、因果状態1、実行時状態0 bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態の密なSVD表現: 576 bytes、64 MAC/記号
- 同じ予測を離散因果状態へ結晶化: 48 bytes、0 MAC/記号
- 最大特異値gapの誤判定を、分割データ由来のnoise floorで修正

詳細: [`results/phase1.md`](results/phase1.md)

## Phase 2: 遷移法則の因数分解

K個の独立ビットを持つkey-value予測言語を使い、状態情報量と遷移プログラム記述長を分離しました。

- 厳密予測には最低K bit必要
- 平坦な因果状態表はready状態だけで `2^K` 個
- K=32の疎な平坦表でも約5.6TB
- 因数分解レジスタ機械はK bit＋定数規則
- dense FP32状態よりデータ書込み量を約6656分の1へ削減

詳細: [`results/phase2.md`](results/phase2.md)

## Phase 3a: MDLによる構造探索

必要なレジスタ数を与えず、0〜16スロットと書込み規則を探索しました。

- 100,000トークンの8-key言語から8スロット・offset 0を選択
- 15,486回のQUERYを0誤り
- 少ないslotは誤り、多いslotは余分な記述bitで敗北

詳細: [`results/phase3a.md`](results/phase3a.md)

## Phase 4a: コンパイル済み超軽量バイトLM

held-out NLL改善が規則自身の記述長を上回る文脈だけを残し、failure-link状態機械へコンパイルしました。

- 学習625,748 bytes、別seedテスト155,073 bytes
- 選択規則608、コンパイル状態696
- 実行時状態10 bit
- 独自 `.mplm` バイナリ10,999 bytes
- 0.468469605 BPB
- 平均1.015644遷移確認/byte

これは局所表層予測の橋渡し実験であり、open-domain意味理解の主張ではありません。

詳細: [`results/phase4a.md`](results/phase4a.md)

## Phase 4b〜4c: 意味と創造性のno-neural設計

- 未知固有名詞はexact symbol tableへ一度だけ保存
- 世界状態はtimestamp付き疎関係として更新・撤回
- 質問はqueryへコンパイルし、関連規則だけ実行
- 回答はproof traceから生成
- 創造性は意味program変形、候補生成、criticへ分離
- 外部知識量・検索量・候補探索量も総コストへ含める

設計:

- [`docs/phase4b_minimal_semantic_machine.md`](docs/phase4b_minimal_semantic_machine.md)
- [`docs/phase4c_creative_semantic_machine.md`](docs/phase4c_creative_semantic_machine.md)

## Phase 5a: coding / writing / agentの統一基盤

能力ごとに部品を継ぎ足さず、次の5命令を共有します。

```text
MATCH
DELETE
ADD
EMIT
CHOOSE_MIN
```

一つの `SymbolTable`、`State`、`Rule`、疎規則index、MDL探索器で、コード編集、文章構成、行動計画を同じ基盤上で解きました。

詳細:

- [`results/phase5a.md`](results/phase5a.md)
- [`docs/phase5_unified_work_machine.md`](docs/phase5_unified_work_machine.md)

## Phase 6: 下限、スケーリング、生涯大域最適

- 256段chain: 平坦規則5,376bit → 因数分解43bit、位置状態は下限9bit
- 20bit parity: 任意表1,048,576bit → 規則27bit＋状態1bit
- 答えに必要な20bit読取りや256依存stepは不可避として残す
- Value of Computationで、判断を変える期待値が費用を上回る場合だけ追加思考
- 16-query workloadで局所commit 16,384に対し生涯大域選択4,032

詳細:

- [`docs/phase6_scaling_and_open_ended_intelligence.md`](docs/phase6_scaling_and_open_ended_intelligence.md)
- [`docs/phase6b_minimal_choice_machine.md`](docs/phase6b_minimal_choice_machine.md)
- [`docs/phase6c_global_optimization.md`](docs/phase6c_global_optimization.md)
- [`results/phase6a.md`](results/phase6a.md)
- [`results/phase6c.md`](results/phase6c.md)

## Phase 7a: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%まで低下
- 観測失敗表現を個別rewriteすると、別系列では再び50%
- 10,000回の反復質問でもpersistent state量は増加なし
- 4,096事実でもindexed lookupは1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証のtask loopを実装
- コード候補探索は候補数に比例し、実リポジトリには未達

詳細:

- [`docs/phase7_scaling_to_conversation.md`](docs/phase7_scaling_to_conversation.md)
- [`results/phase7a.md`](results/phase7a.md)

## Phase 8a: 残差駆動の意味プログラム誘導

固有名詞と場所を型付きslotへ置換し、1〜2個の構造・文字特徴からなる最小規則をMDLで選びました。

| parser | 未知組合せ | distractor拒否 | 未知言い換え |
|---|---:|---:|---:|
| exact surface | 0.0% | 100.0% | 0.0% |
| typed slot templates | 100.0% | 100.0% | 0.0% |
| induced feature program | 100.0% | 87.5% | 33.3% |

- entity/location各128: 表面列挙22,112,432bit → program＋symbol 13,989bit
- 約1,580.7倍削減
- 別の言い換え系列では16.7%で、open-domain意味理解は未達

詳細:

- [`docs/phase8_residual_semantic_program_induction.md`](docs/phase8_residual_semantic_program_induction.md)
- [`results/phase8a.md`](results/phase8a.md)

## Phase 8b: interaction traceから潜在操作・役割を誘導

intent名やentity/location型をmain learnerへ渡さず、`pre-state / utterance / post-state / response`から操作を逆算しました。

- 9/9 interactionから操作を復元
- 表面intentではなく `SET(key,value) / GET(key)` を誘導
- key/valueの潜在role purity 100% / 100%
- exact surface objective 4,130
- untyped symbols objective 1,964
- 2 latent roles objective 953、held-out 100%
- `remember / move / query` 202bit → state effect `SET / GET` 163bit
- 新symbolは文字列bitだけを払い、追加rule 0bitで再利用

詳細:

- [`docs/phase8b_latent_roles_and_operations.md`](docs/phase8b_latent_roles_and_operations.md)
- [`results/phase8b.md`](results/phase8b.md)

## Phase 8c: 複数relation・部分観測・noise・遅延effect

意味名を持たない3つのopaque effect channelへ、言語を接地する実験です。

- 27 traces、正解operation 24
- full SET 6/6、partial SET 3/3、delayed SET 3/3、GET 12/12
- 生のoperation推定: recall 100%、precision 96%
- 偶然のexogenous changeを1本だけ誤相関
- support 1 schemaは誤規則を保存し、held-out 94.7%
- support 2＋confidence schemaは誤規則を除去し、held-out 19/19

| hypothesis | bits | validation | lifetime objective |
|---|---:|---:|---:|
| exact surface | 6,400 | 36.8% | 18,688 |
| support 1 schema | 3,983 | 94.7% | 5,007 |
| robust multi-relation schema | 3,703 | 100.0% | 3,703 |

実行時は12規則の線形走査ではなく、固定literal cueでrouteします。

- linear: 12 rule checks/input
- indexed: 平均0.789 rule checks/input
- index pointer 48bitもdescription lengthへ含む

新しいopaque relationは、2本の一貫したtraceから1規則・357bitで追加し、未観測key/value組合せを100%処理しました。

ただし、effect channel IDは観測可能であり、relation partition自体をraw interactionから発見したわけではありません。

詳細:

- [`docs/phase8c_multi_relation_semantics.md`](docs/phase8c_multi_relation_semantics.md)
- [`results/phase8c.md`](results/phase8c.md)

## 次の実験

Phase 8dではopaque channel IDを直接使わず、複数sensor stream、action result、遅延した観測の共変動からrelation partition自体を探索します。

- relationのmerge / split / deleteを競わせる
- 2〜8 step delayed effect
- hidden intermediary state
- probabilistic effectとcontradiction
- exhaustive oracleが可能な小世界でregretを測る
- 会話、文章、コード、tool actionを混在させる

採用条件は引き続き、held-out regretの削減がprogram、knowledge、state、読書き、operation、探索、検証、移行費用を上回ることです。

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
python -m unittest discover -s tests -v
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub Actionsで全テストと全実験をゼロから再現します。
