# 系列A Cycle 012 研究報告

## 仮説

**Null-Calibrated Predictive Classes with Learned Probe Programs**  
（帰無仮説校正付き予測classと学習probe program）

Cycle 011では、正しい候補が候補集合内に存在する大候補条件で、固定12 channelの共有probeが逐次probe数を約半減した。一方、predictive classは意味同値ではなくhash fingerprintで、paraphrase・nested candidate recallは0、候補集合外検知もなかった。

本Cycleでは固定probe channelを廃止し、生の文字列候補に対する削除・置換・順序交換からprobe programを生成し、過去episodeで候補classを分割した実績からprobe順序を局所更新する。また「既存候補のどれでもない」null predictive stateを常時保持し、絶対的なprobe不整合から候補集合外を拒否できるか検証した。

## 先行研究整理

- Futrell & Hahn (2025/2026) は、predictive information制約から局所的・体系的な記号構造が生じ得ることを示す。ただし意味groundingやopen-set候補生成を保証しない。https://www.nature.com/articles/s41562-025-02336-w
- Active Automata Learningではadaptive distinguishing sequenceやsmall test suiteにより、仮説を分ける観測列を削減できる。ただし候補状態・入力alphabet・観測意味が与えられる。https://arxiv.org/abs/1902.01139 https://arxiv.org/abs/2401.12703
- Selective classification/OOD研究は、相対confidenceと候補集合外検出が別問題で、分類器内部の不確実性だけではOODを識別できない場合があることを強調する。https://proceedings.mlr.press/v286/dadalto-camara-gomes25a.html https://proceedings.mlr.press/v267/li25ec.html

## 他4系列との重複表

| 系列 | 最新中心機構 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B Cycle 012 | multi-field relation-preservation anti-unification | 既知0.375 | preservation増分0、未知表現0 | relation/program生成は重複のため棄却 |
| C Cycle 012 | changed/preserved contrastから状態変数候補 | whole prototypeより軽量 | relationは表面chunk、preservation差0 | causal variable形成は重複のため棄却 |
| D Cycle 012 | signed retrieval-interference boundary credit | event F1・干渉後latest改善 | retrieval不安定、長gap過分割 | 長期memory境界は重複のため棄却 |
| E Cycle 012 | null attractorによる絶対残差 | out-set誤確定を約半減 | 50.6%誤確定、adaptive分割で再悪化 | 内部energy nullは重複のため棄却 |
| A Cycle 012 | 外部観測を行うprobe programの学習とnull predictive state | 本Cycleで検証 | raw candidate/probe意味 | 系列固有 |

継承知見:
- B/C: 観測済み整合を言い換えたprobeは増分情報を持たない。
- D: target gainだけの最適化は非対象への干渉を生む。
- E: 候補内分割が進んでも現実適合性は改善しない場合がある。

## 実装

学習器が利用するもの:
- raw日本語文字列
- corpus内の文字2/3-gram頻度
- 削除・置換・順序交換probe後のgeneric binary outcome
- probe kindごとの過去の候補削減量

利用しないもの:
- entity/value/relation辞書
- 固定ontology・手書きslot・形態素解析
- Transformer/RNN
- RAG・外部LLM
- probe応答への正答文字列漏洩

### Candidate proposal

2〜20文字の全局所区間へrarity・文字多様性・句読点境界priorを付け、上位32候補を保持した。評価ではhidden target spanとの文字区間IoU 0.60以上をcandidate recallとした。

### Learned probe programs

候補区間に対して以下を生成した。
1. candidate deletion
2. candidate replacement
3. two-span order swap

probeのgeneric outcomeと候補の予測を比較し、候補集合を再帰更新する。probe kindは過去episodeの平均候補削減量で優先順位を更新する。最大8 probe。

### Null predictive state

残存候補のprobe不整合率またはraw proposal supportが閾値を超えた場合、既存候補へ確定せずnullへ遷移する。

## 実験条件

- train sizes: 32 / 96 / 192
- seeds: 1 / 7 / 19
- 各split: 60例 / seed
- fixed surface probe order
- learned probe order
- learned probe + null
- split: seen、paraphrase、nested、subject omission、multi-sentence distractor、out-set implicit target

## 最大192例・3 seed平均

| 条件 | candidate recall | Fixed accuracy / wrong | Learned accuracy / wrong | Learned+Null accuracy / wrong / null |
|---|---:|---:|---:|---:|
| seen | 0.6389 | 0.3167 / 0.6833 | 0.0278 / 0.9722 | 0.0167 / 0.0000 / 0.9833 |
| paraphrase | 0.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 |
| nested | 0.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 |
| subject omission | 0.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 |
| distractor | 0.0056 | 0.0056 / 0.9944 | 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 |
| out-set | 0.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / **0.0000** / **1.0000** |

Probe数:
- seen fixed: 5.506
- seen learned: 5.833
- out-set fixed: 4.000
- out-set learned+null: 3.000

## 資源

- learned+null model: 11,656 bytes
- candidate cap: 32
- probe cap: 8
- seen inference: 2.2247 ms/example
- out-set inference: 1.2445 ms/example
- Peak RSS: 301,264 KiB（Python runtime込み）
- 推定計算量: proposal `O(L²)`、probe generation `O(H²)`、active update `O(PH)`、`H<=32`, `P<=8`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**Null stateには候補外誤確定を拒否する信号があったが、中核仮説は強く反証。**

### 限定的な結果

候補集合外条件では、fixed/learned方式が100%誤確定した一方、learned+nullはwrong commit 0、null 1.0だった。paraphrase・nested・subject omissionでも誤確定を全面棄権へ変えた。

この制御条件では、相対的な候補分割だけでなく、絶対的なprobe不整合を保持する必要性が再確認された。

### 決定的反証1: Nullは安全な理解ではなく全面拒否

seen条件でもlearned+nullはnull rate 0.9833、accuracy 0.0167だった。候補外検知ではなく、ほぼすべてを拒否する過剰棄権である。

### 決定的反証2: Learned probeがfixedより悪化

seenでfixed accuracy 0.3167に対しlearnedは0.0278。候補削減量をprobe utilityとして学んでも、正しい候補を保持する情報価値とは一致しなかった。

候補数を速く減らすprobeが、誤候補へ高速収束する場合がある。

### 決定的反証3: Candidate proposalが上流で崩壊

- seen recall: 0.6389
- paraphrase: 0
- nested: 0
- subject omission: 0
- distractor: 0.0056

局所rarity区間は未知文字列を拾えても、意味的な対象・操作・目的・scope境界を生成しない。

### 決定的反証4: Probe programは意味的操作でない

削除・置換・順序交換は文字区間操作であり、world action、質問意図、speaker transfer、future recallを自律生成していない。学習されたのはprobe kindの表面上の候補削減量だけである。

### 決定的反証5: 自由日本語統合未成立

paraphrase、nested、subject omission、multi-sentence distractorで能力0。自由対話、読解、推論、計画、因果、反実仮想、自由記述、継続学習を同じ状態で解けていない。

## 系列A固有の進展

必要条件を7段階へ更新する。

1. raw candidate proposal
2. candidate precision / null detection
3. predictive-equivalence class
4. probe program proposal
5. **probe utility = entropy reduction と semantic survival の分離**
6. recursive reversible update
7. open-set semantic abstraction

本Cycleでは2の安全側信号を制御条件で確認した。一方、4は文字摂動、5は候補削減量だけで、正しい意味候補の生存率を評価できなかった。

> 情報利得が大きいprobeは、正答保持の保証がなければ誤った仮説空間を効率よく破壊するだけである。

## 他系列へ返す新知見

- B: 敵対的誤適用probeは候補数を減らすだけでなく、正しいprogramのcross-episode survivalを明示測定する。
- C: relation surgery probeはentropy reductionとobject/relation preservationを別指標にする。
- D: boundary probeは候補segment削減量ではなく、target retrievalとunrelated retrievalの両方を保持するか測る。
- E: null residualを強くすると全面拒否になり得る。in-set coverageとout-set wrong commitを同時制約する必要がある。

## 次の仮説

**Survival-Calibrated Active Probe Programs with Coverage-Constrained Null States**  
（生存率校正型active probe programとcoverage制約付きnull state）

次はprobe utilityを候補削減量だけで更新しない。

- cross-episodeで正しい候補が生き残った率
- unrelated stateを壊さなかった率
- 言い換え後も同じ候補classを分割した率
- probe後のfuture retrieval整合
- null選択によるcoverage loss

を共同目的にする。

最低成功条件:
- seen accuracy 0.3167を上回る
- seen coverageを0.50以上へ回復
- out-set wrong commitを0.20未満
- paraphraseまたはnested candidate recallを0から改善
- candidate 24以下、probe 6以下
- 32KB以下、5ms/example以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
