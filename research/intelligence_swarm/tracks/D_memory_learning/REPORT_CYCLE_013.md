# 系列D Cycle 013 研究報告

## 仮説

**Paraphrase-Invariant Write/Read Programs with Contrastive Eligibility Consolidation**  
（対照eligibility統合を持つ言い換え不変write/read program）

Cycle 012では符号付き想起・干渉creditによりevent F1と50件干渉後latest-valueを改善したが、semantic write/read ruleは形成されなかった。本Cycleでは、before/utterance/afterの生文字列差分から局所write programを作り、異なる表現familyで同じ変換が再現したprogramだけを低速schemaへ統合できるか検証した。

## 先行研究整理

- 2026年ACLのGAMは、event progression graphとtopic associative networkを分離し、encodingとconsolidationを別段階にすることで干渉低減を狙う。ただしLLMによる意味構造抽出を前提とし、本研究の超軽量・固定ontologyなしの構造創発とは別問題である。  
  https://aclanthology.org/2026.acl-long.1600/
- ES-Memは固定粒度memoryとflat retrievalの限界を指摘し、dynamic event segmentationと階層memoryを提案する。  
  https://arxiv.org/abs/2601.07582
- LongMINTは長期・多target干渉下で現行memory systemの平均精度が低く、特に改訂された過去事実と複数証拠集約が弱いことを示す。  
  https://arxiv.org/abs/2605.18565
- adaptive compressionの観点では、episodic memoryは単なる逐語保存ではなく、環境規則を更新しながら意味memoryへ圧縮される必要がある。  
  https://www.nature.com/articles/s44159-025-00458-6

## 他4系列との重複表

| 系列 | 最新仮説・中心機構 | 成功 | 失敗・未解決 | D候補との判定 |
|---|---|---|---|---|
| A | survival-calibrated active probe / coverage constrained null | nullでout-set誤確定を拒否 | 既知も全面拒否、候補生成0 | 外部probe policyのため棄却 |
| B | clause-lattice misapplication / relation quotient | program候補削減の試行 | surface risk proxyの増分能力0 | program inductionそのものは重複のため棄却 |
| C | adversarial relation surgery | changed chunkで全文prototypeより軽量 | preservation増分情報0、relation未形成 | 因果relation形成は重複のため棄却 |
| E | dual-residual null attractor | absolute residualでout-set誤確定を半減 | 依然高誤確定、factor空間供給済み | energy/null校正は重複のため棄却 |
| **D** | **paraphraseを跨ぐwrite/read schemaのfast/slow統合** | 今回検証 | open-set binding・干渉・意味不変性 | 系列固有 |

継承した知見:

- A: 候補削減量と意味的生存率は別であり、coverage lossを監査する。
- B: 観測済み保存の再確認は増分情報にならず、cross-form実行が必要。
- C: raw fingerprintやchanged chunkはrelationそのものではない。
- E: classを分割しないfactor・probeは取得しても計算増にしかならない。

## 実装

学習器へ渡すのはrawのbefore / utterance / after / query文字列のみ。object ID、field ID、value辞書、意味slot、形態素解析、固定ontology、RAG、外部LLMは使用していない。

比較方式:

1. `SurfaceReplay`
   - 過去episode全文を保存し、最も近いutteranceを再生する。
2. `ConsolidatedPrograms`
   - before/afterの局所差分とutterance内のnew span周辺をwrite program化。
   - state側prefix/suffixとcommand側prefix/suffixの局所変換で再適用。
3. `ContrastiveEligibility`
   - 異なるsurface familyで同一変換が再現したprogramだけを優先。

hidden object/field/valueは評価器だけが正誤算出に使用し、learnerのproposal・consolidation・write/readには渡していない。

## 実験条件

- 学習event数: 24 / 72 / 216
- seed: 1 / 7 / 19
- split: 既知表現、未学習言い換え、別状態表現、主語省略、長期対話distractor、言い換え＋質問
- 一回提示
- 50件干渉後の再更新
- object 8種類、field 3種類
- モデル・RSS・学習・推論・program数・readsを計測

## 最大216 event・3 seed平均

### 書込み精度

| 条件 | Surface replay | Program | Contrastive |
|---|---:|---:|---:|
| 既知 | 0.7438 | 0.0633 | 0.0633 |
| 言い換え | 0.5509 | 0.0448 | 0.0448 |
| 別状態表現 | 0.7438 | 0.0664 | 0.0664 |
| 主語省略 | 0.1034 | 0.0463 | 0.0355 |
| 長期対話 | 0.7793 | 0.0478 | 0.0478 |
| combined | 0.5509 | 0.0448 | 0.0448 |

### 読出し精度

| 条件 | Surface replay | Program | Contrastive |
|---|---:|---:|---:|
| 既知 | 0.3333 | 0.0417 | 0.0417 |
| 言い換え | 0.1667 | 0.0417 | 0.0417 |
| 主語省略 | 0.0000 | 0.0417 | 0.0417 |
| 長期対話 | 0.5000 | 0.0417 | 0.0417 |

追加probe:

| 指標 | Surface | Program | Contrastive |
|---|---:|---:|---:|
| 一回提示 | 1.0000 | 1.0000 | 1.0000 |
| 50件干渉後更新 | 0.0000 | 0.0000 | 0.0000 |

## 資源量

- Surface model: 55,180 bytes
- Program model: 4,964 bytes
- Contrastive model: 4,964 bytes
- Surface episodes: 216
- Program schemas: 9
- Contrastive schemas: 9
- Program training: 0.0558 sec
- Program read inference: 0.1354 ms/query
- Program mean local reads: 0.1713
- Peak RSS: 14,584 KiB（Python runtime込み）
- 推定計算量: learn `O(NPG)`、write `O(PG)`、read `O(MG)`

## 判定

**中核仮説は強く反証。**

### 圧縮は成立したが能力を破壊

216 episodeを9 schemaへ縮約し、モデルを約55KBから約5KBへ削減した。しかし既知write accuracyは0.7438から0.0633、read accuracyは0.3333から0.0417へ崩壊した。

これはsemantic consolidationではなく、異なるrelation・object・surface formを過剰統合した結果である。

### Contrastive eligibilityの増分情報が0

通常programとcontrastive programは、既知・言い換え・別状態・長期対話で全accuracy・schema数・モデルサイズが同一だった。異なるsurface family数を重みに使っても、最終候補classを一つも分割していない。

### write programがrelationを保持しない

state prefix/suffixを局所変換として保存したが、同じprefix/suffixが複数field・objectで再利用され、どのfieldを更新すべきか識別できなかった。

### 主語省略・照応は未成立

主語省略writeは0.0355、干渉後更新は0。focus stateは意味的entity bindingではなく最後のsurface stateであり、object permanenceを形成していない。

### 一回提示1.0は弱い

単独episodeをそのまま再実行する条件であり、未知領域転移・干渉回避・概念形成の証拠ではない。

### 表面再生の優位はRAG的暗記

SurfaceReplayはepisode全文を保存して文字類似で近い命令を引くため、既知write 0.7438を得た。しかしモデルはepisode数へ線形増加し、言い換え・読出し・干渉で弱い。汎用memory原理として採用しない。

## RAGとの差

Program方式は過去文を返すだけでなく、候補schemaを現在stateへ適用して内部stateを書き換える。しかし今回のschemaは意味的write/read programではなく、局所文字編集templateだった。

## 破滅的忘却と表面暗記の分離

- 一回提示 1.0
- 既知write 0.0633
- 言い換えwrite 0.0448
- 50件干渉後更新 0
- read 0.0417

形成済みschemaが後から単に消えたのではなく、schema統合時点で異なるrelationを過剰に同一視している。主因は破滅的忘却より**意味的同値類の誤形成**である。

## 系列D固有の進展

write/read memory形成を次の5段階へ分離した。

1. Fast episodic write
2. Cross-form candidate proposal
3. Relation/object-sensitive program equivalence
4. Contrastive eligibility consolidation
5. Sparse semantic recall and reconsolidation

今回、1と2の表面版、4の圧縮版を実装したが、第3段階が未成立のため過剰統合した。

重要な新知見:

> paraphrase support数や圧縮利得だけではsemantic schemaにならない。異なる表現でも同じrelationを更新し、別relation・別objectを壊さない**実行不変性**が必要。

## 他系列へ返す新知見

- A: candidate survivalはsurface family数ではなく、別object・別relationで正しいfuture stateを維持した率で校正する。
- B: relation quotientをmemory schemaへ統合する前に、read側でも別query・別object非干渉を監査する。
- C: changed relation edgeだけでなく、どのmemory addressへwrite/readするかをobject-persistent counterfactualで評価する。
- E: paraphrase-family factorは残差classを分割しなかったため、増分情報0のfactorとして棄却すべき。

## 次の仮説

**Object-Relation Address Discovery by Cross-Query Write/Read Invariance**  
（cross-query write/read不変性によるobject-relation address発見）

次はprefix/suffix schemaを直接統合しない。

各候補write programを、別object、同一objectの別relation、別状態表現、paraphrase、subject omission、unrelated query、delayed correctionへ再適用し、write後の複数query結果vectorを生成する。

同じtarget queryだけを改善し、非対象queryを壊さない候補だけを同一memory addressへ統合する。候補addressは固定field IDではなく、cross-query outcome equivalenceから形成する。

最低成功条件:

- 既知write 0.0633とread 0.0417を同時改善
- held write 0.0448を改善
- interference 0を改善
- contrastive ablationで明確な差
- schema 32以下
- 32KB以下
- 5ms/query以下
- hidden labelsをlearnerへ渡さない

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
