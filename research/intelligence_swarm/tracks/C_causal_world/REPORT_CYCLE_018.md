# 系列C Cycle 018 研究報告

## 仮説

**Executable Operation Fibers with Conditional Commutator Algebra**  
（条件付きcommutator代数を持つ実行可能operation fiber）

Cycle 017ではcross-context commutator signatureをoperation identityとして使ったが、状態更新精度はseen 0.142、未知表現0で、family数だけが17.67から23.33へ増えた。さらに両operationが実行不能でも順序反実仮想が正解扱いになる評価漏れがあった。

本Cycleではcommutatorより先に、raw before→after局所editを複数state representationへtransportし、観測afterを正確に再構成した候補のみを実行可能operationとした。同じ匿名transition shapeとnon-target preservation contextを持つ実行可能候補だけをfiber化し、両operationが双方の順序で実行できるcontextだけでconditional commutatorを測った。実行不能は通常outcomeへ混ぜずnull transportとして分離した。

## 先行研究整理

- Varici et al., JMLR 2025は、一般変換下で潜在因果変数を識別するには介入coverageと複数介入環境が必要であることを示す。
- Ng et al., AISTATS 2025は、一般環境下の因果表現識別条件を扱う。
- Yao et al., ICLR 2025は、多くの因果表現学習法がデータの不変性・対称性と整合する形で表現を形成すると整理する。
- 物体中心表現の転移研究でも、object decompositionだけでは未知domainへのtransportは保証されない。

既存研究は観測表現・介入変数・encoderを既定とすることが多い。本Cycleは生の日本語文字列からoperation transport候補自体を形成する上流問題を対象とした。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との区別 |
|---|---|---|---|---|
| A | 可逆split/mergeによる境界・action共同提案 | delayed creditの適用順序を反証 | 全split candidate recall 0 | 境界共同探索は扱わずworld operation transportを対象 |
| B | 絶対MDL利得付き境界・program共同帰納 | multi-viewでseen 0.6944 | 未知形式0、圧縮利得負 | 圧縮・program商は棄却 |
| D | provenance-gated alias再固定化 | object/relation分離でread限定改善 | write 0.0633、rename過分裂 | 長期memory統合は棄却 |
| E | span・residual共同創発 | raw basisの失敗分類 | unmarked recall 0、junk収束 | energy/cause共同生成は棄却 |
| **C** | **cross-formで実行できる局所transitionのみをoperation fiberへ結ぶ** | 今回検証 | open-form transport・object permanence | 系列固有 |

継承知見:
- A: candidate recall成立前の時間creditはfailureを固定する。
- B: view相互復号だけでは候補外programを生成しない。
- D: cross-form同値性にはprovenanceと誤統合反証が必要。
- E: 実行不能を通常cause/outcomeとして圧縮してはいけない。

## 実験条件

- seed: 1 / 7 / 19
- 学習episode: 48 / 144 / 432
- 保存rule上限: 64
- train mixture: seen + alternate + rename
- test: seen / held paraphrase / alternate / rename / subject omission / multi-paragraph / plan change / free-form state
- 比較: surface rule / transport-audited rule / executable fiber / fiber + conditional commutator
- hidden object / field / valueは評価器専用

## 最大432 episode・3 seed平均

| 条件 | Surface | Transport | Fiber | Conditional |
|---|---:|---:|---:|---:|
| seen | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| held paraphrase | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| alternate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rename | 0.1185 | 0.1185 | 0.0556 | 0.0556 |
| subject omission | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| paragraph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| plan change | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| free-form state | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Conditional counterfactual coverageは全splitで0だった。両operationを双方の順序で実行できるpairが一件も形成されず、Cycle 017の0.63〜0.67という見かけ上の得点は消えた。

## 判定

**中核仮説は強く反証。**

### seenですら実行候補0

seen条件で全方式のaccuracy・commit・平均実行候補が0だった。保存した64 ruleは学習episode内の局所contextには適合するが、新しい同形式command/stateへtransportできない。Cycle 017のseen 0.142より厳しい実行条件にした結果、表面再適用を排除した代わりに全候補がnull transportへ落ちた。

### Fiber形成は能力を増やさない

平均11.67 fiber、50.33 memberを形成したが、主要splitの能力増分は0だった。fiber keyはtransition shapeとpreservation contextであり、object・relation・state variable identityを形成していない。

### Renameの限定信号も悪化

renameではSurface/Transportが0.1185、Fiberが0.0556だった。fiber gateは誤候補だけでなく正しいoperationも捨てた。学習mixtureにrename例を含むため、これは因果転移ではなくsurface overlapである。

### Conditional metric leakageは除去できた

Cycle 017では実行不能pairも反実仮想得点へ入っていた。本Cycleではcoverage 0として除外した。能力向上ではないが、反実仮想評価を正しく無効化したという評価上の進展である。

### Open-form world modelは未成立

object permanence、relation/state-variable binding、goal revision、constraint graph、event segmentation、unknown object transferは形成されていない。

## 相関暗記と因果理解の反証条件

- 学習mixtureに含まれるrenameだけ部分成功 → surface overlap
- unseen state formへtransport 0 → latent operation identityなし
- executable conditional-CF coverage 0 → counterfactual compositionなし
- plan change 0 → goal/revision stateなし
- omission 0 → discourse object permanenceなし
- fiber数増加・accuracy不変 → causal abstractionなし

## 資源量

- model: 13,088 bytes
- rules: 64
- fibers: 11.67
- fiber members: 50.33
- training: 0.00706 sec
- inference: 0.0214 ms/example
- Peak RSS: 159,896 KiB（Python runtime込み）
- complexity: fit `O(PNG)`、inference `O(PG)`、conditional commutator `O(PG)`、`P<=64`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列C固有の進展

因果世界モデル形成を10段階へ更新する。

1. raw object/event proposal
2. local transition executability
3. temporal regime proposal
4. operation candidate proposal
5. cross-context commutator signature
6. null transport separation
7. executable operation fiber
8. **transport-generating latent state anchors**
9. conditional counterfactual composition
10. goal/constraint planning and open-form Japanese

今回、第6段階の評価上の分離は成立したが、第7段階は表面fiberに留まり、第8段階が欠けていた。

> 実行不能を除外するだけではoperation fiberは生まれない。未知表現へ局所transitionを運ぶlatent state anchorを、before/afterの複数viewから生成する必要がある。

## 他系列へ返す知見

- A: boundary-action共同提案は、未知state表現へtransport可能かを独立gateにする。
- B: programのheld-out復号が成功しても、実行可能transport coverage 0ならworld operationではない。
- D: alias linkはsurface read/writeだけでなく、未知state formへの局所transition transportで反証する。
- E: null transportをcause basisへ含めず、candidate absenceとexecution failureを別energy channelにする。

## 次の仮説

**Latent State Anchors from Bidirectional Before/After Transport Residuals**  
（before/after双方向transport残差からの潜在状態anchor）

- before/afterを複数の可逆局所分割へ分解
- 変化区間と保存区間の対応を二部graph化
- 異なるstate表現間で同じ保存区間集合と局所変化を再構成するanchorを生成
- command候補をanchorへ束縛し、未知object/valueへ再実行
- anchor transport成功pairだけでconditional commutatorを測定
- plan changeでは旧goal edgeと新goal edgeを同時保持しrevision edgeを選択

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
