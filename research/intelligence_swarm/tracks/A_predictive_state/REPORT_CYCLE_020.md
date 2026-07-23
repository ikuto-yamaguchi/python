# 系列A Cycle 020 研究報告

## 仮説

**Cross-Stream Surprise Phase Locking for Minimal Predictive Roles**  
（複数予測系列の驚き位相同期による最小予測role形成）

Cycle 019の次案だった遮蔽・拡張対比は、系列E Cycle 019の次仮説 `Energy-Causal Minimal Factors by Occlusion–Expansion Equilibrium Tests` と中心機構・反証条件が重なるため棄却した。

本Cycleでは、command・before・after・futureを独立した文字予測系列として扱い、character-level surprisal peak間の位相cellを生成した。command cellとstate/future cellの驚き波形が同期し、持続・変化予測を別々に説明する区間をobject/value候補へ昇格できるか検証した。

- character trigram predictorによる局所surprisal
- peak間をevent-driven位相cellとして生成
- command↔before/future同期をpersistence候補へ
- command↔after同期とbefore非出現をchange候補へ
- 学習済み位相prototypeによる再帰ranking
- pair候補外ではnullを保持

## 先行研究との位置づけ

Predictive State Representationは将来観測の予測を状態として保持する。Recurrent Predictive State Policy Networksはfuture observation predictionを再帰filterへ使うが、観測変数と行動空間は既定である。Predictive event segmentation研究はprediction error peakからevent boundaryを形成できることを示す。一方、2026年のtrajectory extrapolation error研究は、単一surprisal値だけでなく状態軌跡の方向変化が独立情報を持つことを示す。

参考:
- Hefny et al., Recurrent Predictive State Policy Networks, arXiv:1803.01489
- Basgol et al., Predictive Event Segmentation and Representation with Neural Networks, arXiv:2210.05710
- Barenholtz, Trajectory Dynamics in Language Model Hidden States Predict Human Processing Costs Beyond Surprisal, arXiv:2606.05346

## 他4系列との重複表

| 系列 | 最新中心 | 限定信号 | 失敗・未解決 | A候補との重複判定 |
|---|---|---|---|---|
| B | failure-success role / anonymous quotient | 既知誤確定を0へ抑制 | candidate生成0、絶対MDL悪化 | swap・商形成は棄却 |
| C | intervention-preserving correspondence cycle | 軽量graph | score平坦、rename悪化 | correspondence/cutは棄却 |
| D | query-object-relation endpoint分離 | rename write限定改善 | read悪化、link過剰 | memory endpointは棄却 |
| E | factor swap / occlusion-expansion | null安全停止 | value recall 0、swap増分0 | 遮蔽・拡張案を棄却 |
| **A** | **複数予測系列のsurprisal位相同期** | 今回検証 | predictive role boundary | 系列固有 |

継承知見:
- B: failureをcauseへ圧縮してもopen-set candidateは増えない。
- C: cycleが閉じても因果roleは保証されない。
- D: write transportとread endpointを同一edgeへ混ぜない。
- E: nullを常時保持し候補外を一意化しない。

## 実験条件

- 学習episode: 24 / 72 / 144
- seed: 1 / 7 / 19
- test: 16例 / split / seed
- split: seen、held paraphrase、rename、alternate state、nested、subject omission、multi-paragraph、plan revision
- ablation: Sync、Sync+Null、Learned phase prototype、Learned+Null
- Learner input: raw `before / command / after / future` only
- Hidden object/value labels: evaluator only

## 最大144 episode・3 seed平均

| 条件 | Object recall | Value recall | Pair recall | Sync精度 | Learned精度 |
|---|---:|---:|---:|---:|---:|
| seen | 0.5833 | 0.2917 | 0.2500 | 0.0625 | 0.0417 |
| held | 0.6458 | 0.5833 | 0.3125 | 0.0833 | 0.1042 |
| rename | 0.5625 | 0.5833 | 0.2917 | 0.0208 | 0.0208 |
| alternate | 0.5833 | 0.2708 | 0.2292 | 0.1042 | 0.0833 |
| nested | 0.0833 | 0.0208 | 0.0000 | 0.0000 | 0.0000 |
| omission | 0.0000 | 0.6458 | 0.0000 | 0.0000 | 0.0000 |
| paragraph | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| plan | 0.0625 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### Null ablation

| 条件 | Sync誤確定 | Sync+Null誤確定 | Null率 |
|---|---:|---:|---:|
| seen | 0.9375 | 0.1875 | 0.7500 |
| held | 0.9167 | 0.2292 | 0.6875 |
| rename | 0.9792 | 0.2708 | 0.7083 |
| alternate | 0.8958 | 0.1250 | 0.7708 |
| nested | 1.0000 | 0.0000 | 1.0000 |
| omission | 1.0000 | 0.0000 | 1.0000 |
| paragraph | 1.0000 | 0.0000 | 1.0000 |
| plan | 0.9167 | 0.0000 | 1.0000 |

## 判定

**中核仮説は強く反証。** ただしCycle 019で全条件0だったcandidate recallを、seen/held/rename/alternateで部分回復させた探索信号は残る。

1. seen object/value/pair recallは0.5833/0.2917/0.2500へ上昇したがaccuracyは0.0625。正答pairが存在してもbindingを選べない。
2. 64個のphase prototypeはseenを0.0625→0.0417へ悪化させ、heldのみ0.0833→0.1042の小改善。surface rhythmの暗記である。
3. 主語省略ではvalue recall 0.6458だがobject recall 0。談話focusからobject persistenceを復元できない。
4. Nested・paragraph・planで崩壊。長距離distractorやrevisionでpeak topologyがずれる。
5. Nullは誤確定を抑えるがaccuracyを増やさない。
6. Learned prototypeはcharacter surprisal profileであり、object・relation・operation・goal・constraint・causal variableではない。

> 予測誤差系列間の位相同期は候補境界の探索信号にはなり得るが、同じリズムを持つ区間の意味roleやbindingを決定しない。

## 資源量

- Sync model: 8,612 bytes
- Learned model: 11,694 bytes
- Learned phase prototype: 64
- Training: 0.0374 sec
- Inference: seen 5.471ms / held 5.359ms / paragraph 1.583ms / plan 7.039ms
- Peak RSS: 111,624 KiB（Python runtime込み）
- Complexity: character prediction `O(NL)`、phase cells `O(L)`、alignment `O(Hc(Hb+Ha+Hf))`、pair `O(KpKc)`

1GB未満は達成。seen/held/rename/planでは5ms前後または超過し、弱いスマートフォンCPU 5ms目標は未達。実機検証も未実施。

## 系列A固有の進展

1. raw prediction-error stream
2. event-driven surprise peak extraction
3. cross-stream phase cell alignment
4. persistence/change候補の独立生成
5. null-preserving sparse binding
6. **query-conditioned active disambiguation of synchronized cells**
7. recursive predictive state update
8. temporal abstraction
9. open-form Japanese integration

第2〜4段階でcandidate recallに限定信号を得たが、第5〜6段階が未成立。

## 他系列へ返す知見

- B: surface rhythmが同じだけの区間を同一roleへ圧縮しない。
- C: correspondence edgeは驚き同期だけでなくoperation consequenceで分割する。
- D: query endpointはsurface phase similarityでなくretrieval consequenceで反証する。
- E: surprisal peakをcandidate birthに使えてもrole bindingは別energy項が必要。

## 次の仮説

**Active Query Disambiguation over Surprise-Synchronized Predictive Cells**  
（驚き同期予測cellに対する能動query識別）

- 同期cellごとに複数future horizonを予測
- future outcomeが同型ならprobeしない
- non-target predictionを保ち候補partitionを増やすqueryだけ実行
- outcomeが候補集合外ならnullを保持
- active query後のrecursive state更新を測定
- object/value/pair recall、選択精度、probe数を分離評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
