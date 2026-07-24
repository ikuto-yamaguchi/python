# 系列A Cycle 010 — Raw Character-Class Birth under Episode-Local Syntax

## 統合前提

GOV-010 / AF-011に従い、全episodeへ単一の語順・segmentation templateを強制しない。語順、改行、余剰文字はepisode-local nuisance orbitとして周辺化し、重複しない外部witness集合が同じ構造核へ独立再収束するかを監査した。

## 仮説

**Independent-Witness Raw Character-Class Birth under Episode-Local Syntax**

opaque対象文字集合・opaque操作文字集合をlearnerへ与えず、8文字のraw alphabetから、3文字の対象候補、3文字の操作候補、2文字のnuisance候補、対象mapping、操作mappingを共同探索する。prefix / suffix / interleave / reverse / 改行形式は各episodeで局所的に変化できる。

重複しない2つの5-witness集合が同じ構造核へ再収束することを要求した。

## 比較

- Active witness
- Random witness
- Outcome shuffle
- Factor/class shuffle

final testのafterは候補生成、witness選択、rankingに使用していない。

## 3 seed平均

| 条件 | Set1 survivor | Set2 survivor | Intersection | Prospective | Inverse | 未知語順 | 改行 | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Active | 1.00 | 1.00 | 1.00 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Random | 2.00 | 2.00 | 1.00 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Outcome shuffle | 0.00 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Factor shuffle | 1.00 | 1.00 | 1.00 | 0.357 | 0.357 | 0.390 | 0.326 | 0.357 |

Activeは3/3 seedで、各witness集合単独から同じunique構造へ再収束した。Randomは各集合に2候補を残したが、両集合のintersection後は真構造1件へ収束し、最終外部能力はActiveと同率だった。

## 判断

**character-class oracle除去の上限仮説は支持したが、能力上の進歩は未認定。G1未達。**

今回初めて、対象文字集合・操作文字集合をoracleで与えず、raw alphabetから両classとmappingを外部結果により再構成できた。Factor shuffleで全外部能力が約0.33〜0.39へ低下し、文字classが単なる診断値ではなくprospective/inverse/counterfactual利用に必要であることも確認した。

ただし正式なSemantic Identity Birthではない。

1. ActiveとRandomの最終能力差が0で、+0.10進歩条件を満たさない。
2. 3対象・3操作・2nuisanceというclass cardinalityを既知としている。
3. `noop / mark / swap`というoperation familyとその意味を既知としている。
4. raw自然日本語、Rename、主語省略、複数段落、未知relation、別opaque domain転移は未評価。
5. finite exhaustive version spaceの上限実験である。

正式分類は **oracle_operation_family_and_cardinality_upper_bound**。

## 得られた知見

- 全episode共通のsurface templateは不要で、episode-local nuisance orbitのままでも文字classを外部結果から同定できる。
- 独立witness集合のintersectionはRandomでも正しい構造核を回復するため、Activeの優位はwitness集合単独での一意化効率に限られる。
- 次に外すべきoracleはtoken境界ではなく、class cardinalityとoperation familyである。
- classを誤結合するとforward・inverse・counterfactualが同時に崩れるため、対象class候補は再利用可能identity proposalの必要成分になり得る。

## 他系列への返却

- B: operation familyを既知とせず、外部結果から操作family・arity・argument linkを同時birthする必要がある。
- C: class cardinality候補とoperation-family候補を含む共同version spaceで、object permanenceと因果方向を監査する。
- D: raw classは再収束したがoracle family/cardinalityが残るためmemory eligible unitは0。
- E: AF-011は継続可能。Active=Random最終能力同率なので進歩認定不可。

## 次の仮説

**Nonparametric Role-Inventory Birth from Independent Witness Compression without Fixed Class Cardinality**

次は3/3/2という文字class数を与えず、role inventory数、nuisance文字数、対象class数、操作class数、operation family、arityを可変候補として保持する。重複しないwitness集合が同じ最小構造核へ再収束し、未使用token・主語省略・複数段落・自由日本語でRandom / class-count shuffle / family shuffle / outcome shuffleを0.10以上上回るか検証する。

## 資源

- 初期候補: 20,160
- 生存モデル平均: 18 bytes
- Peak RSS: 113,656 KiB
- 3 seed総実行時間: 7.1134 sec
- 推定演算量: O(2 × B × H × Q), H=20,160, B=5
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## Status

- Semantic Identity Gate G1: 未達
- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
