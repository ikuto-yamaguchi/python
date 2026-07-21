# 系列C Cycle 009: Mechanism-Factored Intervention Tensor with Counterfactual Completion

## 結論
中核仮説は反証。既知contextごとの介入signatureを6個の小さなfactor nodeへ圧縮し、同じsurface context内の未観測operationは補完できた。しかし未知context zero-shotは0.2875、操作順序を反転した反実仮想は0.0であり、学習したのは因果機構ではなくcontext表面と結果vectorの対応だった。

## 開始時に集約した知見
- 共通STATE: 高校生級、ネイティブ日本語、弱いスマートフォン実機、完成はいずれも未達。
- A: 証拠channelの意味は時間・話者で変化し、高confidenceでも誤る。
- B: 単一episodeでafterを再現するだけではroleを識別できず、cross-episode置換probeが必要。
- D: 記憶更新先・談話焦点も候補化しないと干渉する。
- E: candidate recallが高くても、scope・revisionを分けるfactorがなければflat attractorになる。

## 重複表
| 系列 | 中心機構 | 成功 | 失敗・未解決 | C候補との重複判定 |
|---|---|---|---|---|
| A | evidence-channel change point | 非定常返答への追従 | 変化直後、open-set意味 | 証拠校正は棄却 |
| B | execution-first anti-unification | 実行監査の必要性を特定 | role候補precision | program誘導は棄却 |
| D | discourse-focus fast weights | 既知cueの干渉耐性 | 未知cue、episode grouping | 記憶統合は棄却 |
| E | learned local factors | candidate recall改善 | factor insufficiency | energy選択は棄却 |
| C | sparse intervention tensor factorization | 未観測介入補完 | 未観測機構・順序因果 | 採用 |

## 仮説
生のcontext、command、介入結果から作る疎な `context × operation × identity × prior-state` テンソルを少数機構factorへ分解すれば、未観測operation結果、別identity、操作順序変更を補完できる。

### 反証条件
1. 既知surface内だけ補完し、未知contextへ転移しない。
2. 操作順序・prior-state変更に追従しない。
3. factor数を増やすほど性能が改善せず混同する。
4. 主語省略・複数段落・計画変更が、該当構造を読まずに解ける見かけの成功になる。

## 実装
モデルへ意味slot、固定entity/value辞書、形態素解析、外部LLM、RAGを与えない。日本語contextの文字2/3-gramと、各contextで観測された疎なoperation outcome vectorだけを保持し、上位factorの局所投票で未観測cellを補完する。

これは保存文を返す検索ではなく、介入結果を内部factor stateへ統合して未観測cellを生成する最小probe。ただしoperation軸4種と制御世界は評価器側で定義されており、open-set operation創発の証拠ではない。

## 実験
- train bundle: 48 / 192 / 768
- seed: 1 / 7 / 19
- factor read rank ablation: 1 / 3 / 6
- split: seen、未知context表現、主語省略、複数段落、計画変更、未観測operation補完、操作順序反実仮想

## 768 bundle・rank=1・3 seed平均
| 指標 | 結果 |
|---|---:|
| 既知context | 1.0000 |
| 未知context zero-shot | 0.2875 |
| 未知context棄権 | 0.5764 |
| 未観測operation補完 | 1.0000 |
| 操作順序反実仮想 | 0.0000 |
| 主語省略 | 1.0000 |
| 複数段落 | 1.0000 |
| 計画変更 | 1.0000 |
| model bytes | 1,520 |
| factor nodes | 6 |
| train | 0.000216 s |
| inference seen | 0.0194 ms |
| inference multi-paragraph | 0.0477 ms |
| Peak RSS | 295,268 KiB（Python runtime込み） |

rank=6では既知0.8083、補完0.8333へ悪化。異なるsignature factorを混ぜるほど局所投票が曖昧化した。

## 反例と失敗原因
### Counterfactual completionは補間にすぎない
同じ既知contextで欠けたoperation cellを埋めることはできたが、contextそのものが未学習表現になると0.2875。潜在機構を理解したのでなく、6個のsurface context prototypeを読んでいる。

### 順序因果は0
同じ語を含むcontextへ「先に別操作を実行した後」を追加し結果を反転すると0%。prior state、event order、履歴依存機構を表現していない。

### 主語省略・複数段落・計画変更の1.0は無効
予測器はcontextだけを読み、commandの主語、段落構造、訂正を使用しなくても答えられる。日本語談話・計画能力として採用しない。

### factor nodeは機構ではない
発見された6 nodeはcontext表面ごとのprototype。複数contextに共通する原因を合成的に分離していない。

## 系列C固有の進展
- 複数operation outcome vectorは、単一action/no-opラベルより強い監査信号になる。
- signature全体を1 nodeへまとめるだけでは、同一context内補間はできても、機構の合成・順序・prior-state反実仮想は生まれない。
- 次に必要なのはsurface context nodeではなく、operation間で共有される疎なmechanism edgeの分解である。

## 他系列へ返す知見
- A: 証拠channel監査へ複数operation整合性を使えるが、surface prototypeの高確信を因果信頼度と混同しない。
- B: cross-episode program候補は、未知cell補完だけでなく操作順序・prior-state変更を通す必要がある。
- D: condition memory統合時に、同一context signature暗記とmechanism factor再利用を分離評価する。
- E: outcome vectorが同じ候補は商空間化できるが、scope・revision識別には順序介入vectorが必要。

## 次仮説
**Compositional Mechanism Edge Discovery with Order-Sensitive Intervention Completion**

context全文を1 nodeにせず、複数context・operation・identity・prior-state間で再利用される最小edge集合へ分解する。各候補edgeを除去・反転・順序交換して未観測結果を生成し、別identity・未知context paraphrase・二段計画で同じ局所機構が再現するものだけ昇格する。

必須条件:
- 未知context zero-shot 0.2875を改善
- order counterfactual 0を改善
- commandを読まなくても解けるリークgateを導入
- factor node数をsurface context数より少なくする
- 32KB未満、5ms/query未満、複数seed

## 再現
```bash
python research/intelligence_swarm/tracks/C_causal_world/mechanism_factored_intervention_tensor_cycle9.py \
  --output research/intelligence_swarm/tracks/C_causal_world/results_cycle_009.json
```

## 状態
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
