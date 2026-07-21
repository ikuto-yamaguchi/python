# 系列D Cycle 003 — Open-View Sleep Consolidation

## 結論

未知の日本語表現を即座に低速記憶へ固定せず、高速領域の暫定view仮説として保持し、異なるepisodeで既知viewとの対応が繰り返し確認された場合だけ睡眠型統合する `Open-View Sleep Consolidation` を検証した。

最大540学習例・3 seed平均で、閉集合記憶は未知viewを統合できず0だった。一方、睡眠型記憶は3関係系列中2系列の未知viewを低速schemaへ追加し、統合後の未知view一回提示と40件干渉後の最新値上書きで0.6667を得た。単独で一度だけ現れた未知view、さらに別の第4構文は0のままだった。

したがって、**未知表現を反復するcross-view証拠が得られるまで暫定保持し、その後にだけ書込み規則へ統合する**という更新原理は限定的に支持された。しかし自由日本語のopen-set意味理解としては反証である。

## 他4系列との重複表

| 系列 | 最新中心機構 | 継承した知見 | 本サイクルの非重複点 |
|---|---|---|---|
| A | 能動識別型予測状態 | 内部反復だけで決着しない候補には追加観測が必要 | 確認発話生成ではなく、追加観測後の記憶固定化条件を研究 |
| B | Cross-view MDL商 | 複数viewは一部同義表現を束ねるが、prototype保存は線形増加する | 圧縮商ではなく、新規viewを低速write/read ruleへ定着するかを検証 |
| C | 対照介入必要性 | 操作／無操作対照は下流監査信号になる | 因果辺を作らず、episode記憶のview獲得と干渉を研究 |
| E | 学習factor緩和 | 候補構造が同型なら重み学習は無効 | energy緩和を使わず、反復cross-view証拠による再固定化を検証 |

重複する候補として、A型の確認選択、B型のMDL商形成、C型の因果昇格、E型のfactor graph緩和は採用しなかった。

## 仮説

既存schemaへ一致しない表現を直ちに棄却または固定せず、次の二段階で扱う。

1. **高速暫定仮説**: 未知文と、同じepisodeを記述する既知viewから、匿名の二値境界とview pattern候補を生成する。
2. **睡眠型低速統合**: 同じpatternが異なるepisode固有値で2回以上再現し、可逆再構成できる場合だけ既存schemaへ追加する。

新viewの意味名、entity/value slot名、固定ontologyは与えない。既知viewで抽出された二つのepisode-local値が未知文にも再出現することだけを利用する。

予測は、閉集合方式より未知view統合後の一回提示と干渉後上書きが改善し、単発の偶然候補と無関係な対を固定化しないことである。

## 実装

`open_view_sleep_consolidation.py`

- seed viewはanswer spanなしのcross-view反統一で誘導
- 既知viewへ一意に照合できるepisodeだけを新view候補生成へ使う
- episode固有の二つの値が未知文にも現れる場合だけ匿名patternを作る
- 異なる値組でsupport 2以上になったpatternだけsleepで統合
- 高速bindingはtimestamp付き双方向束縛
- query時は6本のquery linkだけを読み、最新bindingを推論状態へ戻す

使用していないもの:

- 回答ラベル・answer span
- 意味slot名・固定ontology
- 形態素解析辞書
- Transformer・外部LLM
- RAG・ベクトルDB
- 問題別分岐

ただしデータは3関係系列の制御日本語であり、生の自由対話コーパスではない。

## 実験

- 学習規模: 48 / 180 / 540
- seed: 1 / 7 / 19
- 比較:
  - `ClosedMemory`: 学習済みviewだけを使用
  - `SleepMemory`: 新viewを暫定保持し反復後に統合
- 学習済みviewの一回提示
- 未知viewを単独で一度だけ観測
- 既知viewとの対応を18 episodeで提示後にsleep
- sleep後の未知view一回提示
- さらに未知の第4構文
- 40件の無関係記憶を挟んだ最新値上書き
- 無関係なcross-view pairの拒否
- model bytes / Peak RSS / 学習時間 / 推論時間 / query reads / schema数 / binding数

再現:

```bash
python research/intelligence_swarm/tracks/D_memory_learning/open_view_sleep_consolidation.py
```

## 最大540例・3 seed平均

| 指標 | ClosedMemory | SleepMemory |
|---|---:|---:|
| 学習済みview一回提示 | 0.6667 | 0.6667 |
| 単独未知view・sleep前 | 0.0000 | 0.0000 |
| 反復対応後の未知view | 0.0000 | **0.6667** |
| 完全に新しい第4構文 | 0.0000 | 0.0000 |
| 干渉後の最新値 | 0.0000 | **0.6667** |
| 無関係pair拒否 | 0.0000 | **1.0000** |
| model bytes | 28,664 | 32,749 |
| query reads | 6 | 6 |
| inference | 0.01265 ms | 0.01245 ms |
| 追加view | 0 | 2 |
| binding | 522 | 624 |

- 学習時間: 約0.0324秒
- Peak RSS: 398,024 KiB（Python runtime込み）
- モデルは1GB未満だが、弱いスマートフォン実機では未測定
- 推定query計算量: O(Q·L)、Q=6
- 新view提案計算量: O(S·L²)に近い文字反統一。今回S=3で小さいが、長文スケーリングは未検証

## 支持された部分

1. 単独の未知表現を低速schemaへ即時固定せず、暫定仮説として保持できる。
2. 異なるepisodeで同じcross-view対応が再現した場合だけ、2つの新viewを低速write/read schemaへ追加できた。
3. 統合されたviewは新しいentity/valueの一回提示を書込み、40件の干渉後も最新値へ上書きできた。
4. query readsは学習例数やbinding数ではなく6本のlinkに固定され、知識量と読出し量を分離した。
5. episode-local値を共有しない無関係pairは全て拒否した。

## 構造的反証

現在の仮説を汎用知能経路としては棄却する。

1. 3関係系列中1系列でseed viewの境界誘導が失敗し、最大性能は0.6667に留まった。文字反統一が助詞を値区間へ吸収し、schema/query bindingの向きが崩れた。
2. 単独の未知表現は0。未知文だけから構造・意味を生成できない。
3. 第4構文は0。sleepは観測されたcross-view同値化を増やすだけで、開集合一般化ではない。
4. episode identityとvalueが未知文・既知文で完全に同じ表面文字列として現れる必要がある。代名詞、表記揺れ、同義語、暗示的照応は扱えない。
5. 何が同一episodeかというcross-view groupingは実験器から与えられる。実対話から自律発見していない。
6. 記憶値の参照・上書き以外の推論、計画、因果、反実仮想、自由生成、自由対話へ統合していない。
7. 選択的忘却、長期容量制御、schema競合、誤統合からの再固定化解除を実装していない。
8. 自由日本語統合ゲートは未達である。

## 系列D固有の進展

Cycle 002では「回答なしでも観測済みview間の書込み規則を作れる」と分かった。今回さらに、

> **新しい表現を一度見ただけで意味記憶へ昇格させず、異なるepisodeでcross-view対応が反復した場合にだけ低速の書込み規則へ定着させると、閉集合viewを安全に拡張できる。**

ことを限定的に実測した。

同時に、最大ボトルネックは記憶容量や忘却率より上流の、**境界不確実性を保持した複数binding仮説生成**であると明確になった。単一の文字反統一境界を即決したため1系列が失敗した。

## 他系列へ返す知見

- **Aへ**: 追加確認で得た一回の応答を直ちに状態へ固定せず、異なる時点で再確認された候補だけを低速状態へ統合すべき。
- **Bへ**: cross-view MDL programは圧縮利得だけでなく、新しい未ラベル観測を高速bindingへ正しく書けるか、反復時にmodel bytesがprototype数へ線形増加しないかで評価すべき。
- **Cへ**: 因果操作schemaを保存する前に、別episode・別identityで同じ対照構造が再現するまで暫定記憶へ留める必要がある。
- **Eへ**: 新view候補は単一境界へ即決せず、助詞を含む／含まない境界、slot順序、binding方向が異なるfactor graphとして保持し、後続証拠で緩和すべき。

## 次の仮説

**Boundary-Uncertain Sleep Consolidation with Reversible Rejection**

次は未知文ごとに、以下が異なる少数の暫定仮説を保持する。

- 匿名区間の左右境界
- 助詞をslotへ含めるか
- slot順序
- query key側
- 双方向bindingの向き
- 既存schemaとの対応

統合条件は、

1. 元文を可逆再構成できる
2. 異なるepisodeで再現する
3. query結果を改善する
4. 既存bindingと衝突しない
5. 介入後もidentityを保存する
6. model bytesと読出し量を過度に増やさない

ことの同時成立とする。誤統合が後続反例で判明した場合には低速schemaを再び暫定状態へ戻す再固定化解除も検証する。

成功条件は、3関係すべてで未知view統合を成立させ、完全未見構文・表記揺れ・代名詞・干渉・誤統合回復を同時改善することである。

- highschool_level_passed: false
- native_japanese_communication_passed: false
- weak_smartphone_verified: false
- completion: false
