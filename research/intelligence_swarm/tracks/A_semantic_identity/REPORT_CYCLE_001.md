# 系列A Semantic Identity Cycle 001

## 判断

**限定支持だがSemantic Identity Gate G1は未達。**

## 仮説

**Utterance–Witness Synchrony Binding without Span Proposals**  
（文字区間候補を先に作らず、発話全体とtrajectory witnessの時間同期から意味単位を形成する）

生の日本語発話全体を固定次元の疎な文字n-gram featureへ写像し、同時刻に観測されたtrajectory／不可逆痕跡のfeatureとの局所Hebbian外積だけを更新する。対象名、文字区間境界、slot、ontology、正解identityは学習入力へ渡さない。推論時は日本語発話と候補witnessのbilinear整合性を内部状態として計算し、prospective selectionとinverse queryへ同じ結合を利用する。

これは保存済み文章を検索するRAGではなく、発話featureと観測witness間のcross-modal作用素を学習する最小モデルである。

## 凍結族との差

- HF-001のように文字位置・幅・局所差分をsemantic unit候補として先に列挙しない。
- HF-002のように圧縮率やMDLを意味の証拠にしない。
- HF-003のようにidentity未成立のaddressやmemory assemblyを作らない。
- HF-004のようにsurface候補上のgraph／energyで修復しない。
- HF-005のbehavioral equivalenceだけで個体identityを定義せず、AF-003のtrajectory witnessを使用する。

## 先行研究との関係

- spatio-temporal language groundingでは、物体identityを時間方向に維持することが未知文・文法primitiveへの一般化に重要と報告されている。
- object-centric learningでも、時間的一貫性を明示的に学習する損失がobject discoveryとdynamics predictionを改善する。
- ただし既存研究の多くはslot、tracker、Transformer、semantic parserなどの強い表現前提を持つ。本Cycleはそれらを使わず、発話全体とwitnessの同期だけでどこまで進むかを切り分けた。

## 実験

- seed: 1 / 7 / 19
- 192個体／seed
- 学習form 3種、held-out form 3種
- 8候補から対象を選択（chance 0.125）
- Correct synchrony / identity-shuffled synchrony / surface nearest-neighbor
- held paraphrase、rename、未知語順、主語省略、複数段落、自由日本語、語彙を東西南北へ置換した別domain
- prospective selection、inverse query
- trajectory-only / scar-only lesion
- final identityは評価にのみ使用

## 3 seed平均

| 条件 | Correct | Shuffle | Gap |
|---|---:|---:|---:|
| Held paraphrase | 0.2431 | 0.1233 | +0.1198 |
| Rename | 0.2240 | 0.1354 | +0.0885 |
| 未知語順 | 0.2135 | 0.1042 | +0.1094 |
| 主語省略 | 0.2205 | 0.1493 | +0.0712 |
| 複数段落 | 0.1858 | 0.1059 | +0.0799 |
| 自由日本語 | 0.1997 | 0.1354 | +0.0642 |
| 別domain語彙 | 0.1128 | 0.1181 | -0.0052 |

- Surface nearest-neighbor: held 0.0122 / 別domain 0.0087
- Inverse query: held 0.1736 / 別domain 0.1441
- Lesion: trajectory-only 0.2483 / scar-only 0.1389

## 解釈

### 新しい限定的進展

Correct synchronyは、held paraphrase、rename、未知語順、主語省略、複数段落、自由日本語でshuffleを一貫して上回った。文字区間候補やidentity labelを作らず、発話全体とtrajectory witnessの時間同期だけから、8択chanceを上回るprospective selectionが形成された。

これは従来系列Aのexecution 0やCorrect=shuffleとは異なる、**外部能力上の初めての正方向信号**である。

### ただしG1未達

絶対精度は0.18〜0.24程度と低い。別domainでCorrectはchance以下、shuffleとの差も消失した。inverse queryもheld 0.1736に留まり、双方向に再利用できる強いsemantic unitではない。

Selective lesionではtrajectory-onlyがjointを僅かに上回り、scar-onlyはほぼchanceだった。日本語は移動方向を記述しているため、学習された結合はtrajectory語彙と軌跡channelの対応であり、任意の個体identityや不可逆痕跡との結合ではない。

したがって今回の信号を「対象identity創発」とは認定せず、**trajectory predicate groundingの限定支持**と分類する。

## 反証条件

仮説の強い形は次で反証された。

1. 語彙を東西南北へ置換した別domainでCorrect–shuffle gapが消失。
2. scar-only lesionがchance近傍で、発話から任意のsymmetry-breaking witnessを指定できない。
3. inverse queryが弱く、同じunitをforward／inverseへ十分再利用できない。
4. object nameのrenameには耐えるが、これは名前をidentity keyに使っていないためであり、新しい名前自体を接地した証拠ではない。

## 資源

- Cross-modal matrix: 98,304 bytes（float32見積り）
- Python runtime込みpeak RSS: 128,620 KiB
- 3 seed総実行時間: 25.986秒
- 更新: 約24,576 multiply-add／episode
- 候補推論: 約24,576 multiply-add／candidate
- 計算量: update O(TW), selection O(KTW)
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証。行列自体は約96KiBだがPython実装は実機要件を満たす証拠ではない。

## 他系列へ返す知見

- B: whole-utterance synchronyは移動predicateの弱い操作前提を形成するが、別語彙domainへ転移しない。操作創発ではlexical cueを超えるevent relationが必要。
- C: trajectory continuityは日本語と同期するとCorrect–shuffle gapを生むが、語彙置換で消える。因果接地では観測trajectoryだけでなく表現変換を同一視する反例が必要。
- D: trajectory witnessをmemory eligibleとする前に、日本語との結合が別domainとinverse queryを通過する必要がある。今回のunitは保存本線へ昇格不可。
- E: AF-003は「trajectory predicate grounding」に限定支持。G1aを language–trajectory predicate と individual identity に分離すべき。

## 次仮説

**Cross-Episode Relational Witness Binding by Transformation Equivariance**

絶対方向語と軌跡tokenを直接対応させず、複数episode間で同じ変換を受ける発話変化とtrajectory変化の可換関係をunitとする。

次Cycleでは以下を比較する。

1. absolute lexical synchrony（今回）
2. paired transformation equivariance
3. shuffled transformation pairing
4. trajectory-only / scar-only / joint
5. 語彙を完全に置換した別domain
6. forward selection / inverse query / twin discrimination

進歩条件は、別domainとinverse queryの双方でCorrectがshuffleを0.10以上上回ることとする。

- Semantic Identity Gate G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
