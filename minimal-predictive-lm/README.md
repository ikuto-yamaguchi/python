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

結果:

- IID過程: Hankel rank 1、因果状態1、実行時状態0 bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態の密なSVD表現: 576 bytes、64 MAC/記号
- 同じ予測を離散因果状態へ結晶化: 48 bytes、0 MAC/記号
- 最大特異値ギャップは真のrank 5をrank 1と誤判定
- 2分割データから推定した演算子ノイズ床ではrank 5を復元

詳細: [`results/phase1.md`](results/phase1.md)

## Phase 2: 遷移法則の因数分解

K個の独立ビットを持つkey-value予測言語を使い、状態情報量と遷移プログラム記述長を分離しました。

結果:

- 厳密予測には最低Kビット必要
- 平坦な因果状態表はready状態だけで `2^K` 個
- K=32の疎な平坦表でも約5.6TB
- 因数分解レジスタ機械はKビット＋定数規則で同じ予測を実現
- dense FP32状態よりデータ書込み量を約6656分の1へ削減

詳細: [`results/phase2.md`](results/phase2.md)

## Phase 3a: MDLによる構造探索

必要なレジスタ数を与えず、0〜16スロットと書込み規則を探索しました。

結果:

- 100,000トークンの8-key言語から8スロット・offset 0を自動選択
- 15,486回のQUERYを0誤り
- 7スロットは940誤り、6スロットは1,902誤り
- 9〜16スロットは正確だが、余分な状態・プログラムbitで敗北

詳細: [`results/phase3a.md`](results/phase3a.md)

## Phase 4a: コンパイル済み超軽量バイトLM

held-out NLL改善が規則自身の記述長を上回る文脈だけを残し、failure-link状態機械へコンパイルしました。

決定的micro-corpusでの結果:

- 学習625,748 bytes、別seedテスト155,073 bytes
- 選択規則608、コンパイル状態696
- 実行時状態10 bit
- 独自 `.mplm` バイナリ10,999 bytes
- 0.468469605 BPB
- 平均1.015644遷移確認/byte
- 保存・再読込後もBPB完全一致

| model | BPB | compact bytes |
|---|---:|---:|
| fixed 3-gram | 0.557296466 | 16,294 |
| fixed 4-gram | 0.531891477 | 33,383 |
| fixed 8-gram | 0.727351516 | 399,426 |
| **compiled residual LM** | **0.468469605** | **10,999** |

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

一つの `SymbolTable`、`State`、`Rule`、疎規則index、最小記述長探索器で、三種類のmicro-taskを解きます。

| task | result | objective | rule checks |
|---|---|---:|---:|
| coding | `f(x)=3*x+1` の全テスト通過patch | 6 bit | 81 |
| writing | goal / method / caveatを満たす3文 | 25 bit | 6 |
| agent | lab→hall→vault→pickup | 3 bit | 5 |

共有シンボルは117個で、IDは7bitです。

この結果の意味は、問題が難しいことではありません。**コード編集、文章構成、行動計画が別々の内部世界や別々の実行器を必須としない**ことを、最小コードで確認した点にあります。

詳細:

- [`results/phase5a.md`](results/phase5a.md)
- [`docs/phase5_unified_work_machine.md`](docs/phase5_unified_work_machine.md)

## 後付け肥大化を防ぐ規則

`memory`、`stack`、`counter`、`planner`、`creativity operator`、`AST editor`、`tool caller` は、最初から独立モジュールにしません。

まず既存命令のマクロとして表現し、対象ワークロードへ部分評価します。新しいネイティブ命令は、次の差が正になる場合だけ採用します。

```text
existing lifetime cost
- new primitive lifetime cost
- opcode bits
- compiler / serializer bits
- representation-conversion cost
- verification cost
```

一つのベンチマークだけ速くなる専用部品は、原則としてマクロのまま残します。

## 最終用途を最初から評価する

後から機能を足さないため、研究評価には初期段階から次を含めます。

### Coding

- 未知リポジトリの局所修正
- 複数ファイル依存
- テスト・型・ビルド失敗からの修正
- 読んだコードbit、patch bit、テスト実行数、tool effect数

### Writing

- 要件・事実・文体制約
- 長文の論旨・参照一貫性
- 差分推敲
- 新規性と適切さ
- 読んだ知識bit、談話状態bit、候補数

### Agent

- 部分観測
- 長期タスク
- 失敗復旧
- 外部操作と副作用確認
- 観測bit、行動数、再計画数、動的状態bit

## 次の実験

Phase 5bでは、別々のデモではなく一つのepisodeで次を連続実行します。

```text
仕様文を読む
-> 同じ正準状態へ要件を保存
-> コードを修正
-> test toolを実行
-> 失敗なら同じ状態上で再計画
-> 結果報告を書く
```

文章理解、コード状態、テスト結果、計画、報告内容を一度だけ保持し、モジュール境界のコピーを発生させないことを検証します。

その後、外部作用を一つの `EFFECT` 境界として追加し、汎用IRをタスク専用状態機械へ自動コンパイルします。

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
python -m unittest discover -s tests -v
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub Actionsで全テストと全実験をゼロから再現します。
