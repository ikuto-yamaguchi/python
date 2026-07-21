# 系列A Cycle 007 研究報告

## 仮説

**Reliability-Calibrated Active Predictive States with Reversible Evidence Channels**  
（信頼度校正型・可逆証拠channel付き能動予測状態）

Cycle 006では、候補集合をほぼ二分する質問木により、既知yes/no表現なら2〜8候補を理論的な情報量に近い回数で識別できた。一方、未学習返答では内部entropyだけが減少し、8候補精度0.1074・棄権0で誤確信へ収束した。

本サイクルの検証可能な仮説は次である。

> 返答文字列から推定したyes/noを即時の真実として扱わず、表面類似、過去の下流整合率、解釈一致率を独立した証拠channel信頼度として保持し、低信頼なら候補状態を更新しないことで、既知対話の性能を一定範囲で維持しながら未知・非回答・否定トラップの誤確定を選択的棄権へ変換できる。

後続の一般的な失敗信号が到着した場合は、最後の候補集合更新を可逆に取り消す。後続信号には正答値を含めない。

## 先行研究整理

- Park et al., *Calibrated Prediction with Covariate Shift via Unsupervised Domain Adaptation*, AISTATS 2020. 分布変化下では通常の確信度が過大評価され得る。https://proceedings.mlr.press/v108/park20b.html
- Liang et al., *Selective Classification Under Distribution Shifts*, 2024. 分布変化を含む選択的予測ではID前提のconfidence scoreだけでは不十分。https://arxiv.org/abs/2405.05160
- Cattelan & Silva, *How to Fix a Broken Confidence Estimator*, UAI 2024. 棄権性能はconfidence estimatorの品質に強く依存する。https://proceedings.mlr.press/v244/cattelan24a.html
- Testoni & Fernández, *Asking the Right Question at the Right Time*, 2024. モデル不確実性と人間のclarification需要は一致せず、質問policyと観測意味は分離して扱う必要がある。https://arxiv.org/abs/2402.06509
- Yu & Blanchard, *Distribution-Free Sequential Prediction with Abstentions*, COLT 2026. 逐次予測では誤分類と誤った棄権の双方にトレードオフがある。https://proceedings.mlr.press/v336/yu26a.html

今回の差分は、既存分類器の確率校正ではなく、候補世界の再帰更新に用いる自然言語証拠channelを局所的・可逆に校正する最小機構を反証した点にある。

## 過去実験知見の集約

- A006: 質問policyは既知返答で効率的だが、未知返答を誤解釈すると高速に誤確信へ収束する。
- B007: 実行効果は未知predicateのprimitive橋渡し信号になるが、role・scope・状態relationを同時には生成できない。
- C007: 効果付き一回観測は未知contextのsurface alias追加には使えるが、潜在因果条件の発見ではない。
- D007: 正しいepisode候補が集合に入れば仮書込み監査が効くが、代名詞・更新先候補のrecallは崩壊する。
- E007: scope候補数を増やしても異なる実行結果を生まなければenergyは平坦化する。

## 重複表

| 系列 | 最新仮説・中心機構 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B | Joint Role–Effect MDL Lattice | 効果付きprimitive橋渡し | role/scope同時誘導、別状態表現 | primitive候補生成は重複のため棄却 |
| C | Multi-operation intervention signatureからcondition factor発見 | one-shot context bridge、軽量商空間 | branch数固定、zero-shot意味転移 | 因果condition誘導は重複のため棄却 |
| D | Effect-grounded discourse-state memory | 明示区間one-shot binding | 代名詞、談話焦点、更新先 | 長期記憶統合は重複のため棄却 |
| E | Intervention-discriminative scope attractor | 非同型branchがあれば短い緩和が機能 | scope proposal recall、局所学習 | 内部energy緩和は重複のため棄却 |
| A候補 | 証拠channel信頼度を状態更新と分離し可逆化 | 誤確信を選択的棄権へ変える可能性 | coverage崩壊、意味drift、候補生成未解決 | 採用 |

中心機構は外部返答channelの信頼度と候補状態更新の分離であり、B〜Eの構造候補生成・因果・記憶・energy選択とは実質的に異なる。

## 最小実装

学習器は生の日本語返答を文字2/3/4-gramで表現し、最大5個の局所prototypeだけを読む。

各prototypeに保持する状態:

- 返答解釈候補の局所頻度
- 下流interaction success/failureのBeta事後平均
- 近傍prototype間の解釈一致率
- support数

候補集合更新:

1. 候補集合を半分へ分割する。
2. 日本語返答を証拠channelで解釈する。
3. `similarity × reliability × agreement` が閾値未満なら更新しない。
4. 閾値以上なら候補集合を再帰更新する。
5. 後続の一般的失敗信号が来た場合、直前の候補集合へrollbackする。

使用していないもの:

- Transformer / RNN / attention
- 形態素解析
- 固定ontology・意味slot
- 外部LLM・RAG
- 正答値を含む後続観測
- 問題別推論分岐
- 手書き返答辞書。語句集合は評価データ生成専用で、学習器は文字列と下流整合だけを受け取る。

## 実験条件

- 学習量: 64 / 256 / 1024
- seed: 1 / 7 / 19
- 候補数: 2 / 4 / 8
- 比較:
  - `naive`: 近傍返答を必ずyes/noへ解釈
  - `calibrated`: reliability・agreement・supportが不足すれば棄権
- split:
  - 学習済み返答表現
  - 未学習の言い換え
  - 情報を持たない返答
  - 否定を含むadversarial表現
  - 同じ表面の運用意味が反転するchannel drift
  - 後続一般失敗によるrollback
- target valueは遅延証拠へ含めない。

## 1024例・3 seed平均

### 8候補

| 指標 | naive | calibrated |
|---|---:|---:|
| 既知表現 accuracy | 1.0000 | 0.3208 |
| 既知表現 coverage | 1.0000 | 0.3208 |
| 既知表現 selective accuracy | 1.0000 | 1.0000 |
| 未学習表現 wrong commit | 0.7653 | 0.0000 |
| 未学習表現 abstention | 0.0000 | 1.0000 |
| 非回答 wrong commit | 0.2417 | 0.0000 |
| adversarial wrong commit | 0.9958 | 0.0000 |
| drift wrong commit | 1.0000 | 0.3208 |
| rollback success / 全episode | 1.0000 | 0.6917 |
| 平均ターン | 3.0000 | 2.1667 |
| 対話時間 ms | 0.3629 | 0.2669 |

### 候補数別の既知coverage

| 候補数 | naive | calibrated | calibrated selective accuracy |
|---:|---:|---:|---:|
| 2 | 1.0000 | 0.6417 | 1.0000 |
| 4 | 1.0000 | 0.4597 | 1.0000 |
| 8 | 1.0000 | 0.3208 | 1.0000 |

## 資源測定

- 直列化モデル: **1,009 bytes**
- prototype数: **12**
- 1ターン当たり局所読出し: 約 **4.09**
- 8候補対話: 約 **0.2669 ms**
- Peak RSS: **389,892 KiB**。Python runtime込みで方式固有メモリではない。
- 推定計算量:
  - 学習 `O(NG)`
  - 1返答推論 `O(PG)`、ただしtop-5だけを状態更新へ使用
  - 候補分割回数は最大 `O(log K)` を想定
- モデル本体は1GB未満を大幅に満たす。弱いスマートフォン実機検証は未実施。

## 支持された部分

> 観測channelの信頼度を候補状態のentropyとは別に保持すると、未知・非回答・否定トラップを誤った候補へ強制確定する代わりに、選択的棄権へ変換できる。

8候補では、naiveの未学習表現wrong commit 0.7653、adversarial wrong commit 0.9958に対し、calibratedは双方0となった。非回答もwrong commit 0で全件棄権した。

実際に証拠を適用したepisodeでは、一般的な後続失敗信号により直前の候補集合へ戻せた。rollback成功率がcoverage未満なのは、低信頼で最初から更新しなかったepisodeを分母に含むためである。

## 反証

### 1. 既知表現のcoverageが崩壊

8候補では既知表現のselective accuracyは1.0だが、coverageは0.3208に低下した。2候補でも0.6417である。証拠channelの確信度を十分に一般化できず、正しい観測まで拒否している。

### 2. 未学習表現を理解せず全面拒否

未学習表現のwrong commitは0になったが、accuracyも0、abstention 1.0である。意味を獲得したのではなく、open-set入力をすべて拒否しただけである。

### 3. channel driftには高確信で失敗

既知表面の運用意味を反転させるdriftでは、8候補でcoverage 0.3208、wrong commit 0.3208となり、確定したものは全件誤りだった。過去supportと表面類似に基づく信頼度は、意味変化・皮肉・話者差・局所規約変更を検出できない。

### 4. 信頼度は意味変数ではない

保持したのはsurface prototypeの成功率であり、肯定、否定、保留、訂正、皮肉、引用、他者発話といった再利用可能な対話行為を生成していない。

### 5. 候補世界は実験器から供給

生の日本語から対象・変数・関係・操作・目的・制約・因果候補を生成していない。候補集合が正しい前提で証拠channelだけを評価した下流probeである。

### 6. 統合能力は未達

自由対話、指示遂行、読解、計画、因果、反実仮想、自由記述、長期対話、継続学習は成立していない。

## 統合評価

**判定: 限定的な安全部品として部分支持。open-set能動予測状態の中核仮説として反証。**

系列A固有の進展は、予測状態の不確実性を次の二種類へ分解したことである。

1. **World-state uncertainty**: どの候補世界が正しいか。
2. **Evidence-channel uncertainty**: 観測された日本語返答をどの状態更新として信頼できるか。

Cycle 006は第1だけを減らし、誤確信した。Cycle 007は第2を独立化すると誤確定を減らせることを示したが、現在のsurface校正では安全性とcoverageの両立、および意味driftへの適応に失敗した。

## 他系列へ返す知見

- **Bへ:** primitive候補のMDLが短くても、bridgeに使うeffect channelが未校正なら誤primitiveを効率よく固定する。effect evidenceの信頼度を別状態にする必要がある。
- **Cへ:** action/no-op効果をconditionへ橋渡しする際、観測結果channelの信頼度と意味driftを独立に監査する必要がある。
- **Dへ:** 低信頼な照応・更新証拠はfast memoryへ暫定保持し、低速統合しない。後続不整合時にedgeをrollbackする必要がある。
- **Eへ:** energy marginや収束は、入力factor自体が信頼できる証拠であることを保証しない。証拠channel reliabilityを独立factorにする必要がある。

## 次の一点

**Predictive Evidence-Channel Change-Point States**  
（予測的証拠channel変化点状態）

次はsurface prototypeの静的成功率を使わない。同じ返答形式について、直前までの予測整合率、話者・局所会話episode、返答後の部分的行動結果、訂正・撤回の発生、他の証拠channelとの不一致をイベント駆動で追跡し、証拠意味の変化点候補を状態として生成する。変化点候補が高い間は過去の高supportを無効化し、証拠解釈を複数保持する。

反証条件:

- 既知8候補coverageを0.3208から大幅改善できない
- drift wrong commitを0.3208から減らせない
- 未学習表現を全面拒否のままにする
- static prototypeよりモデルサイズ・推論量が線形増加する
- 自由日本語統合ゲートが0のまま

## 再現

```bash
python research/intelligence_swarm/tracks/A_predictive_state/reliability_calibrated_predictive_state_cycle7.py \
  --output research/intelligence_swarm/tracks/A_predictive_state/results_cycle_007.json
```

## 状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
