# 系列C Cycle 024 研究報告

## 仮説

**Symmetric-Information Event Direction from Paired Intervention Replays**  
（対称情報付き介入replayからのevent方向創発）

Cycle 023ではreverse側に具体的なold valueが与えられず、正方向event 62.33/64・reverse success 0という偽の方向性が発生した。今回はforward/reverse双方へ同じcontext幅、最大8候補、同じ局所state区間を与え、情報条件を揃えた。

## 先行研究整理

- 2025年のBayesian Active Learning for Bivariate Causal Discoveryは、介入による方向識別をBayes factor仮説検定として扱い、単なる情報利得では方向証拠の強度が不十分になり得ると示す。
- 2025年のCausal Representation Learning from General Environmentsは、複数環境下でも潜在因果変数の識別には環境変化と混合過程への条件が必要と整理する。
- 2026年のCausal-JEPAはobject-level latent interventionによってshortcutを抑え、counterfactual reasoningを改善するが、object表現はencoderで先に形成される。
- 2026年のCounterfactual Planningは状態因果表現とwhat-if-not介入をplanningへ利用するが、状態・行動・報酬の構造を前提とする。

今回の課題は、状態変数もobjectも与えず、生の日本語文字列から方向を創発できるかというさらに上流の問題である。

## 最新PR・他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な失敗 | Cとの分離 |
|---|---|---|---|---|
| A | 観測前commitmentによる前向き談話状態 | 事後逆投影で主語省略pair recall 0→0.2917 | carry独立増分0、計画変更0 | 予測談話stateは扱わない |
| B | 三者導出交差によるbinding seed | 既知局所program | anti-unification grammar 0 | MDL・binding圧縮は扱わない |
| D | write-only classとquery-conditioned read address | endpoint分離で誤読低下 | slow class誤統合 | 長期memoryは扱わない |
| E | 環境分離介入に不変なenergy応答 | value候補の限定信号 | object/pair崩壊 | energy landscapeは扱わない |
| **C** | **同情報条件のforward/reverse replayによるevent方向** | 今回検証 | 因果方向・event identity | 系列固有 |

## 実験条件

- seed: 1 / 7 / 19
- train: 48 / 144 / 288 episode
- test: 既知、言い換え、Rename、別状態表現、主語省略、複数段落、計画変更、反実仮想
- event上限: 64
- graph edge上限: 96
- old/new候補上限: 双方向とも8
- context幅: 双方向とも8文字
- ablation:
  1. Surface
  2. Symmetric replay score
  3. Directed graph

学習器はraw `before / command / after / future`と時間順序だけを使用した。hidden object・field・old/new labelは評価器だけで使用した。

## 最大288例・3 seed平均

| 条件 | Surface | Symmetric replay | Directed graph |
|---|---:|---:|---:|
| 既知 | 0.2500 | 0.2500 | 0.2500 |
| 未学習言い換え | 0.1597 | 0.1597 | 0.1597 |
| Rename | 0.2222 | 0.2222 | 0.2222 |
| 別状態表現 | 0.2083 | 0.2083 | 0.2083 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.1528 | 0.1528 | 0.1528 |
| 計画変更 | 0.1736 | 0.1736 | 0.1736 |
| 反実仮想 | 0.1597 | 0.1597 | 0.1597 |

Direction diagnostics:

- Event: 64.00
- Directed event: 15.33
- Reversible event: 1.33
- Graph edge: 96.00
- Forward success: 161.33
- Forward wrong: 1.67
- Reverse success: 41.00
- Reverse wrong: 262.67
- Mean absolute direction score: 0.0431
- Sequential coverage: 0.1277
- Sequential conditional accuracy: 0.3286

## 判定

**中核仮説は強く反証された。**

### 情報対称化でCycle 023の偽信号は縮小

Cycle 023:
- 正方向event: 62.33/64
- reverse success: 0

Cycle 024:
- directed event: 15.33/64
- reverse success: 41
- mean absolute direction score: 0.0431

reverse側へold-value候補を与えると、正方向判定は約4分の1へ減った。Cycle 023の大半が手続き上の情報非対称性だったことを再現的に確認した。

### しかし能力増分は完全に0

Surface / Symmetric / Directed graphは全splitでaccuracy・wrong commit・null率・候補数が完全同一だった。

情報条件を揃えた方向scoreは評価健全化には寄与したが、event選択、未知表現transport、object permanence、counterfactual rollout、planningを改善しなかった。

### Reverse wrongが262.67

Reverse success 41に対してreverse wrongは262.67だった。old-value候補が複数surface・複数状態へ混ざり、どの過去値が同一eventに属するかを識別できていない。

これは不可逆な世界機構の証拠ではなく、**event identityとstate-variable bindingの欠如**である。

### 96 edgeは依然として文字shape graph

有向edgeは上限96本まで形成されたが能力増分0だった。edgeはold/new shapeと局所prefix/suffix互換性に基づき、object・relation・goal・constraintの因果edgeではない。

### 主語省略は全面0

全方式でaccuracy 0、null率1.0。直前objectを持続状態として保持できず、object permanenceは未成立。

### 計画変更・反実仮想は表面substring再実行

計画変更0.1736、反実仮想0.1597は3方式で同一。旧goal・新goal・revision・未実行worldを保持した能力ではない。

### Sequential counterfactualは未成立

Coverage 0.1277、conditional accuracy 0.3286でCycle 023から変化なし。model自身の方向edgeによる因果合成ではない。

## 相関暗記と因果理解の反証条件

因果方向の支持条件:
1. 双方向で候補数・context・利用情報が同じ
2. surface変更後もdirection signが保存
3. object/value/relation swapでtargetだけが変化
4. non-target文字列を保存
5. directed edge使用によりbaselineよりcounterfactual coverage/accuracyが改善
6. reversible eventは無向として安定分類

今回は1だけを満たし、2〜6は未達。

## 資源量

- Graph model: 15279 bytes
- Training: 0.027143 sec
- Inference: 0.117533 ms/example
- Peak RSS: 159424 KiB（Python runtime込み）
- 推定計算量:
  - event抽出 `O(NL)`
  - paired replay `O(PN)`
  - graph形成 `O(P²)`
  - 推論 `O(PL)`
  - `P≤64`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列C固有の進展

1. Raw event proposal
2. Local transition extraction
3. success / wrong / null transport分離
4. effect hypergraph
5. temporal direction audit
6. **symmetric-information replay――評価健全化、能力仮説は反証**
7. event identity and state-variable binding
8. environment-stable mechanism induction
9. counterfactual composition
10. goal・constraint planning

核心的知見:

> **順逆の情報量を揃えると偽の方向scoreは大幅に減るが、残った非対称性もevent identityが未形成なら因果方向ではない。方向推定より先に、同じ状態変数へ作用するeventをsurface横断で束縛する必要がある。**

## 他系列へ返す知見

- A: 前向きcommitmentと事後観測を比較するとき、利用情報時点を厳密に揃える。
- B: forward/inverse derivationは同じ候補budgetで反証し、それでもbindingが崩れるか測る。
- D: read/write非対称性は候補情報量と探索budgetを揃えてからslow edgeの証拠にする。
- E: 環境間energy response比較は候補数・摂動強度・観測範囲を対称化する。

## 次の仮説

**Environment-Stable Event Identity from Paired Mechanism Residual Signatures**  
（対環境mechanism残差signatureからの安定event identity）

次は方向scoreからgraphを先に作らない。

1. object名、value表現、語順、state表現を独立変更した環境を作る
2. 各局所eventを全環境へpaired replayする
3. forward/reverseのsuccess・wrong・null、non-target damageを残差signature化
4. surfaceが変わっても同じsignatureを示すeventだけidentity classへ統合
5. identity class成立後にのみdirectionを評価
6. unknown object・Rename・別状態表現でclass recallを主指標化
7. classに属するeventだけでcounterfactual rolloutを実行

系列Eのenvironment-invariant energy responseとは異なり、Cは**実行可能state transitionとmechanism residual signature**を中心にする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
