# 系列C Cycle 019 研究報告

## 仮説

**Latent State Anchors from Bidirectional Before/After Transport Residuals**  
（before/after双方向transport残差からの潜在状態anchor）

Cycle 018ではcross-formで観測afterを正確に再構成できるoperationだけをfiber化したが、seenを含む主要条件で実行可能候補が0、conditional counterfactual coverageも0だった。今回、rule contextを直接同一視せず、before/afterの**保存区間**と**変化区間**を別viewとして匿名anchorへ束縛し、異なる表現間で局所transitionを往復transportできる場合だけ因果状態anchorへ昇格できるか検証した。

## 先行研究整理

- Causal-JEPAはobject-level maskingを潜在介入として利用し、object間相互作用を推論しないshortcutを抑える。object単位の介入が重要だが、object表現自体は外部encoderから与えられる。
- Event-Conditioned Diagnosticsは、予測精度だけでなくevent-regime、object permanence、field-aligned成分への介入で機能性を診断する。ただし明示的moduleや文脈不変性を保証しない。
- FACTSはgraph-structured recurrent memoryとpermutation-invariant routingでworld modelを構成するが、入力のobject/state factorは既定の表現空間上にある。
- Object-Centric Latent Action Learningはdistractorからagent-object interactionを分離するが、visual object decompositionとproxy actionを前提とする。

これらから、単なるfuture predictionやsurface transportではなく、**保存される対象側**と**変化する状態側**を分離し、双方向介入で機能性を検証する必要があると判断した。

## 他4系列との重複表

| 系列 | 最新中心 | 成功・限定信号 | 失敗・未解決 | C候補との区別 |
|---|---|---|---|---|
| A Cycle 018 | persistence/change境界の次案 | 境界候補を多数生成 | pair recall 0、junk誤確定、30ms超 | 文字境界探索は棄却 |
| B Cycle 018 | 反例符号化program symbol | 既知局所実行0.69 | 未知形式0、MDL 6.66倍悪化 | 圧縮・program商は棄却 |
| D Cycle 017 | provenance alias reconsolidation | rename readに表面信号 | slow link 0、interference recall 0 | 長期memory aliasは棄却 |
| E Cycle 017 | frustration-driven candidate birth | null保持で誤確定抑制 | recall 0、birthはjunk生成 | energy candidate birthは棄却 |
| **C Cycle 019** | **保存区間×変化区間の双方向transport anchor** | 今回検証 | latent state anchor・因果合成 | 系列固有 |

継承知見:
- A: object persistenceとvalue changeを独立viewとして測る。
- B: 実行不能と誤実行を分離し、個別反例記録を意味causeとみなさない。
- D: surface共起ではなく同一trajectoryへの双方向bridgeを要求する。
- E: candidate absenceを相対scoreで無理に一意化せずnullに保つ。

## 実装

学習器へ渡すのはraw `before / command / after / future`文字列とepisode順序のみ。hidden object・field・valueは評価専用。

1. before/afterの最長共通prefix/suffixから変化区間と保存区間を抽出
2. command中のafter側変化区間周辺から局所ruleを生成
3. 保存区間signatureと変化区間signatureを別々に形成
4. ablation:
   - Surface rule
   - Preservation-only anchor
   - Bidirectional preservation+change anchor
5. 異episodeへruleをtransportし、forward exact reconstruction、reverse recovery、non-target preservationを監査
6. 双方向anchorはtransport reliability 0.58以上だけ推論候補へ残す
7. 反実仮想は両operationが双方の順序で実行できるpairだけを母数にする

## 実験条件

- train episode: 48 / 144 / 432
- seed: 1 / 7 / 19
- rule上限: 64
- anchor上限: 32
- test:
  - seen
  - 未学習言い換え
  - 別状態表現
  - rename
  - 主語省略
  - 複数段落
  - 計画変更
  - 自由状態表現

## 最大432 episode・3 seed平均

### 状態更新精度

| 条件 | Surface | 保存区間anchor | 双方向anchor |
|---|---:|---:|---:|
| seen | 0.0910 | **0.2160** | 0.0617 |
| 言い換え | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.1080 | **0.2299** | 0.0741 |
| rename | 0.1157 | **0.1744** | 0.0694 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 |
| 自由状態表現 | 0.0000 | 0.0000 | 0.0000 |

### Conditional counterfactual coverage

| 条件 | Surface | 保存区間anchor | 双方向anchor |
|---|---:|---:|---:|
| seen | 0.0031 | 0.0015 | 0.0015 |
| 別状態表現 | 0.0046 | 0.0077 | 0.0046 |
| rename | 0.0015 | 0.0062 | 0.0015 |
| その他 | 0 | 0 | 0 |

## 判定

**中核仮説は強く反証。保存区間anchorには限定的なsurface実行信号のみ。**

### 1. 保存区間anchorは一時改善するが因果anchorではない

seenは0.0910→0.2160、別状態表現は0.1080→0.2299、renameは0.1157→0.1744へ改善した。しかし未学習言い換え・主語省略・複数段落・計画変更・自由状態表現は全て0である。

改善は同じ局所prefix/suffix形状を共有するrule候補を増やした結果であり、object・relation・state variableの同一性を示さない。

### 2. 双方向transport gateが正しい候補も破棄

双方向anchorはseen 0.0617、別状態表現0.0741、rename 0.0694へ悪化した。forward/reverse exactnessを厳しく要求すると、表面差がある正しい候補までnull transportとして除外される。

- 保存区間anchorのmember: 358.67
- 双方向anchorのmember: 78.33
- 双方向null transport: 20639

双方向性は十分条件ではなく、現在のraw局所ruleではtransport可能性自体を作れない。

### 3. transport successが極端に疎

432 episode条件でも双方向anchorのtransport_okは平均57、null transportは20639。成功した少数pairは同一表現contextの再出現であり、未知表現への因果transportではない。

### 4. Conditional counterfactual coverageは実質0

最大でも別状態表現の保存区間anchorでcoverage 0.0077。反実仮想accuracy値は母数がほぼ無いため能力指標に採用しない。

Cycle 017で実行不能pairを含めて0.63〜0.67と過大評価した問題は解消されたが、実行可能な因果合成能力は依然として無い。

### 5. 目標・制約・計画状態は未形成

計画変更・複数段落・主語省略は全方式0。旧goal、新goal、revision edge、constraint、談話focus、object permanenceをgraphへ保持していない。

## 相関暗記と因果理解の分離

- seen/rename/alternate限定改善: surface context reuse
- held/free-form 0: relation/state表現の不変性なし
- conditional coverageほぼ0: intervention compositionなし
- plan 0: goal/revision modelなし
- bidirectional gateで悪化: reversible string edit ≠ reversible causal mechanism

## 資源量

- Surface model: 8466 bytes
- Preservation anchor model: 52394 bytes
- Bidirectional anchor model: 23935 bytes
- rules: 64
- anchors: 32
- training: 0.0281 sec
- inference: 0.0259 ms/example
- Peak RSS: 112644 KiB（Python runtime込み）
- complexity:
  - rule生成 `O(PN G)`
  - transport監査 `O(APN G)`
  - inference `O(APG)`
  - `P≤64, A≤32`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列C固有の進展

必要段階を更新する。

1. Raw object/event proposal
2. Local transition executability
3. Null transport separation
4. Preservation/change view separation
5. Bidirectional transport audit
6. **Transport correspondence discovery across representation changes**
7. Latent state anchor
8. Conditional counterfactual composition
9. Goal/constraint planning
10. 自由日本語統合

今回は第4・5段階を実装した。最大の新知見:

> 保存区間と変化区間を分離しても、文字位置対応を自動発見できなければ双方向transportは正しいruleを捨てるだけになる。必要なのは厳しいgateではなく、異表現間の対応写像そのものの創発である。

## 他系列へ返す知見

- A: persistence/change viewを分けるだけでは不十分。異表現間で対応位置を生成するtransport mapが必要。
- B: failure cause quotientは「実行不能」を圧縮せず、対応写像未発見とwrong executionを別featureにする。
- D: bridge episodeは同じtrajectory文字列ではなく、異表現間の局所対応写像を含む必要がある。
- E: null transportを高energy causeへ直接昇格せず、correspondence absenceとして別状態に保持する。

## 次の仮説

**Sparse Transport Correspondence Maps from Cycle-Consistent Local Alignments**  
（cycle-consistent局所alignmentからの疎transport対応写像）

次はanchor gateを先に固定しない。

1. before/after保存区間を複数の局所segmentへ分解
2. 異なるstate表現間でsegmentの対応候補を疎な二部graphとして生成
3. A→B→Aのcycle consistencyと局所transition再構成を同時評価
4. object名・value・relation表現を変えても残る対応edgeだけをtransport mapへ昇格
5. mapを通して未知表現へoperationを移送
6. transport可能pairだけでconditional counterfactualを測定
7. correspondence不明はnullのまま保持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
