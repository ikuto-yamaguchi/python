# 系列D Cycle 041

## 仮説

**Interference-Graph Memory Assemblies from Non-Additive Bidirectional Replay Closure**  
（非加法的な双方向replay閉包からの干渉グラフmemory assembly）

Cycle 040ではwrite/read共同予測generatorを形成できたが、単体削除必要性は0で、semantic traceとは認められなかった。次案の「最小双方向十分集合」は系列B Cycle 041の削除因果role grammarと中心機構が重なるため棄却した。

今回は系列D固有に、generator間の**干渉と非加法的な共同閉路**を疎graphへ変換し、単体では弱い局所generatorが、互いの誤起動を抑制するassemblyとしてfast/slow memoryへ統合できるか検証した。

- Generator単体のread/write replay応答を測定
- 同じreplayで両者が誤実行するpairをconflict edge化
- Pairのunionが各単体より2件以上多いclosed witnessを持つ場合だけsynergy edge化
- Conflictを含まない最大4 generatorの疎assemblyを形成
- 2 session以上で再現するassemblyだけslow化
- Base / Assembly / Slow / Shuffled assemblyを比較
- Final test outcomeは候補生成・rankingに不使用

## 最新系列との重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A Cycle 041 | Boundary-conditioned state rebirth | 時間event境界・state再起動 |
| B Cycle 041 | Deletion-causal minimal role grammar | 最小十分集合・MDL grammar |
| C Cycle 041 | Leave-one-world-out relation axis completion | 因果world差分・relation axis |
| E Cycle 040 | Residual eigenmode constraint field | Energy固有mode・attractor |
| **D Cycle 041** | **Read/write干渉graph、非加法assembly、fast/slow統合** | 今回の固有対象 |

## 3 seed平均

| 条件 | Base closed / wrong / null | Assembly closed / wrong / null | Slow closed / wrong / null | Shuffle closed / wrong / null |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.1667 / 0.8333 |
| 未知語順 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.2333 / 0.7667 |
| Rename | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0333 / 0.9667 |
| 別状態表現 | 0.4333 / 0.3000 / 0.2667 | 0.2667 / 0.2000 / 0.5333 | 0.1000 / 0.1667 / 0.7333 | 0.2667 / 0.2000 / 0.5333 |
| 入れ子 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0333 / 0.9667 |
| 主語省略 | 0.0000 / 0.6333 / 0.3667 | 0.0000 / 0.1667 / 0.8333 | 0.0000 / 0.1667 / 0.8333 | 0.0000 / 0.1667 / 0.8333 |
| 複数段落 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 |
| 自由日本語 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 | 0.0000 / 0.0000 / 1.0000 |

追加診断：

- Generator: **23.33**
- Conflict edge: **78.67**
- Synergy edge: **40.00**
- Fast assembly: **2.67**
- Slow assembly: **2.33**
- One-shot closed: Base 0.0000 / Assembly 0.0556 / Shuffle 0.0556
- Latest recall: **0.0000**
- Obsolete recall: **0.0000**

## 判定

**中核仮説は強く反証された。**

### 疎assemblyは形成された

Correct replayから平均78.67本のconflict edge、40.00本のsynergy edge、2.67個のfast assemblyが形成された。2 session以上で再現したslow assemblyも2.33個残った。

したがって、局所generator間の干渉構造とunion closureを疎graphへ変換する処理自体は成立した。

### 広域memory能力は改善しない

既知・未知語順・Rename・入れ子・複数段落・自由日本語ではAssembly closed-cycle accuracyは0だった。唯一、別状態表現で0.2667のclosed signalがあったが、shuffled assemblyも同じ0.2667であり、Correct replay固有の能力ではない。

Baseの別状態表現0.4333をAssemblyは0.2667へ低下させており、干渉graphは正しい候補も削除した。

> **Surface-local generatorにもconflict edgeと非加法unionは形成できる。Graph疎性やassembly synergyだけではsemantic memory addressを証明しない。**

### One-shot信号もshuffleと同一

Assemblyのone-shot closedは0.0556だったが、shuffled assemblyも0.0556で完全に同じだった。新episodeをその場でmemoryへ統合した信号ではなく、既存surface assemblyの再適用である。

### 主語省略・長期対話・最新値

主語省略ではclosed 0、wrong 0.1667。複数段落・自由日本語は全面nullだった。Latest recallとobsolete recallはいずれも0であり、最新値選択、選択的忘却、長期対話のfocus保持は成立しない。

### 破滅的忘却ではない

良い記憶が後から壊れたのではない。semantic addressが形成される前に、surface generatorの候補tie・誤起動・全面棄権が支配している。したがって失敗はcatastrophic forgettingではなく**initial memory semantics failure**である。

## 先行研究との位置づけ

近年の継続学習は、短期・長期memoryを分けるdual-memory構造、疎なparameter subspace、semantic sparse coding、予算制約付きreplayを検討している。ただし、それらはmemory unitまたは入力表現がすでに存在する前提である。今回扱ったのは、その上流にある生の自由日本語からread/write共通unitを形成する問題である。

## RAG・単純検索との差

保存文章やnearest-neighbor vectorを返していない。

1. Raw日本語からwrite/read generatorを形成
2. Independent replayで閉路・誤起動を測定
3. Generator間のconflict/synergy graphを形成
4. 疎assemblyをquery時の内部推論状態として起動
5. 複数sessionで再現するassemblyだけslow化

という内部memory機構である。ただしassemblyはsurface位置・文字shapeに依存し、semantic associative memoryには未到達である。

## 資源量

- Model: **2961 bytes**
- Peak RSS: **111380 KiB**（Python runtime込み）
- Training: **0.3085 sec**
- Inference:
  - 既知: **2.068 ms/query**
  - 複数段落: **4.625 ms/query**
  - 自由日本語: **2.979 ms/query**
- 計算量:
  - Induction `O(NL)`
  - Replay response `O(QG)`
  - Conflict graph `O(G²Q)`
  - Greedy sparse assembly `O(G²)`
  - Inference `O(AGL)`
- Generator上限24、Assembly上限24、1 assembly最大4 generator

1GB未満は達成した。短文は5ms未満だが、Python runtime込みRSSは約109MBで、弱いスマートフォンCPU実機は未検証。Base方式の長文は5msを超える。

## 系列D固有の進展

> **単体generatorの削除必要性から、generator間の干渉・非加法closure・session再現性を持つ疎memory assemblyへ進めた。しかしsurface-local候補にも同じgraph構造が形成され、Correctとshuffleのone-shot能力が同一だった。**

## 他系列へ返す知見

- A: Event境界後の候補populationをgraph化しても、node identityがsurface-localならstate semanticsは生まれない。
- B: Role削除profileに加えてpair synergyを導入しても、semantic groundingなしでは短い失敗grammarを作るだけである。
- C: Relation axisの低rank性と同様、generator unionの非加法性もsurface共変で成立するため、因果証拠にはunique intervention witnessが必要。
- E: Conflict/synergy edgeをenergyへ移しても、Correct/shuffle固定点差を必須化しなければsurface basinを強化する。

## 次の仮説

**Cross-Form Interference-Invariant Memory Assemblies from Leave-One-Form-Out Replay**  
（leave-one-form-out replayによる表現横断干渉不変memory assembly）

1. 同じ潜在変更をseen・語順変更・別状態表現・自由文の複数formで生成
2. 一つのformを完全に隠してassemblyのconflict/synergy edgeを予測
3. 具体位置・shapeではなく、form間で保存されるedge sign patternをassembly identity化
4. Correct form alignment／shuffled form／single-form／surface graphを比較
5. 隠したform上でwrite/read closed cycleが増えることを必須化
6. Assembly lesionで対応form群だけが崩れるunique witnessを要求
7. One-shotでは新formのedge residualだけfast update
8. Sleep phaseでは複数session・複数formで再現するassemblyだけslow統合
9. Latest／obsolete assemblyを同じ潜在target上で競合

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
