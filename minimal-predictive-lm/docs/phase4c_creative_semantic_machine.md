# Phase 4c: Creative Semantic Machine

## 問い

no-neuralな最小意味機械へ進むと、LLMが持つような創造性を失わないか。

結論: 何も追加しなければ失う。正確な記号推論器は既知規則の実行には強いが、候補空間を広げる機構がなければ、意外な連想・新しい構成・表現の揺らぎを生まない。

したがって、創造性を密なニューラル分布へ戻すのではなく、次の二つへ明示的に分離する。

1. Candidate generator: 新しい意味プログラム候補を安く生成する
2. Critic: 新規性、妥当性、有用性、整合性、コストを測る

## 最終ランタイム制約

- dense neural layer: 0
- dense matrix multiplication: 0
- serialized neural weights: 0
- 候補生成と評価の全状態bit、読書きbit、命令数を計測
- ランダム性はseedと小さな確率表だけで表現
- 外部知識庫の保存量と検索量も総コストへ含める

## 創造性の分解

創造性を単一スコアとして扱わない。

- novelty: 既知候補からどれだけ離れているか
- appropriateness: 問題制約を満たすか
- coherence: 世界状態と矛盾しないか
- usefulness: 目標関数を改善するか
- surprise: 低確率だが説明可能な結合か
- compression gain: 複数事例を短い新規則で説明できるか

## 候補生成プリミティブ

意味プログラムや概念グラフへ、疎な変形だけを適用する。

- SUBSTITUTE: 同型の役割を別概念へ置換
- ANALOGIZE: 関係グラフの部分同型を別領域へ写像
- COMPOSE: 2つの既存プログラムを接続
- INVERT: 因果、主体、目的、順序を反転
- RELAX: 制約を1つだけ緩和
- STRENGTHEN: 制約を1つ追加
- SCALE: 数、時間、空間、主体数を変換
- COUNTERFACTUAL: 1事実だけ反転した世界を実行
- MUTATE-RULE: 既存規則の引数・条件・結果を局所変更
- INVENT-SYMBOL: 複数事例を短く説明する新概念を導入

各演算は固定命令長を持ち、生成候補は意味プログラムとして実行可能でなければならない。

## 探索

全候補を生成しない。優先度付きのquality-diversity探索を用いる。

score(candidate) =
    task_utility
  + novelty
  + explanatory_compression_gain
  - contradiction_penalty
  - program_bits
  - expected_runtime_cost
  - knowledge_reads

意味特徴の異なるセルごとに最良候補だけを保持し、似た案の大量重複を避ける。

## 暗黙のセンスをどう扱うか

人間的なセンスや文体は無料ではない。以下へ分離する。

- explicit preference rules
- examples compressed as reusable motifs
- sparse feature weights
- pairwise ranking constraints
- user-specific feedback log

高次元埋め込みへ丸ごと押し込まず、判断に必要だった特徴だけを追加する。誤評価が起きたとき、候補対を区別する最小特徴を探索し、MDL改善がある場合だけ保存する。

## 最初の検証環境

人工日本語micro-worldで、学習時に存在しない組合せを生成させる。

### Task A: 制約付き物語

入力:
- 登場人物、所有物、場所、禁止条件、目標結末

評価:
- 全制約充足
- 時間的一貫性
- 学習例との構造距離
- 物語プログラムbit数
- 生成時命令数

### Task B: 道具の新用途

オブジェクトの属性・機能・環境制約から、未観測用途を生成する。

評価:
- 実行可能性
- 新規性
- 必要な追加仮定数
- 因果説明の長さ

### Task C: 類推による発明

領域Aの関係構造を領域Bへ移し、新しい仕組みを作る。

評価:
- 構造対応率
- 目的関数改善
- 既存案との重複
- 説明可能な変換列

## 比較系

1. 決定論的意味機械のみ
2. 一様ランダム変形
3. novelty-only探索
4. utility-only探索
5. quality-diversity + MDL（本命）
6. Phase 4a局所LMのみ

創造性が単なるランダムノイズでないことを確認するため、noveltyとappropriatenessを必ず同時評価する。

## 成功条件

- held-out組合せで既知案のコピーを超える
- 制約充足率を維持したまま候補多様性を改善
- 同じ品質の候補を、token-by-token生成より少ない意味命令で作る
- 生成理由を変換列として再生可能
- 最終バイナリにニューラル成分が存在しない
- 外部知識を含む全保存bitと全検索bitを報告

## 重要な限界

広い創造性には広い知識が必要であり、その情報量は消せない。小さくできるのは主に、

- 知識の重複
- 無関係知識へのアクセス
- 候補生成の重複
- token単位の逐次思考
- 暗黙表現の冗長性

である。

目標は「11KBで全知識を持つ」ことではなく、知識・探索・表現を分離し、創造的成果1件あたりの総bit・総読書き・総命令数を最小化することとする。
