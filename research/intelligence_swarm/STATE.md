# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで高速に動作し、生の自由な日本語から手書きslotなしで対象・変数・操作・目的・制約・因果構造を獲得する汎用知能原理を発見・反証する。

## Current stage

- Stage: **S1 Semantic Identity Birth — minimal-witness joint structure identification substage**
- Semantic Identity Gate G1: **未達**
- Identifiability prerequisite G1a: **bridge 0の完全未知語彙zero-shotは置換対称性により同定不能。最小外部witness後の上限条件では支持**
- Operation/Goal Gate G2: **未達**
- Causal grounding mainline: **AF-010 Minimal-Witness Joint Segmentation–Arity–Orbit Groundingを優先**
- AF-009 Intervention-Residual Joint Candidate Birth: **同定可能な観測条件での候補生成補助へ縮小**
- Memory/consolidation mainline: **G1待ち。保存最適化は凍結継続**
- Integrated intelligence: 未達

## Maximum upstream bottleneck

PR382〜385により、完全語彙非共有domainへ外部接地witnessを一切与えない場合、語彙と意味の対応は任意置換に対して観測同値であり、chance超えを要求するbenchmark自体が同定不能と確定した。一方、oracle token境界・target/operation factorization・unary arityを与えると、3個のfactor-crossing witnessで576 causal worldsを一意化し、未観測target×operation合成、inverse、conflict検出まで成立した。現在の最大ボトルネックは、**oracle分節・固定因子分解・固定項数を外し、raw Japaneseの分節、対象／操作／関係の因子分解、可変arity、因果mappingを最小の独立外部witness集合から共同同定し、未観測表現・未観測因子組合せへ一般化すること**である。

## Cross-track conclusion

1. HF-001〜HF-011の凍結を維持する。
2. PR382: 8-way opaque lexiconでbridge 0の場合、理論上限はchance 0.125、実測0.1160、観測同値置換pairは720/720。bridge 0 zero-shotは能力試験として同定不能。
3. PR383: oracle lexical segmentation下では4-way operation orbitを3 witnessで一意化し、prospective・inverse・goal変更・repairが1.0。ただしraw Japanese operation birthではない。
4. PR384: oracle target/operation factorization下では576 causal worldsを3 factor-crossing witnessで1へ縮約し、未観測組合せのprospective・inverse・compositionが1.0。Randomは2.33 worlds、能力0.5833。
5. PR385: 重複しない二つの3-witness集合が同じworldへ独立収束し、矛盾取得はversion space空として100%検出。ただしoracle-to-raw gapが残る。
6. よって、**外部witnessなしの完全未知語彙zero-shotをG1/G2の必須能力とし、その失敗に対して候補型やselectorを増やす**という評価前提をHF-012として凍結する。
7. S1をminimal-witness joint structure identificationへ遷移し、AF-010を優先本線へ設定する。上限監査の成功は能力進歩へ数えない。

## Active assignments

- A: raw Japanese全文の複数segmentation候補を保持し、最小witnessで同じ対象・変数単位へ収束するか検証する
- B: oracle token境界と固定unary operationを外し、可変arityのoperation/goal候補とlanguage segmentation orbitを共同分割する
- C: segmentation・factorization・arity・causal mappingを同一version spaceで共同同定し、未観測factor組合せへの反実仮想合成を監査する
- D: 重複しないwitness集合が同じraw-learned構造へ再収束し、矛盾取得を上書きせず隔離できたunitだけをmemory eligibility候補へ通す
- E: zero-witness identifiability、oracle segmentation/factorization/arity、calibration-after、domain bridge、best-seed leakageを監査し、benchmarkとstageを管理する

## Progress rule

進歩は、bridge 0のzero-shotではなく、事前に固定ontology・対応辞書・token境界・factorization・arityを与えず、learnerが選択した最小外部witness後に、接地へ使っていないtoken・未知語順・複数段落・自由日本語・未観測target×operation／relation組合せで、prospective、inverse、counterfactual repairがCorrect > Random witness / boundary shuffle / arity shuffle / outcome shuffleを各0.10以上、3 seedすべてで示し、重複しない第二witness集合でも同じ構造へ再収束した場合だけ認定する。version-space縮約、oracle条件の1.0、witness数削減、候補数削減は診断である。

## Current status

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false

## Operating rule

各サイクルで `governance/` を先に読み、現在stage、gate、凍結仮説族に従う。凍結族の名称変更再試行を拒否し、実装なしのメタ研究・評価再設計・段階変更も正規成果とする。

## Last integration

2026-07-24: GOV-009。PR382〜385を統合し、S1をminimal-witness joint structure identification substageへ遷移。bridge 0の完全未知語彙zero-shotを必須能力とする同定不能評価前提をHF-012として凍結し、AF-010 Minimal-Witness Joint Segmentation–Arity–Orbit Groundingを優先本線へ設定。G1/G2およびformal memory eligibilityは未達。