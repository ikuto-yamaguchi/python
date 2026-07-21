# 系列C Cycle 002 — Variable-Preserving Intervention Quotient

## 直近失敗

Cycle 001 の intervention-stable residual event graph は、矛盾介入の 80.8% で棄権できた一方、表面編集座標へ対象名・値・位置を混入させ、正常系列を過剰拒否した。rename、言い換え、主語省略、二段計画、自由日本語ゲートは改善しなかった。

## 他系列との重複表

| 系列 | 最新の中心機構 | 成功 | 失敗 | 今回の非重複点 |
|---|---|---|---|---|
| A | 将来分布による予測状態圧縮 | 状態数・読み出し・推論時間削減 | identity・介入差・言い換えを消失 | 受動予測でなく介入前後の可逆同一性を検証 |
| B | MDLアンカー後の残差span生成 | 未知名称span F1 0.945 | 言い換え完全一致0、意味未同定 | span境界でなく状態変化の商空間を検証 |
| D | 低速schemaと高速bindingの分離 | 一回提示・上書き1.0 | 言い換え0、answer span依存 | 保存則でなく介入イベントの同値化を検証 |
| E | 少数候補の制約緩和 | 二段計画0.821 | 手書き表面制約・既知編集候補依存 | 候補再順位付けでなくイベント表現そのものを検証 |

## 新仮説

`Variable-Preserving Intervention Quotient`

介入前状態・命令・介入後状態の文字列差分から、介入前後で不変かつ命令にも現れる区間を episode identity 候補、変化し命令に新値として現れる区間を relation-value 候補として自動分離する。identity と値をプレースホルダ化した before/command の組をイベント同値類とし、推論時は未知identityを可逆に束縛して値の置換だけを実行する。

固定の人物・場所slot、形態素辞書、手書きontology、外部LLM、RAG、問題別分岐は使用しない。

## 実験

- 学習量: 32 / 128 / 512
- seed: 1 / 7 / 19
- surface nearest-transition baseline
- quotient event induction
- 通常系列
- 全対象名を未見語へ変更
- 未学習の命令言い換え
- 同じ命令表面で状態が変わらないconfound
- 未見対象を使う二段合成
- model bytes / Peak RSS / training / inference / candidate reads / rule count

## 結果（512例、3 seed平均）

| 指標 | surface | quotient |
|---|---:|---:|
| 通常 | 1.0000 | **1.0000** |
| 未知identity rename | 0.0000 | **1.0000** |
| 未学習言い換え | 0.1167 | **0.0000** |
| confound棄権 | 0.0000 | **0.0000** |
| 未知identity二段合成 | 0.0000 | **1.0000** |
| model bytes | 61,633 | **253** |
| inference latency | 6.90 ms | **0.0253 ms** |
| candidate reads | 512 | **3** |
| induced rules | 512 | **3** |
| training time | 0.00154 s | 0.0169 s |
| Peak RSS | 393,852 KiB | 393,852 KiB |

Peak RSS は同一Pythonプロセス全体を含み、方式固有・スマートフォン実機値ではない。

## 支持された部分

- 抽象イベントと episode identity を別チャネルへ分けると、未見対象名でも同じ状態変化を適用できた。
- 同じイベントを二回逐次適用し、未見対象上で二段状態遷移を合成できた。
- 表面履歴512件を読む方式に対し、3規則・253 bytes・約0.025 msまで圧縮できた。
- データ量32から既に同じ能力へ到達し、例数追加ではなく同値類形成が主要因だった。

## 明確な反証

現在の仮説を汎用因果理解としては棄却する。

1. 未学習言い換えは0%。操作意味ではなく誘導済み文字骨格に依存する。
2. 同じ命令で状態が変化しないconfoundを拒否できず、棄権率0%。観測された変化を因果必然と誤認する。
3. 新しい値表面の形態が学習時と異なる場合、値境界を一般化できない。
4. 対象・値以外の関係、目的、制約、反実仮想、自然な計画言語を自律生成していない。
5. 自由対話、読解、自由記述、長期対話、継続学習を成立させていない。

成功は `object identity preserving state edit` に限定され、意味的な操作誘導・因果方向・目的理解ではない。

## 系列C固有の進展

介入再現性だけでは不足するが、先に identity と relation-value を可逆分離すれば、renameと合成は回復する。しかし変化が観測されたという事実だけでは、それが命令の意味または因果機構だとは確定しない。

必要条件は次の二層になる。

1. **Variable-preserving quotient:** 個体を消さずに操作同値類を形成する。
2. **Contrastive mechanism test:** 同じ表面命令の無介入・別介入・逆介入を比較し、変化の必然性を反証する。

## 他系列へ返す知見

- A: 状態圧縮はidentityを別チャネルへ保護してから行う。受動未来一致だけで統合しない。
- B: MDLでidentity/value境界候補を出した後、介入商空間の再利用利得を追加評価できる。
- D: 高速bindingを記憶する際、操作schemaは文字位置でなくidentity保存型遷移として保存する。
- E: constraint factorにはidentity保存と値変化を別factorとして入れ、さらに無介入対照で因果必然性を検査する。

## 次仮説

`Contrastive Intervention Necessity Graph`

同一または近い初期状態に対して、実行・不実行・逆操作・別対象操作の対照系列を集め、実行時のみ対象関係が変化し、不実行時には変化せず、別対象操作では対象identityが保存され、逆操作で元状態へ戻り、言い換えを跨いでも同じ対照パターンを持つ場合だけ候補イベントを因果辺へ昇格させる。

次サイクルでは命令テンプレートを固定せず、系列BのMDL残差候補を入力側の候補生成に利用し、対照介入の必要性スコアが未知言い換えとconfound拒否を同時改善するかを反証する。

- highschool_level_passed=false
- native_japanese_communication_passed=false
- weak_smartphone_verified=false
- completion=false
