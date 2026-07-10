# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測・意味処理・仕事実行に必要な**最小記憶**と**最小計算**を、数学的下限と実測コストから逆算する研究です。

最終目標は、コーディング、文章作成、ツール利用を伴うエージェント処理までを、一つの最小実行基盤で扱うことです。

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
+ training and compiler cost / expected deployments
+ representation-boundary cost
```

## ランタイム方針

- semantic understandingをdense neural residualへ丸投げしない
- 最終バイナリにニューラル重みを残さない研究経路を優先する
- 記憶、推論、計画、創造、文章、コード編集を別ランタイムにしない
- 一つの正準シンボル表、一つの疎な事実状態、一つの書換え原理を共有する
- 汎用IRは最後に部分評価・規則融合・状態最小化し、抽象化overheadを消す
- 新命令は、生涯MDLで導入費用を上回る削減が確認できた場合だけ採用する

## Phase 1: 最小予測状態

既知の確率過程からHankel行列を作り、最小線形予測次元と離散因果状態を復元しました。

- IID過程: Hankel rank 1、因果状態1、実行時状態0 bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態の密なSVD表現: 576 bytes、64 MAC/記号
- 同じ予測を離散因果状態へ結晶化: 48 bytes、0 MAC/記号
- 最大特異値ギャップは真のrank 5をrank 1と誤判定
- 2分割データから推定した演算子ノイズ床ではrank 5を復元

詳細: [`results/phase1.md`](results/phase1.md)

## Phase 2: 遷移法則の因数分解

K個の独立ビットを持つkey-value予測言語を使い、状態情報量と遷移プログラム記述長を分離しました。

- 厳密予測には最低Kビット必要
- 平坦な因果状態表はready状態だけで `2^K` 個
- K=32の疎な平坦表でも約5.6TB
- 因数分解レジスタ機械はKビット＋定数規則で同じ予測を実現
- dense FP32状態よりデータ書込み量を約6656分の1へ削減

詳細: [`results/phase2.md`](results/phase2.md)

## Phase 3a: MDLによる構造探索

必要なレジスタ数を与えず、0〜16スロットと書込み規則を探索しました。

- 100,000トークンの8-key言語から8スロット・offset 0を自動選択
- 15,486回のQUERYを0誤り
- 7スロットは940誤り、6スロットは1,902誤り
- 9〜16スロットは正確だが、余分な状態・プログラムbitで敗北

詳細: [`results/phase3a.md`](results/phase3a.md)

## Phase 4a: コンパイル済み超軽量バイトLM

held-out NLL改善が規則自身の記述長を上回る文脈だけを残し、failure-link状態機械へコンパイルしました。

- 学習625,748 bytes、別seedテスト155,073 bytes
- 選択規則608、コンパイル状態696
- 実行時状態10 bit
- 独自 `.mplm` バイナリ10,999 bytes
- 0.468469605 BPB
- 平均1.015644遷移確認/byte
- 保存・再読込後もBPB完全一致

これは局所表層予測の橋渡し実験であり、open-domain意味理解の主張ではありません。

詳細: [`results/phase4a.md`](results/phase4a.md)

## Phase 4b〜4c: 意味と創造性のno-neural設計

意味理解、長期記憶、質問応答、推論を、明示的なシンボル・疎な関係・実行可能な規則へ分解します。

- 未知固有名詞は正確なsymbol tableへ一度だけ保存
- 世界状態はtimestamp付き疎関係として更新・撤回
- 質問はqueryへコンパイルし、到達可能な規則だけ実行
- 回答はproof traceから生成
- 創造性は意味プログラムの変形、候補生成、criticへ分離
- 外部知識量・検索量・候補探索量も総コストに含める

設計:

- [`docs/phase4b_minimal_semantic_machine.md`](docs/phase4b_minimal_semantic_machine.md)
- [`docs/phase4c_creative_semantic_machine.md`](docs/phase4c_creative_semantic_machine.md)

## Phase 5a: coding / writing / agentの統一基盤

能力ごとに部品を継ぎ足すのではなく、次の5命令だけを共有する最小実験を作りました。

```text
MATCH
DELETE
ADD
EMIT
CHOOSE_MIN
```

一つの `SymbolTable`、`State`、`Rule`、疎規則index、最小記述長探索器で、コード編集、文章構成、行動計画を同じ基盤上で解きます。

詳細:

- [`results/phase5a.md`](results/phase5a.md)
- [`docs/phase5_unified_work_machine.md`](docs/phase5_unified_work_machine.md)

## Phase 6: 下限、スケーリング、生涯大域最適

- 256段chain: 平坦規則5,376bitから因数分解43bit、位置状態は下限9bit
- 20bit parity: 任意表1,048,576bitから規則27bit＋状態1bit
- Value of Computationにより、判断を変える期待値が計算費用を上回る場合だけ追加思考
- 16-query workloadで局所commit 16,384に対し大域選択4,032

詳細:

- [`docs/phase6_scaling_and_open_ended_intelligence.md`](docs/phase6_scaling_and_open_ended_intelligence.md)
- [`docs/phase6b_minimal_choice_machine.md`](docs/phase6b_minimal_choice_machine.md)
- [`docs/phase6c_global_optimization.md`](docs/phase6c_global_optimization.md)
- [`results/phase6a.md`](results/phase6a.md)
- [`results/phase6c.md`](results/phase6c.md)

## Phase 7a: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3%から82.4%、100%へ改善
- 砕けた別表現: 50%まで低下
- 10,000回の反復質問でもpersistent state量は増加なし
- 4,096事実でもindexed lookupは1 read
- test失敗から証拠保存、再試行、最終検証までの小さなtask loopを実装
- コード候補探索は候補数に比例し、実リポジトリには未達

詳細:

- [`docs/phase7_scaling_to_conversation.md`](docs/phase7_scaling_to_conversation.md)
- [`results/phase7a.md`](results/phase7a.md)

## Phase 8a: 残差駆動の意味プログラム誘導

固有名詞と場所を型付きslotへ置き換え、1〜2個の構造・文字特徴からなる最小規則をMDLで選びました。

| parser | 未知組合せ | distractor拒否 | 未知言い換え |
|---|---:|---:|---:|
| exact surface | 0.0% | 100.0% | 0.0% |
| typed slot templates | 100.0% | 100.0% | 0.0% |
| induced feature program | 100.0% | 87.5% | 33.3% |

失敗した4構文を残差例として再学習すると、同じ構文を別の固有名詞へ適用する精度は100%になりましたが、別の言い換え系列では16.7%でした。表面パターンを超えた型・述語・目的の自動発見は未達です。

表面文を全列挙する場合と比較すると、entity/locationが各128個のとき:

- exact surface: 22,112,432 bit
- induced program＋symbol: 13,989 bit
- 約1,580.7倍の削減

詳細:

- [`docs/phase8_residual_semantic_program_induction.md`](docs/phase8_residual_semantic_program_induction.md)
- [`results/phase8a.md`](results/phase8a.md)

## 次の実験

Phase 8bではentity/location型やintent labelを外から与えません。同じ内部状態から異なる正解行動が要求された衝突を集め、衝突を分離する最小の型、predicate、relation、parameterized programを提案します。

採用条件は、held-outの会話・文章・コード・tool taskで減るregretが、program bit、動的状態、読書き、探索、検証、移行費用を上回ることです。

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
python -m unittest discover -s tests -v
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub Actionsで全テストと全実験をゼロから再現します。
