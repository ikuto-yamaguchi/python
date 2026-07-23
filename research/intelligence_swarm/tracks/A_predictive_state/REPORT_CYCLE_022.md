# 系列A Cycle 022 研究報告

## 仮説

**Self-Generated Predictive Tests from Candidate Disagreement Residuals**  
（候補間不一致残差からの予測test自己生成）

Cycle 021では固定された5種類のqueryを用いると、正答pairが候補集合内にある条件では候補をほぼ完全に識別できた。しかしquery familyは実験側が与えており、nested・omitted・paragraph・planのcandidate recallは0だった。

本Cycleでは固定query名を廃止し、候補ごとのafter / future1 / future2 / before予測が最も食い違うraw局所観測窓をtestとして自己生成した。観測後にactive candidate setを再帰更新し、分割不能または候補外の場合は観測窓と同期するcommand区間を追加birthさせた。

## 先行研究整理

- Predictive State Representationは、将来のaction–observation test結果の予測をstateとして扱う。
- 2025年のquery synthesis active learningは、候補poolから選ぶだけでなく連続design空間内で情報利得の高いqueryを生成できることを示す。
- 2025–2026年のactive inference研究では、expected information gainによってworld-model仮説を分割するactionを選ぶ方向が整理されている。
- ただし既存研究は候補状態、観測空間、query design space、generative modelを定義済みとする。本Cycleの課題は、生日本語から不完全に生じた候補と観測testを同時に更新する上流問題である。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との重複判断 |
|---|---|---|---|---|
| B | partial derivation homomorphism | 既知context内のfiller再利用 | context nonterminal 0、未知形式0 | grammar/MDLは棄却 |
| C | edit correspondence program | success/wrong/null分離 | 約99% null transport | world operation mapは棄却 |
| D | value-change equivalence memory | endpoint分離で誤読減少 | slow binding 0 | 長期memory統合は棄却 |
| E | constraint-wise bifurcation | null安全停止 | value birthが消失 | energy bifurcationは棄却 |
| **A** | **候補予測不一致から観測testを自己生成し、予測状態を更新** | 今回検証 | open-set cell birth | 系列固有 |

継承知見:
- B: unknown/noexecを意味差として固定しない。
- C: candidate actionの実行可能性と観測test識別を分離する。
- D: object endpointとvalue endpointを混ぜない。
- E: nullを常時保持し、相対scoreだけで候補外を一意化しない。

## 実験条件

- Seed: 1 / 7 / 19
- 学習episode: 24 / 72
- Test: 8例 / split / seed
- 条件: seen, held, rename, alternate, nested, omitted, paragraph, plan
- Candidate pair: 最大16、feedback後最大24
- 自己生成test: after / future1 / future2 / beforeのsurprisal cellから最大12
- 最大active test: 4
- アブレーション:
  1. Passive
  2. Self-generated test
  3. Self-generated test + open-set feedback birth
  4. Feedback birth + null
- hidden object/valueは評価と環境状態のsimulationだけに使用。test位置・candidate・birth区間の生成には使用しない。

## 最大72 episode・3 seed平均

| 条件 | 初期pair recall | 自己生成test精度 | Feedback後pair recall | 平均birth | Null付き誤確定 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.4167 | 0.4167 | 0.4167 | 0.1667 | 0.0000 |
| 未学習言い換え | 0.2083 | 0.2083 | 0.2083 | 0.0000 | 0.0000 |
| Rename | 0.2083 | 0.2083 | 0.2083 | 0.2500 | 0.0000 |
| 別状態表現 | 0.4167 | 0.4167 | 0.4167 | 0.2500 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 0.1667 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 | 0.1667 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 0.7083 | 0.0000 |

## 判定

**候補集合内の自己生成testには限定支持。Open-set candidate birth仮説は強く反証。**

### 自己生成testは固定queryなしでも候補内正答を選択

- seen: pair recall 0.4167 / accuracy 0.4167
- held: 0.2083 / 0.2083
- alternate: 0.4167 / 0.4167

平均約1回の自己生成testで、正答が候補集合内にあれば選べる限定信号が再現した。

### Feedback birthはcandidate recallを一件も増やさない

全splitで`post_pair_recall == pair_recall`だった。観測窓とsurprisal profileが近いcommand区間を追加しても、正しいobject/value pairは新生しなかった。追加候補はjunkまたは既存候補の包含spanだった。

### Open-set条件は引き続き0

nested、omitted、paragraph、planのpost-pair recallは全て0。主語省略ではvalue recall 0.7500だがobject recall 0であり、観測testは省略された談話objectを候補化できない。

### Nullなしでは候補外を誤確定

Self-generated test方式はheld wrong commit 0.6250、rename 0.5417だった。情報利得の高いtestでも、正答候補が集合外ならjunk集合を精密に一意化する。

Null付き方式は全splitでwrong commit 0だが、候補外条件では全面棄権である。

### 観測oracle依存は残る

Test位置は自己生成したが、outcomeはsimulation environmentのraw local observationから得る。現実のユーザー・実機・外界に対して、どの観測をどう取得するかは未実装。自律言語理解の証拠ではない。

## 反証条件

- 候補内識別成功: post-test accuracyがinitial pair recallへ到達
- open-set birth成功: post_pair_recall > initial pair_recall
- 誤確定: initial pair recall 0でnon-null選択
- surface test崩壊: testが候補数を減らすが正答を新生しない
- oracle依存: outcome取得actionが内部から実行不能
- 再帰状態成立: active setが観測に応じて縮小
- 意味状態成立: nested/omitted/paragraph/planでobject・value・scopeが生成されること

今回は候補内識別とactive-set縮小のみ成立。open-set birth・意味状態・自律観測は不成立。

## 資源量

- モデル: 11,937 bytes
- Predictive prototype: 64
- 学習時間: 0.00527 sec
- 推論時間:
  - seen 15.245 ms/example
  - held 15.421 ms/example
  - nested 8.991 ms/example
  - paragraph 9.355 ms/example
- 平均test: seen 1.000 / plan 1.375
- Peak RSS: 111,636 KiB（Python runtime込み）
- 推定計算量:
  - char prediction `O(NL)`
  - disagreement test生成 `O(WH)`
  - feedback birth `O(LH)`
  - recursive update `O(QH)`
  - `W≤40, H≤24, Q≤4`

1GB未満は達成。主要条件で14–15msとなり5ms目標は未達。弱いスマートフォン実機は未検証。

## 系列A固有の進展

1. Raw prediction-error stream
2. Surprisal event cell
3. Persistence/change candidate
4. Candidate disagreement representation
5. **Self-generated local observation test**
6. Observation-conditioned recursive active-set update
7. Open-set cell birth
8. Discourse/time abstraction
9. 自由日本語world state

今回、第5・6段階には限定信号が出た。第7段階は反証。

> 候補間の予測不一致から観測testを自己生成すれば、固定query ontologyなしでも候補集合内の識別は可能。しかし観測testの結果をsurprisal類似で境界birthへ戻しても、候補集合外の意味roleは生成されない。識別と構造創発は別問題である。

## 他系列へ返す知見

- B: context relation候補には、候補導出間の不一致を最大化するheld-out testを自己生成できる。ただしtestはunknown productionを生成しない。
- C: transport map候補をfuture/non-target observationで能動分割できるが、map自体のbirthは別機構が必要。
- D: endpoint候補をquery consequenceで逐次絞れるが、省略object endpointは観測testだけで新生しない。
- E: information-gain testはbasin rankingより候補内識別に強いが、factor birth方向は与えない。

## 次の仮説

**Predictive Test–Cell Co-Creation by Residual Backprojection with Discourse Carry**  
（談話carry付き残差逆投影による予測test・cell共同創発）

1. Test outcomeが予測と異なった残差をafter/future位置へ保持
2. 残差をbefore・commandへ局所逆投影する複数対応仮説を維持
3. 直前episodeの未解消object cellをdiscourse carryとして保持
4. 各逆投影仮説が次の観測予測を改善するかオンライン反証
5. 複数horizonで同じ対応が再発したcellだけ昇格
6. 主語省略・複数段落・計画変更のpost_pair_recall改善を主評価
7. 観測取得costと計算costを分離
8. Nullとunknown cellを常時保持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
