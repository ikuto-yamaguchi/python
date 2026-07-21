# 系列A Cycle 011 研究報告

## 仮説

**Predictive-Equivalence Scope Classes with Shared Active Probes**  
（予測同値scope classと共有能動probe）

Cycle 010では、正しいscope候補が集合内にある場合、候補を一件ずつ実行してgeneric success/failureを得ると未学習scopeを修復できた。しかし候補数に比例してprobeが増え、括弧を外すとcandidate recallが0だった。

本Cycleでは二つを同時に検証した。

1. raw日本語から低頻度局所区間を候補生成し、括弧なしcandidate recallを0から改善できるか。
2. 候補が生成する複数の未来観測bitを予測vectorとし、同じvectorの候補を同値classへまとめ、classを最大分割する共有probeで候補を絞れるか。

probe応答は選択した一般的な環境結果の0/1だけであり、正答文字列は返さない。

## 先行研究整理

- Active Learning with Simple Questions は、単一候補のlabel queryより広いregion queryにより、query language complexityとの交換で対話回数を削減できることを示す。  
  https://proceedings.mlr.press/v247/vasilis24a.html
- Learning from Equivalence Queries, Revisited は、仮説を配置しcounterexampleで更新する反復学習を再検討する。候補集合とcounterexample生成方式が性能を規定する。  
  https://proceedings.mlr.press/v336/braverman26a.html
- Active automata learningでは、非同値状態を分けるseparating sequence長がquery complexityを左右する。  
  https://proceedings.mlr.press/v217/kruger23a.html
- 2025年のpredictive information研究は、未来予測の複雑さ制約から局所的・体系的な記号構造が生じ得ることを示すが、実世界意味へのgroundingは別問題である。  
  https://www.nature.com/articles/s41562-025-02336-w

## 他4系列との重複表

| 系列 | 最新中心機構 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B Cycle 011 | 反例誘導role境界精密化 | proposal recall 0.9037 | precision 0.26、能力0、推論候補再爆発 | role/program生成は重複のため棄却 |
| C Cycle 011 | context/state probeによるmechanism edge分離 | probe依存性を可視化 | raw fingerprintへ過分裂、既知0.1444 | causal edge形成は重複のため棄却 |
| D Cycle 011 | retrieval-Jacobian境界credit | seen F1と一部retrieval改善 | 大segment誤統合、干渉最新値0 | memory境界は重複のため棄却 |
| E Cycle 011 | 残差classへの適応factor取得 | factor評価数を約47%へ削減 | 正答候補なしでも0.7617誤収束 | 内部factor取得は重複のため棄却 |
| A Cycle 011 | 予測同値classを共有外部probeで分割 | 本Cycleで検証 | open-set candidate proposal | 系列固有 |

継承知見:

- B: 候補数削減と正しいrole生成は別問題。
- C: raw fingerprint差を意味構造と誤認しない。
- D: 単一目的の未来gainは誤統合を生む。
- E: 候補集合外の正解を検出できない一意収束は危険。

## 実装

学習器が利用するもの:

- raw日本語文字列
- corpus内の文字bigram頻度
- 選択したprobeのgeneric binary outcome

利用しないもの:

- entity/value辞書
- 固定ontology・手書きslot
- 形態素解析
- Transformer / RNN
- RAG / 外部LLM
- probe応答への正答値漏洩

### 候補生成

corpus bigram頻度から2〜7文字の局所区間へrarity scoreを付け、助詞・句読点境界、文字多様性を弱い構造priorとして上位24区間を残した。特定の値語彙や意味labelは与えていない。

### 共有probe

各候補は12個の一般的摂動channelに対するbinary予測vectorを持つ。残存候補を最も均等に分割するchannelを選び、観測結果と一致する候補だけを残す。最大8 probe。

比較:

1. immediate ranking
2. 候補を一件ずつ試すsequential probe
3. 最大分割shared probe
4. random viable probe ablation

## 実験条件

- train sizes: 64 / 256 / 512
- seeds: 1 / 7 / 19
- 候補数: 2 / 4 / 8 / 16
- splitあたり60例 / seed
- seen
- 言い換えframe
- 完全未知語
- 入れ子
- 主語省略
- distractor複数文
- 未知語＋言い換え＋distractor

## 最大512例・3 seed平均

| split / hidden candidates | candidate recall | immediate | sequential | shared | sequential probes | shared probes |
|---|---:|---:|---:|---:|---:|---:|
| seen / 4 | 0.9167 | 0.2000 | 0.9167 | 0.9111 | 3.20 | 4.29 |
| seen / 8 | 0.9278 | 0.0778 | 0.9278 | 0.9167 | 5.24 | 4.31 |
| seen / 16 | 0.9778 | 0.0444 | 0.9778 | 0.9778 | 9.31 | 4.57 |
| unknown_words / 4 | 1.0000 | 0.2444 | 1.0000 | 0.9944 | 2.80 | 4.72 |
| unknown_words / 8 | 1.0000 | 0.0944 | 1.0000 | 1.0000 | 4.89 | 4.59 |
| unknown_words / 16 | 1.0000 | 0.0611 | 1.0000 | 1.0000 | 8.38 | 4.64 |
| paraphrase / 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 |
| paraphrase / 8 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 |
| paraphrase / 16 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 |
| nested / 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 |
| nested / 8 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 |
| nested / 16 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 |
| subject_omission / 4 | 0.0667 | 0.0000 | 0.0667 | 0.0611 | 1.54 | 0.31 |
| subject_omission / 8 | 0.0667 | 0.0000 | 0.0667 | 0.0611 | 1.50 | 0.31 |
| subject_omission / 16 | 0.0222 | 0.0000 | 0.0222 | 0.0222 | 0.50 | 0.11 |
| distractor / 4 | 0.4000 | 0.0000 | 0.4000 | 0.3944 | 6.86 | 1.82 |
| distractor / 8 | 0.3722 | 0.0000 | 0.3722 | 0.3722 | 6.92 | 1.75 |
| distractor / 16 | 0.2167 | 0.0000 | 0.2167 | 0.2167 | 3.64 | 0.99 |
| combined / 4 | 1.0000 | 0.2667 | 1.0000 | 0.9889 | 3.21 | 4.72 |
| combined / 8 | 1.0000 | 0.1333 | 1.0000 | 0.9889 | 5.67 | 4.69 |
| combined / 16 | 1.0000 | 0.0611 | 1.0000 | 0.9833 | 8.86 | 4.67 |

### 注目結果

- seen 16候補: recall **0.9778**、shared accuracy **0.9778**
- seen 16候補: sequential **9.31** probe、shared **4.57** probe
- unknown words 16候補: recall **1.0000**、shared **1.0000**
- combined 16候補: sequential **8.86**、shared **4.67**
- paraphraseのみ: candidate recall **0.0000**
- nested 4候補以上: candidate recall **0.0000**
- subject omission: candidate recall **0.02〜0.08**
- false commit: 全条件 **0.0000**。未識別時は棄権した。

## 資源

- model: **4304 bytes**
- bigram types: **411**
- candidate cap: 24
- probe channels: 12
- 最大probe: 8
- 1例全方式: 約1.3〜2.3 ms
- Peak RSS: **303332 KiB**（Python runtime込み）
- 全suite: 約23.9秒
- complexity:
  - proposal `O(L²)`
  - class build `O(HC)`
  - shared active `O(C × H × log H)`、`C=12`, `H<=24`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**共有probeによる候補分割は限定支持。中核の自由日本語構造創発仮説は反証。**

### 支持された部分

正しい候補が集合に含まれる大候補条件では、一件ずつ試す方式より共有probeが少ない観測で候補を識別した。

- seen 16候補: 9.31 → 4.57 probe
- combined 16候補: 8.86 → 4.67 probe
- unknown words 16候補: 8.38 → 4.64 probe

> 候補が異なる未来観測vectorを持つなら、候補を一件ずつ試すより、予測同値classを最大分割する共有観測の方が大規模候補集合で効率的である。

### 反証1: 小候補ではむしろ非効率

2〜4候補では候補外のsurface区間を含む24候補を分割するため、shared probeはsequentialより多かった。候補生成precisionが低い場合、情報利得policyはjunk候補の識別へ観測を浪費する。

### 反証2: predictive equivalence classがほぼ形成されない

平均predictive class数は約24で、候補数とほぼ同じだった。今回のhash由来予測vectorは意味的な同値classではなく、候補を人工的に区別するfingerprintである。

### 反証3: 言い換え・入れ子・省略でcandidate proposal崩壊

- paraphrase recall 0
- nested 4候補以上 recall 0
- subject omission recall最大0.078

局所rarityだけでは対象・変数・relation・operation・goal・constraintを生成できない。

### 反証4: 未知語1.0は意味理解ではない

未知語は珍しい文字列なのでrarity detectorが拾いやすい。意味を理解したのではなく、統計的に目立つ文字区間を候補化した結果である。

### 反証5: probe空間が実験側から供給済み

12摂動channelは実験側が定義している。生の日本語や世界相互作用から、どの観測を問い合わせるべきかを生成したわけではない。

### 反証6: 自由日本語統合ゲートは0

自由対話、指示遂行、読解、推論、計画、因果、反実仮想、自由記述、長期対話、継続学習を同一モデルで通過していない。

## 系列A固有の進展

系列Aの能動推論を次の6段階へ更新した。

1. Raw candidate proposal
2. Candidate precision / null-hypothesis detection
3. Predictive-equivalence class formation
4. Shared active probe generation
5. Reversible recursive update
6. Semantic abstraction / open-set transfer

本Cycleでは、制御された大候補条件で4・5を限定支持した。一方、1はsplit依存、2は未実装、3はfingerprint化、6は未成立。

## 他系列へ返す新知見

- B: candidate precisionが低いままactive observationを行うと、junk programの識別にquery budgetを浪費する。
- C: mechanism候補を分けるprobeはraw fingerprintではなく、複数candidateを共有して分割する再利用可能outcomeである必要がある。
- D: boundary候補へのfuture-retrieval probeは、一件ずつではなく境界classを最大分割する共有質問へまとめられる可能性がある。ただし誤boundary候補が多いと逆効果。
- E: residual class分割と同様、Aでも分割利得0のprobeは取得しない。ただしnull hypothesisがないと候補集合外の正解を検出できない。

## 次の仮説

**Null-Calibrated Predictive Classes with Learned Probe Programs**  
（帰無仮説校正付き予測classと学習probe program）

次は固定12 channelを廃止する。

- raw発話区間を置換・削除・順序交換した局所介入からprobe候補を生成
- 異なる候補classを実際に分割したprobeだけを再利用libraryへ昇格
- どの候補も後続観測を説明できないnull stateを常時保持
- junk候補へのquery浪費を候補precision costとして罰する
- 後続反例でprobe programと候補stateを同時rollback

最低成功条件:

- paraphrase candidate recall 0を改善
- nested 4候補以上 recall 0を改善
- subject omission recall 0.078を改善
- 16候補shared probe 4.57以下を維持
- nullなし誤収束と単なる棄権を分離
- model 32KB未満
- 5ms/example未満
- 複数seed

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
