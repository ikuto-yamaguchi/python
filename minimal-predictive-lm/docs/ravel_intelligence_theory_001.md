# RAVEL-1G: Reversible Abstraction Via Event Lattices

## 0. 目的

固定された完成条件を満たすための**独自の知能計算仮説**を定義する。

- 完全パッケージ <= decimal 1,000,000,000 bytes
- 弱い一般スマートフォンで高速応答
- 日本の全大学入試を、証明・論述・英作文・リスニング・面接を含め100%
- 自然な長期対話、説明、訂正、計画、指示遂行
- 普通の教材・会話・画像・音声から汎用的に能力を獲得
- Transformer、dense attention、会話長に比例するKV cacheを知能本体にしない

RAVELは既存方式を縮小したものではない。知能を「言語列の確率予測」ではなく、**観測を最小の可逆操作体系へコンパイルし、その体系を再利用・合成・自己修正する能力**として実装する。

## 1. 中心仮説

> 世界を正しく説明できる知能とは、異なる表現・対象・領域に再利用でき、前向きにも逆向きにも実行できる少数の操作で、観測変化と問いを再構成できる系である。

学習対象は固定次元の巨大な潜在ベクトルでも、単語の続きを当てる重みでもない。学習によって増える主な要素は次の4つである。

1. **Entity atoms**: 同一性を保つ実体・属性・関係の疎な識別子
2. **Reversible event programs**: 前提、効果、逆操作、保存量、例外残差を持つ可逆な操作
3. **Macro programs**: 頻繁に再利用される操作列を一命令へ再コンパイルした階層手続き
4. **Residual memory**: 一般操作で説明し切れない固有事実・出典・経験だけを保存する圧縮記憶

言語、画像、数式、音声は知能本体ではなく、この共通操作体系へ観測を接地し、実行結果を外へ戻す入出力面である。

## 2. 新しい学習原理: Explanatory Work Conservation

RAVELは単なる損失最小化ではなく、候補構造が削減した説明仕事量を測る。

候補操作 `p` の価値を次で定義する。

```
EW(p) = eliminated_residual_bits
        / (stored_program_bytes + active_execution_cost + contradiction_cost)
```

学習更新は以下を同時に満たす場合だけ採用する。

- 複数の表層・実体・領域で観測残差を削減する
- 前向き実行と逆向き実行の両方で整合する
- 既存操作との合成で新しい観測を説明できる
- 固有例の丸暗記より総保存量と総実行量を削減する
- 矛盾する証拠を消去せず、条件差として分離できる

これにより、頻出語の予測ではなく、再利用可能な因果・計算・推論操作が優先的に残る。

## 3. モデル構成

### 3.1 Delta Perception Frontend

連続する文章、画像、音声、数式から「何が同じで、何が変わったか」を疎なdelta packetとして出力する。

- byte/local-patch recurrent encoder
- 近傍のみを見る小型畳み込み・再帰処理
- modalityごとの表層特徴はここだけに閉じ込める
- 出力は固定ベクトルではなく、候補実体・関係・変化の疎な集合

### 3.2 Identity Binder

異なる名前、言い換え、視点、モダリティに現れる対象を、予測可能性と操作互換性によって同一entity atomへ束縛する。

同義語辞書は使わない。同じ操作の前提・効果として置換可能で、将来観測を同様に説明するものを同一概念候補とする。

### 3.3 Reversible Event Algebra

各event programは次を持つ。

```
preconditions -> effects
inverse_preconditions -> inverse_effects
preserved_slots
created/deleted slots
uncertainty and provenance
```

前向きに結果を予測できるだけでなく、結果から原因候補を復元できる。数学の逆算、因果推論、空所補充、誤り訂正を同じ実行機構で扱う。

### 3.4 Event Lattice

操作は平坦な辞書ではなく、条件の包含関係で束ねたlatticeになる。

- 下位: 特定条件の精密な操作
- 上位: 多数の事例に共通する一般操作
- 横方向: 同じ効果を持つ代替操作
- 逆辺: 結果から原因へ戻る操作

問いに必要な最小部分だけを起動するため、全操作を走査しない。

### 3.5 Recursive Macro Compiler

頻繁に連続実行され、まとまって再利用される操作列を新しい一操作へコンパイルする。

```
[p1, p2, p3, p4] -> macro_M
[macro_M, p5, p6] -> macro_N
```

推論深度が増えても、再利用された推論は階層化され、実行ステップは概ね対数的に圧縮される。暗記した答えではなく、再利用可能な推論経路そのものを圧縮する。

### 3.6 Residual Episodic Memory

一般操作で復元できる情報は保存しない。保存するのは以下だけ。

- 一般則から外れる残差
- 固有名詞・日時・数値・出典
- 会話上の約束、訂正、未解決事項
- 操作の信頼度を更新する反例

記憶はentity/program IDと差分を中心に持ち、原文は必要な箇所だけ圧縮保持する。

### 3.7 Constraint Workspace

質問を答え候補の生成問題ではなく、満たすべき制約集合へ変換する。

1. event latticeから関連操作を疎検索
2. 前向き・逆向き・反実仮想を並行実行
3. 保存量、次元、論理、出典の制約で枝を削除
4. 矛盾した場合は原因となる前提まで巻き戻す
5. 検証済みの世界状態・実行traceをrealizerへ渡す

### 3.8 Language and Multimodal Realizer

内部traceを日本語、数式、図、音声へ変換する小型生成器。知識や推論を重みに抱え込ませない。

- 答え
- 根拠
- 計算・証明trace
- 不確実性と不足証拠
- 訂正箇所

をworld stateから条件付き生成する。

## 4. 高校生級へ到達するスケーリング仮説

RAVELは密なパラメータ数ではなく、次の3量を増やす。

1. **Coverage**: 説明できるentity/event/constraintの種類
2. **Closure**: 前向き・逆向き・反実仮想が閉じている割合
3. **Compression depth**: 再利用推論がmacroへ階層化された深さ

能力の一次近似を次と置く。

```
capability ~= coverage * reversible_closure * macro_reuse
```

データを増やしたとき、program libraryがデータ件数と同じ速度で増えるなら失敗である。一般化が成立すれば、観測数 `N` に対し再利用program数 `P(N)` は劣線形になり、macro reuseと未知事例精度が上がる。

### 4.1 容量スケール

同じ構造のまま、以下の5点で拡張する。

| Scale | Package target | 主目的 |
|---|---:|---|
| R1 | 1 MB | 可逆event誘導とmacro形成の成立 |
| R2 | 16 MB | 言い換え・未知実体・複数領域で操作共有 |
| R3 | 128 MB | 中学教材全域、長文、継続記憶、説明生成 |
| R4 | 512 MB | 高校全教科、証明・論述・英語・図表・長期対話 |
| R5 | 900-990 MB | 全大学入試範囲、音声・画像・面接を含む完成候補 |

これは単純なサイズ目標ではない。各段階で、追加容量の大半が新しい固有例ではなく、再利用可能なentity/program/macroと必要最小限の残差へ使われることが条件である。

### 4.2 R5の暫定バイト配分

| Component | Budget |
|---|---:|
| multimodal delta frontends | 180 MB |
| entity/relation atoms and indexes | 120 MB |
| reversible event programs | 140 MB |
| macro programs and sparse planner | 100 MB |
| residual knowledge/provenance memory | 330 MB |
| Japanese/math/audio realizer | 90 MB |
| runtime metadata and safety margin | 30 MB |
| **Total** | **990 MB** |

暫定表現密度:

- entity/relation atom: 12-24 bytes
- microprogram: 32-64 bytes
- macroprogram: 48-96 bytes
- residual fact: 8-40 bytes + optional compressed source span

この密度なら、数百万の概念・操作と数千万規模の圧縮残差を1GB内に置く余地がある。必要数は実験で更新するが、dense neural weightsへ知識を全面埋込みするより、知識量と保存量を直接管理できる。

### 4.3 推論スケール

弱いスマートフォンでのactive setを固定する。

- active entity candidates: 256-1024
- active microprograms: 32-128
- active macroprograms: 8-32
- search branches: 4-16
- workspace slots: 1K-8K sparse records
- 会話履歴長に比例するdense cacheは持たない

知識総量が増えても、階層indexと条件latticeによってactive computeをほぼ一定に保つ。難問だけはmacro展開・反実仮想枝を増やしてtest-time computeを使う。

## 5. 学習経路

### Phase A: Observation-to-Event Bootstrapping

ラベル付き問題から始めない。時間的に隣接した文章・画像・操作ログから、変化を説明する最小可逆programを発見する。

### Phase B: Cross-Surface Binding

異なる言い回し・図・数式が同じprogramを起動するよう、予測結果の一致を使ってentity/program IDを統合する。

### Phase C: Macro Crystallization

教材の解説、証明、計算過程、会話修正から、繰り返し使われる操作列をmacroへコンパイルする。

### Phase D: Curriculum Expansion

小学校 -> 中学校 -> 高校へデータを増やすが、教科別モデルは作らない。既存programで説明できない残差だけが新しいprogramを生む。

### Phase E: Deliberative Self-Training

未解決問題に対し、前向き・逆向き・反実仮想探索で候補traceを作り、外部検算・シミュレーション・証拠整合で正しいtraceだけをmacro化する。自己生成文をそのまま正解として学習しない。

### Phase F: Mobile Compilation

成立したprogram latticeをID幅縮小、差分符号化、ページング、hot macro常駐、cold memory圧縮で端末向けにコンパイルする。

## 6. 既存系統との差分

RAVELは以下のどれか一つではない。

- recurrent/SSM language model: 次byte予測を知能本体にしない
- neural world model: 固定次元潜在状態を全知識の容器にしない
- program synthesis: 外部LLMや人手DSLに操作候補を依存しない
- symbolic AI: 人間が概念・述語・規則を定義しない
- retrieval system: 保存文の一致ではなく、可逆操作と制約を実行する
- latent reasoning: dense vectorを反復するのではなく、操作自体を発明・圧縮する
- mixture of experts: expertを人為的に分割せず、再利用されたevent chainからmacroが生成される

既存研究はfrontend、最適化、量子化、評価設計の参考にするが、知能コアはRAVEL固有のevent algebra、explanatory-work更新、recursive macro compilationで構成する。

## 7. 最初の実装

`ravel_event_algebra.py` に以下を実装する。

1. 状態差分から可逆microprogramを生成
2. 異なるentity名でも同じ構造変化を同一programへ統合
3. programのforward/inverse実行
4. 頻出program列をmacroへコンパイル
5. macro利用による実行ステップ削減
6. 固有残差と一般programの保存量比較

これは高校生級モデルそのものではない。RAVELの中心原理が実装可能で、表層暗記より劣線形に知識を増やせるかを最初に検証する研究プロトタイプである。

## 8. 見通しの意味

この文書でいう見通しは「何点なら合格」という評価表ではない。

> RAVEL構成を固定し、R1からR5へentity/event/macro/residual capacityと教材多様性を同時に拡張する。program libraryの成長が劣線形で、macro再利用と未知事例精度が増えるなら、1GB内で高校生級へ到達できるという技術仮説である。

このスケーリング仮説が崩れた場合はRAVELを修繕して延命せず、どの原理が崩れたかを特定し、次の独自理論へ置き換える。
