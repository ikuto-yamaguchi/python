# 系列B Operation / Goal Cycle 008

## 仮説

**Joint Segmentation–Variable-Arity Operation Orbit Birth from Minimal Witnesses**  
（最小witnessによる共同分節・可変arity操作orbit創発）

GOV-009 / AF-010とA PR #387を受け、oracle token境界と固定unary operationを外し、raw concatenated opaque commandから次を同一version spaceで共同同定できるか検証した。

- commandの構造解釈
- opaque object token mapping
- opaque operation token mapping
- operation arity（0 / 1 / 2）
- argument order
- prospective rollout

初期仮説数は27,648、witness budgetは5、seedは1 / 7 / 19。Active / Random / Boundary shuffle / Arity shuffle / Outcome shuffleを比較した。

## 現在段階との整合

- Stage: S1 minimal-witness joint structure identification
- G1: 未達
- G2: 未達
- HF-001〜HF-012の凍結を維持
- bridge 0 zero-shotを能力gateに戻していない
- surface grammar、固定slot、ontology、辞書、RAG、外部LLMは不使用
- final test outcomeはselection/rankingへ不使用

## 3 seed平均

| 方式 | 残存仮説 | Witness | Prospective | Inverse | Failure repair | 自由表現 |
|---|---:|---:|---:|---:|---:|---:|
| Active | 0.33 | 5.00 | 0.2222 | 0.2222 | 0.2222 | 0.2267 |
| Random | 3.33 | 4.33 | 0.3819 | 0.4444 | 0.3889 | 0.3839 |
| Boundary shuffle | 1.67 | 4.00 | 0.3889 | 0.4444 | 0.3819 | 0.3995 |
| Arity shuffle | 1.00 | 4.00 | 0.0347 | 0.0417 | 0.0347 | 0.0575 |
| Outcome shuffle | 0.00 | 1.00 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Strict gate: **0 / 3 seed**

## 判断

**中核仮説は強く反証。能力上の進歩は未認定。G1 / G2とも未達。正式operation proposalは0件。**

Active selectorは平均残存仮説を0.33まで縮約したが、3 seed中2 seedで正しい仮説を含むversion spaceそのものを空にした。外部能力はProspective / Inverse / Repair / 自由表現すべて0.22前後に留まり、RandomとBoundary shuffleを下回った。

Randomは平均3.33仮説を残し、Prospective 0.3819、Inverse 0.4444だった。Boundary shuffleも0.3889 / 0.4444であり、正しい構造解釈を維持したActiveの優位はない。

Arity shuffleで能力が大きく下がったため、項数制約は必要である。しかし、項数制約が必要であることと、raw Japaneseから正しい操作構造が創発したことは別である。

## 新しい切り分け

今回の最大知見は次である。

> **候補結果entropyを最大化するwitnessは、現在のraw segmentation / form仮説がmisspecifiedな場合、誤った仮説同士を最も鋭く分割し、正しい構造を早期消去する。**

つまり、Active orbit splittingはoracle構造下では有効だったが、構造仮説そのものが未完成なraw条件では安全ではない。

現在のselectorは「どの候補を分離するか」は最適化するが、「正しい構造が候補集合に含まれているか」「witnessが未知構造を生成する必要があるか」を扱わない。これはselector failureではなく、**structure-support failure + destructive over-pruning**である。

## 反証条件

仮説支持には以下が必要だった。

1. ActiveがRandom / boundary shuffle / arity shuffle / outcome shuffleを外部能力で各+0.10以上上回る
2. 3 seedすべてでversion space非空
3. Prospective / Inverse / Repair / 自由表現が同時改善
4. 同じsegmentation / arity / mappingが独立witness集合で再収束
5. 追加witnessで正しい仮説を消去しない

今回はすべて未達。

## 資源量

- 初期仮説: 27,648
- Witness budget: 5
- Active model: 平均33 bytes
- Peak RSS: 159,740 KiB（Python runtime込み）
- Active総計算時間: 平均1.3789 sec / seed
- 推定計算量: selector `O(B·H·Q)`、推論 `O(H·Q)`
- 1GB未満: 達成
- 弱いスマートフォンCPU: 状態数27,648の全列挙は小規模なら可能だが、自然文スケールでは探索爆発。実機未検証

## A / C / Dへの返却

### Aへ

境界・語順・余剰語・arityを同時に含む候補空間では、entropy最大化witnessが正しいidentity候補を消す。Aのidentity proposalには、単一witness適合だけでなく、**反例を受けた際に既存候補を消去せず構造分裂できるclosure条件**が必要。

### Cへ

因果監査へ渡せるoperation proposalは0件。介入候補は、既存version space縮約ではなく、観測結果を説明できない際に新しいarity / argument-order / scope構造を生成できる必要がある。

### Dへ

取得時成功が安定せず、3 seed中2 seedでActive version spaceが空。memory eligibilityは0。失敗分類はinitial operation semantics failure / destructive over-pruningであり、保持失敗ではない。

## 次仮説

**Conservative Structure-Birth from Witnesses that Preserve Counterfactual Coverage**  
（反実仮想coverageを保存する保守的witnessによる構造創発）

次はentropy最大化だけで候補を削除しない。

1. witness観測後にversion spaceが空になる場合、候補消去を停止
2. 予測不能残差から新しいboundary / arity / argument-order branchを生成
3. 既存仮説と新生仮説を並存
4. 未観測counterfactualのcoverageを維持するwitnessだけ採用
5. Active entropy / conservative active / random / structure-birthなし / shuffleを比較
6. 重複しない第二witness集合で同じ構造へ再収束するか監査

## 状態

- 能力上の進歩: なし
- G1: 未達
- G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
