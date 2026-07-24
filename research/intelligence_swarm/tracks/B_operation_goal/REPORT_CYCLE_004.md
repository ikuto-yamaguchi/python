# 系列B Operation/Goal Cycle 004

## 仮説

**Cross-Lexicon Selective Consequence Subspace from Counterfactual Response Consensus**  
（反実仮想応答の語彙横断合意からの選択的結果部分空間）

GOV-005でHF-008が凍結され、単一domain・domain平均・一部seedの結果指紋陽性をsemantic operationとみなせなくなった。AF-006の条件に従い、完全語彙非共有の3 domain D/E/Fで、identity・operation・goal・wording介入に対する結果channelの応答順位が一致する部分空間だけを採用した。

モデルは各domainのraw Japanese全文から結果指紋を予測し、介入前world上の32 target×move候補を仮想実行してrankする。domain間辞書、共有token、shared object ID、手書きslot、固定ontology、span proposal、RAG、外部LLMは使っていない。テスト時にafter・完成trajectoryは使っていない。

## 過去知見と重複回避

| 系列 | 最新知見 | Bで重複採用しないもの |
|---|---|---|
| A PR362 | 少数観測によるdomain-local consequence grounding | 単一domainのfew-shot陽性 |
| C PR364 | generic disagreementはRandomを安定して上回らない | 総不一致最大化だけのactive選択 |
| D PR365 | opaque Eのみ陽性、Dへ再現せずeligible 1/3 | best-domain / best-seed採用 |
| E PR366 | HF-008凍結、AF-006昇格 | domain平均によるsemantic認定 |
| **B Cycle 004** | **複数opaque domainで同じ選択的結果channelを匿名選抜** | 今回の固有監査 |

## 設計

1. 完全に異なる3組の日本語語彙で独立domainを生成する。
2. 各domainでselector変更、move変更、goal変更、wording変更のcounterfactual episodeを作る。
3. 結果指紋channelごとに4介入への応答順位を計測する。
4. 3 domainで順位と選択性が一致するchannelだけをconsensus subspaceへ残す。
5. Full fingerprint / Correct consensus / Shuffled-domain consensusを比較する。
6. Prospective joint、inverse、goal判定をheld・未知語順・自由日本語・goal変更・failure repairで測る。

因子名称は評価・反例生成にのみ使用し、モデル内部では4本の匿名介入familyとして扱った。

## 3 seed平均

Joint chanceは0.03125、inverse chanceは0.125、goal chanceは0.5。

| Domain / 条件 | Consensus joint | Outcome shuffle | 差 | Inverse | Goal | Full joint |
|---|---:|---:|---:|---:|---:|---:|
| D / held | 0.0417 | 0.0000 | +0.0417 | 0.2500 | 0.4167 | 0.0417 |
| D / word_order | 0.0833 | 0.0000 | +0.0833 | 0.1250 | 0.8333 | 0.0833 |
| D / free | 0.0833 | 0.1250 | -0.0417 | 0.2917 | 0.3750 | 0.0417 |
| D / goal_change | 0.0000 | 0.0417 | -0.0417 | 0.1667 | 0.6250 | 0.0417 |
| D / repair | 0.0833 | 0.0000 | +0.0833 | 0.0417 | 0.7083 | 0.2083 |
| E / held | 0.0000 | 0.0417 | -0.0417 | 0.2500 | 0.7083 | 0.0000 |
| E / word_order | 0.0833 | 0.0000 | +0.0833 | 0.0417 | 0.7917 | 0.0833 |
| E / free | 0.0000 | 0.1250 | -0.1250 | 0.2083 | 0.6667 | 0.0417 |
| E / goal_change | 0.0833 | 0.0833 | +0.0000 | 0.0833 | 0.5833 | 0.0833 |
| E / repair | 0.0417 | 0.0417 | +0.0000 | 0.1667 | 0.5417 | 0.0417 |
| F / held | 0.1250 | 0.0833 | +0.0417 | 0.2083 | 0.8333 | 0.0833 |
| F / word_order | 0.0417 | 0.0000 | +0.0417 | 0.1250 | 0.4583 | 0.0417 |
| F / free | 0.0000 | 0.0417 | -0.0417 | 0.2083 | 0.6250 | 0.0417 |
| F / goal_change | 0.0417 | 0.1250 | -0.0833 | 0.1667 | 0.5833 | 0.0833 |
| F / repair | 0.0417 | 0.0833 | -0.0417 | 0.1667 | 0.5833 | 0.0417 |

追加診断:

- Consensus channel数: **4.67 / 16**
- 厳格progress gate通過seed: **0 / 3**
- Model: **7026 bytes/domain**
- Peak RSS: **112888 KiB**（Python/NumPy runtime込み）
- Candidate: 32
- 推定更新量: 1536 ops/episode
- 推定推論量: 11264 ops/query

## 判定

**中核仮説は反証。能力上の進歩は認定しない。G1/G2未達。**

### 選択的channel合意は形成できた

3 domainの匿名介入response順位から、平均4.67 channelのconsensus subspaceを形成できた。したがって、完全語彙非共有domainでも結果側の一部成分に共通した選択性を見つける処理自体は成立した。

### しかし外部能力はdomain間で同符号にならない

- D/freeはCorrect 0.0833に対しshuffle 0.1250で悪化。
- E/freeはCorrect 0、shuffle 0.1250。
- F/goal_changeはCorrect 0.0417、shuffle 0.1250。
- strict seed passは0/3。

一部条件ではCorrect>shuffleだが、別条件・別domainでは逆転する。AF-006が要求する2 domain以上・3 seed全て・各能力差+0.10を満たさない。

### Channel consensusはoperation primitiveではない

結果channelの介入応答順位が一致しても、raw Japanese側で同じoperationを安定して再生成できなかった。現在のconsensusは物理結果符号化の共通性であり、言語―操作の双方向bindingではない。

### Goal判定の高値は証拠にならない

Full方式のgoal accuracyは多くの条件で0.9前後だが、goal weightingの生成分布が偏っており、consensus lesionで大きく低下する。prospective jointとinverseを伴わないため、goal semantics成立とは認定しない。

## 反証条件

| 条件 | 結果 |
|---|---|
| 完全語彙非共有3 domainでconsensus channel形成 | 達成 |
| Correct consensusがshuffled consensusより安定 | 未達 |
| 2 domain以上・3/3 seedでfree/goal/repair差+0.10 | 未達 |
| Prospectiveとinverseを同時改善 | 未達 |
| Goal変更でoperation保持とgoal選択を同時達成 | 未達 |
| 1GB未満・小規模CPU計算量 | 達成 |

## 系列B固有の知見

> **結果側の選択的因果channelを語彙非共有domain間で合意させるだけでは、言語側のoperation primitiveは再生成されない。必要なのはchannel一致ではなく、同じ未知発話がどのcounterfactual応答を変え、どれを保存するかという双方向の選択的一貫性である。**

## 他系列へ返す知見

- A: identity proposalは結果channel一致だけでなく、発話介入→結果介入と結果介入→発話選択の双方向signatureを要求する。
- C: factor-selective active interventionはoutput disagreementではなく、language-side interventionの予測的情報利得を含める。
- D: consensus channelが形成されても全seed資格0なので、fast weights・干渉保持を再開しない。
- E: AF-006を継続できるが、output-only consensusという下位仮説は不採用とする。

## 次仮説

**Bidirectional Counterfactual Codebook Birth from Cross-Lexicon Response Conservation**

次はoutput channelだけを揃えない。

1. 各opaque domainで発話counterfactualと結果counterfactualを双方向に生成する。
2. 発話の最小変化がtarget / transition / goalのどのresponseだけを変えるか測る。
3. 結果側lesionから逆に、どの発話候補だけが棄却されるか測る。
4. Forwardとinverseの選択行列が転置近似になるunitだけを採用する。
5. domain間で行列の符号patternが一致するか監査する。
6. Correct / language-shuffle / outcome-shuffle / one-way-onlyを比較する。
7. 自由日本語・goal変更・failure repairで各domain Correct-shuffle +0.10、3/3 seedを必須化する。

- Stage: S1継続
- G1: 未達
- G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
