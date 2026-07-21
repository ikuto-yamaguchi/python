# 系列A Cycle 006 — Entropy-Matched Multi-Turn Predictive Repair Programs

## 結論

候補未来がすでに存在し、利用者の yes/no 応答を既知表現として正しく解釈できる場合、候補集合をほぼ二分する質問を反復することで、2〜8候補を情報理論的下限に近いターン数で一意化できた。

一方、未学習の肯定・否定表現では候補集合を誤った側へ収束させ、8候補精度は0.1074まで崩壊した。したがって中核の自由日本語能動推論仮説は反証する。成立したのは、候補生成後かつ応答行為が既知である場合の下流query policyに限られる。

高校生級知能、ネイティブ日本語コミュニケーション、弱いスマートフォン実機検証、完成はいずれも未達。

## 統合した他系列の知見

- B Cycle 006: role factoringは既知predicateの語順変化を部分吸収するが、完全未知lexemeはoperationへ写像できない。
- C Cycle 006: action/no-op branchは既知contextで選べるが、未知context表現へ転移しない。
- D Cycle 006: predictive retrieval gainはepisode proposalが弱い場合にcandidate recallを救えない。
- E Cycle 006: 候補数ではなく、異なる実行結果を持つ非同型branchがenergy landscapeを形成する。
- A Cycle 005: 承認・否定1 bitで二候補は修復できるが、多候補には情報量が不足する。

## 重複監査

| 候補仮説 | 他系列との重複 | 判定 |
|---|---|---|
| 未知predicateから候補programを生成 | Bのprimitive inductionと重複 | 棄却 |
| action/no-op因果branchを学ぶ | C/Eの中心課題と重複 | 棄却 |
| episode groupingを対話履歴から学ぶ | Dの中心課題と重複 | 棄却 |
| 既存候補集合に対し取得情報量と質問回数を一致させる | A固有の能動観測選択 | 採用 |

## 仮説

候補状態がK個ある場合、候補表面から生成したyes/no predicateのうち期待エントロピー減少が最大のものを選び、応答後に候補集合を再帰更新すれば、既知応答表現の範囲では概ねlog2(K) bitの取得で状態を一意化できる。

固定された「場所」「色」などの意味因子は与えず、候補文字列間の差から毎ターンpartition predicateを生成する。期待情報利得が対話コスト以下なら停止する。

## 反証条件

- 既知応答でも取得bit数とentropy減少が一致しない。
- K増加に伴い質問数がlog2(K)を大幅に超える。
- 情報を持たない返答で状態を更新する。
- 未学習の肯定・否定表現で安全に一意化できない。
- 候補未来そのものを生の日本語から生成できない。

## 実装と条件

`entropy_matched_repair_cycle6.py`

- 候補数: 2, 3, 4, 5, 6, 8
- 候補表面から文字1/2-gram predicateを生成
- 期待エントロピー減少最大のpartitionを選択
- known / held-out / uninformative / mixed feedback
- one-shot ablation
- cost-aware stopping ablation
- seed: 1 / 7 / 19
- feedback学習量: 32 / 128 / 512

固定ontology、意味slot、形態素解析、Transformer、RNN、RAG、外部LLMは使用していない。

## 512例・3 seed平均

| 候補数 | known精度 | 平均turn | 取得bit | 理想bit | 時間 |
|---:|---:|---:|---:|---:|---:|
| 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.1089 ms |
| 3 | 1.0000 | 1.6722 | 1.5850 | 1.5850 | 0.1816 ms |
| 4 | 1.0000 | 2.0537 | 2.0000 | 2.0000 | 0.2272 ms |
| 5 | 1.0000 | 2.4093 | 2.3219 | 2.3219 | 0.2799 ms |
| 6 | 1.0000 | 2.6222 | 2.5850 | 2.5850 | 0.3186 ms |
| 8 | 1.0000 | 3.1426 | 3.0000 | 3.0000 | 0.4090 ms |

### 8候補の応答条件

| 応答条件 | 精度 | 棄権 | 平均turn | 取得bit |
|---|---:|---:|---:|---:|
| known | 1.0000 | 0.0000 | 3.1426 | 3.0000 |
| held-out | 0.1074 | 0.0000 | 2.6889 | 3.0000 |
| uninformative | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| mixed | 0.2315 | 0.4833 | 2.3222 | 1.8935 |

Ablation:

- one-shot: accuracy 0.2222、abstention 0.7778
- cost-aware: accuracy 1.0000、平均turn 2.1537、取得bit 2.0876
- model bytes: 514
- feedback patterns: 12
- Peak RSS: 305,300 KiB（Python runtime込み）

## 支持された部分

既知のyes/no応答を正しく解析でき、候補未来がすでにある場合には、候補集合を反復的に二分することで2〜8候補を小さな計算量で一意化できた。取得bitは各Kでlog2(K)と一致した。one-shotでは多候補を解消できず、Cycle 005の「候補entropyに見合う情報量が必要」という結論を確認した。

## 決定的な反証

### 未学習応答で誤った確定へ収束

held-out応答では候補を減らし切るため棄権せず、誤った側へ収束した。8候補精度0.1074はランダム水準付近である。取得bitが3.0でも、正しい情報を得たとは限らず、誤分類された応答によって内部entropyが減っただけである。

### 情報利得は意味理解を保証しない

質問policyが効率的でも、回答act parserが誤れば確信を持って間違える。内部uncertainty減少と現実の正しさを分離する必要がある。

### 候補未来は実験器から与えられている

生の自由な日本語から対象・操作・目的・制約・因果候補を生成していない。B/C/Eが扱うcandidate proposal問題を解決した証拠ではない。

### 質問は表面文字predicate

候補に特定文字が含まれるかという質問構造であり、自然な意味的確認意図を形成していない。

### 統合ゲートは0

自由対話、指示遂行、読解、推論、計画、因果、反実仮想、自由記述、長期対話、継続学習は未達。

## 系列A固有の進展

能動推論を二層へ分離できた。

1. Query policy: 候補集合をどの観測で効率的に分けるか。
2. Observation semantics/calibration: 得た返答がどのbranchを支持し、更新してよいか。

今回1は既知応答表現で成立したが、2がopen-setで成立しない限り、entropy reductionは誤った確信を増やし得る。

## 他系列へ返す知見

- B: operation候補のentropyを減らす質問木は作れるが、未知返答を誤解釈すると誤primitiveへ確定する。feedback calibrationが必要。
- C: 複数因果branchを情報利得で分けられるが、観測の意味を誤ると誤branchへ高確信で収束する。
- D: memory graph候補の確認結果は、open-set feedback actが校正されるまで低速記憶へ固定してはいけない。
- E: energy marginやentropy低下は候補正しさの証拠ではない。外部観測channelの信頼度をfactorとして持つ必要がある。

## 次の仮説

**Reliability-Calibrated Active Predictive States with Reversible Evidence Channels**

返答をyes/noへ即時確定せず、観測channelごとにreliability仮説を保持する。

- 未知応答では候補状態と応答act候補を同時保持
- 同じ返答形式が後続整合性をどれだけ改善したかでchannel信頼度を更新
- entropyが減ってもchannel信頼度が低ければ確定しない
- 誤ったfeedback解釈を後続反例で撤回
- known/held/mixedでcalibration error、誤確信率、質問数を測定

必須成功条件は、known精度とlog2(K)効率を維持しつつ、held-out 8候補の誤確定を大幅に減らし、誤答ではなく選択的棄権へ変えること。
