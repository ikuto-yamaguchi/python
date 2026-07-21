# 系列D Cycle 002 — Answer-Free Cross-View Predictive Rebinding

## 結論

回答区間や意味slotを教師として使わず、同じ対象・値を含む複数の表現を相互比較して匿名slotを形成し、そのslotを低速の書込み・読出し規則として使う方式を検証した。

観測済みの2種類の表現間では、一回提示記憶、言い換え、30件の干渉後の最新値上書きが全seedで成功した。一方、学習時に一度も見ていない第3構文への転移は全seed・全規模で0だった。

したがって、回答ラベル依存は除去できたが、自由日本語の開集合構造創発には到達していない。

## 他系列との重複監査

| 系列 | 中心機構 | 継承した知見 | 本サイクルとの差 |
|---|---|---|---|
| A | 未来分布による予測状態圧縮 | identityは圧縮前に保護する必要がある | 未来分布で状態を統合せず、複数表現中の同一表面を可逆束縛へ書く |
| B | MDL残差・記号候補 | 固定構造とepisode表面を分離する | 圧縮率ではなく、誘導した匿名構造を高速記憶の書込み器として使う |
| C | 介入安定イベント | 抽象機構とepisode identityを別チャネルにする | 因果操作は扱わず、保存前のentity/value再束縛だけを検証する |
| E | 複数候補の制約緩和 | 早期確定を避ける必要がある | 今回は最小の直接束縛プローブであり反復エネルギー最小化は行わない |
| D Cycle 001 | answer spanでschema誘導 | 低速schemaを未ラベル観測の書込み器にする | answer spanを完全に除去し、複数表現の共参照だけでschemaを誘導する |

予測利得だけでschemaを選ぶ案は系列Aと重複し、かつA Cycle 001で意味差を潰すことが示されたため棄却した。

## 仮説

**Answer-Free Cross-View Predictive Rebinding**

同一episodeを記述する異なる表現の間で繰り返し一致する2つの表面区間を匿名slotとして保持し、質問中に再出現するslotをentity側として同定する。低速記憶は語や答えを保存せず、次の二種類の規則だけを持つ。

1. 新しい文から2つの匿名値を取り出し、高速可逆束縛へ書く規則
2. 質問からentity値を取り出し、対応する高速束縛を推論状態へ戻す規則

これは生文検索やベクトルDBではなく、低速の構造規則とepisode-localな高速束縛を分離する機構プローブである。

## 実装境界

- Transformer、外部LLM、RAG、形態素辞書なし
- 固定ontology、person/location等の意味slot名なし
- answer span、回答ラベル、タスクIDなし
- 文字列の共参照と表現間の差分だけから匿名slotを誘導
- 高速記憶は双方の方向を可逆に保存し、timestampで最新値を選択

## 実験

- 学習規模: 48 / 180 / 540 unlabeled cross-view triples
- seed: 1 / 7 / 19
- 関係系列: 保管場所、担当者、合言葉
- 比較:
  - raw episodic storage
  - Cycle 001相当のanswer-supervised近似
  - answer-free cross-view rebinding
- 一回提示学習
- 学習済み別表現への言い換え
- 完全未見の第3構文
- entityを省略した質問での棄権
- 30件の干渉を挟んだ最新値上書き
- モデルbytes、Peak RSS、学習・推論時間、候補読出し、view数、binding数

再現:

```bash
python research/intelligence_swarm/tracks/D_memory_learning/answer_free_cross_view_rebinding.py
```

## 最大540例・3 seed平均

| 方法 | 一回提示 | 観測済み言い換え | 未見構文 | 省略時棄権 | 干渉後の最新値 | model bytes | query reads |
|---|---:|---:|---:|---:|---:|---:|---:|
| raw storage | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 110,571 | 60.5 |
| answer-supervised近似 | 0.667 | 0.000 | 0.000 | 1.000 | 0.000 | 36,880 | 540 |
| cross-view rebinding | **1.000** | **1.000** | **0.000** | **1.000** | **1.000** | 44,515 | **6** |

追加測定:

- 推論時間: 0.01238 ms/query
- 3種類のview schema
- 6本のquery link
- 評価後fast binding: 986
- 3方式合計の学習時間: 約0.0411秒 / seed
- Peak RSS: 291,612 KiB（Python runtime込み）
- モデル表現は1GB未満だが、弱いスマートフォン実機では未測定

## 支持された部分

1. answer spanなしでも、複数表現に共通するepisode固有値から匿名slotと質問linkを誘導できた。
2. 低速schemaを知識本体ではなく、新規観測を高速束縛へ変換する書込み器として利用できた。
3. 同じentityの後続観測はtimestamp付きbindingを更新し、多数の干渉後も最新値を返した。
4. 読出しは540学習例ではなく6 query linkだけを走査し、知識量と推論読出し量を分離できた。

## 構造的反証

現在の仮説を日本語汎用知能経路としては棄却する。

1. 完全未見の第3構文は全seed・全規模で0。観測済みview間の閉集合同値化にすぎない。
2. 匿名slotは、paired descriptions内で同じ表面が文字列として再出現することへ依存する。
3. 主語省略では正しく棄権するだけで、対話文脈から省略対象を解決できない。
4. syntheticな3関係系列であり、生の自由日本語、長文、入れ子、曖昧性を扱わない。
5. 記憶した値の参照・上書きだけであり、操作、因果、計画、反実仮想、自由生成へ統合していない。
6. answer-supervised baselineはCycle 001の近似であり、より強い可逆束縛・表面検索baselineとの比較が必要。

一回提示100%と言い換え100%を日本語理解の証拠とは扱わない。

## 系列D固有の進展

**記憶schemaの初期誘導にanswer spanは必須ではない。複数表現で同じepisode identityが再現する場合、その共参照を使って匿名の書込み・読出し規則を形成できる。**

ただし、この成功と未知構文を自律生成する能力は別問題である。今回の最大ボトルネックは記憶容量や更新則ではなく、既存viewに一致しない入力から新しいview仮説を生成することである。

## 他系列へ返す知見

- A: identityを保持したまま状態圧縮するには、未来類似だけでなくcross-view可逆束縛を独立チャネルとして残す必要がある。
- B: MDLで得た候補構文は、圧縮結果として保存するだけでなく、fast bindingへのwrite/read ruleとして評価すべき。
- C: 介入イベントを比較する前に、cross-viewでepisode identityを束縛すれば表面座標によるイベント断片化を減らせる可能性がある。
- E: 未知入力では複数の新規view候補を保持し、可逆再構成・将来予測・介入整合性で緩和する必要がある。

## 次の仮説

**Open-Set Multi-View Rebinding with Sleep Consolidation**

既存schemaへの照合だけでなく、未見構文が来た際に複数の新規view候補をその場で生成する。候補は次の合意で競合させる。

1. 入力の可逆再構成
2. 既存bindingとのcross-view整合
3. 後続予測改善
4. 介入後もidentityが保存されること
5. 過去の別viewを壊さないこと

高速領域で複数候補を保持し、睡眠型統合では異なる時点・表現に再出現して干渉を増やさない候補だけを低速schemaへ定着させる。次回は自然な日本語対話を含め、未見構文、主語省略の文脈解決、長期干渉、古い値の選択的忘却を同時に評価する。

- highschool_level_passed=false
- native_japanese_communication_passed=false
- weak_smartphone_verified=false
- completion=false
