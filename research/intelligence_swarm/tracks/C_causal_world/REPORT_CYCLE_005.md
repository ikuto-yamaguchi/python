# 系列C Cycle 005 — Identity-Factored Executable Event Branches

## 目的

系列C Cycle 004では、操作・無操作・逆操作・別対象操作を追加しても、単一編集規則の採否条件としてしか使われず、内部表現が変化しなかった。系列E Cycle 004では、反実仮想world branchを実行しても、operationへepisode identityが混入していたため正常入力を全面拒否した。

本サイクルは、因果スコアやenergyを改良せず、より上流の表現原理を検証した。

> episode固有identity/valueをfast bindingへ分離し、同一のlatent event programを通常操作・別対象・逆操作・二段合成へ再束縛できるなら、表面編集記憶より軽量かつ転移可能な因果world branch基盤になる。

## 他系列との重複表

| 系列 | 最新中心機構 | 本サイクルとの境界 |
|---|---|---|
| A | 質問・返答・後続観測による予測状態改訂 | 外部確認や返答解釈を行わず、介入前のevent実行表現のみ検証 |
| B | operation node / surface decoder分離をMDLで圧縮 | 圧縮率ではなく、別identity・逆操作・合成への実行可能性を検証 |
| D | 境界仮説の睡眠統合と解除 | 長期記憶更新ではなく、保存前のevent branch表現を検証 |
| E | world-branch energyによる候補緩和 | energy順位付けを使わず、候補program自体の再束縛可能性を検証 |

継承した知見:

- B: operationとsurface decoderを分離すると保存重複は減るが、encoder意味同値は解けない。
- E: world branchはidentity leakageを検出する監査になる。
- D: 初期構造仮説を不可逆確定してはいけない。
- A: 後続観測による改訂と観測前予測を分離評価する。

## 実装

`BindingSeparatedCausalProgram` は学習器へentity/value一覧や意味slotを与えない。介入前・命令・介入後の文字列から以下を誘導する。

1. 三viewに共通するidentity候補
2. before/after差分によるold/new候補
3. command/afterに共通しbeforeにないnew hint
4. identity/valueを匿名化したcommand view
5. identity/valueを匿名化したbefore/after transition program

推論時はcommand viewからepisode-local bindingを抽出し、同一programへ注入する。逆操作、別対象、二段合成は同じprogramを再利用して実行する。

比較対象は、過去episodeのbefore+command文字列に最も近いafterを返すsurface memoryである。

## 実験条件

- 学習量: 32 / 128 / 512 episode
- seed: 1 / 7 / 19
- 学習器へ固定entity/value ontologyなし
- 通常操作
- entity/value全面rename
- 完全未学習命令構文
- 観測前no-op状態
- 逆操作
- 別対象への同一操作
- 二段合成
- model bytes / Peak RSS / 学習時間 / 推論時間 / candidate reads / program数

## 512 episode・3 seed平均

| 指標 | Surface memory | Binding-separated branch |
|---|---:|---:|
| 通常 | 0.1833 | **1.0000** |
| entity/value rename | 0.0000 | **1.0000** |
| 完全未学習命令構文 | 0.3083 | **0.0000** |
| 観測前no-op | 0.0000 | **0.0000** |
| 逆操作 | 0.2167 | **1.0000** |
| 別identity再実行 | 0.1833 | **1.0000** |
| 二段合成 | 0.2417 | **1.0000** |
| model bytes | 17,743.3 | **4,677.7** |
| 推論 ms/query | 6.6144 | **1.0302** |
| candidate reads | 128 | **40.67** |
| latent programs | 0 | **6** |

Peak RSSは308,772 KiB。Pythonランタイム込みであり方式固有値・スマートフォン実測値ではない。

## 限定的に支持された原理

> operation nodeとepisode-local identity/value bindingを分離すると、同じ状態遷移を未知identity、逆操作、別対象、二段合成へ再利用できる。

32 episodeでも通常0.925、rename 0.908、reverse 0.85、別identity 0.95、二段合成0.867を得た。128 episode以降はこれらが1.0となり、表面episode記憶より小さいprogram集合へ圧縮された。

これは系列E Cycle 004で検出されたidentity leakageを構造的に解消する下流部品である。

## 決定的反証

中核の自由日本語因果誘導仮説は棄却する。

### 完全未学習命令構文は0

operation programは既知command skeletonからしか呼び出せない。「移す」と未観測の表現を同じoperationへ結ぶ意味encoderは存在しない。表面検索の0.3083も意味転移ではなく偶然の近傍一致である。

### 観測前no-op予測は0

状態に「固定中」が含まれていても、その制約が操作を無効化することを学習できなかった。no-op例から得られるbefore/command対応を、通常event programと同じ因果状態変数へ統合できていない。

したがって、操作あり・操作なしworld branchを実行生成する基盤はできても、どの条件でbranchが有効になるかという因果制約は未獲得である。

### 生の自由日本語ではない

データ生成側には複数テンプレートがある。学習器へontologyは渡していないが、結果は人工的な一関係・一対象・一値変更世界に限定される。主語省略、複数段落、暗示的照応、目的、計画変更、自然な反実仮想、自由生成・自由対話には接続していない。

### 資源条件は未検証

model bytesは1GB未満だが、Peak RSSはランタイム込みで約301MiB。弱いスマートフォン実機でのCPU/RSS/電力測定はない。

## 系列C固有の新知見

因果world modelには少なくとも二つの独立問題がある。

1. **再束縛可能なevent algebra**: identity/valueとoperationを分離し、別対象・逆操作・合成へ実行できること。
2. **contextual branch gating**: 状態制約からaction/no-op/blocked branchのどれが成立するかをopen-setに予測すること。

本サイクルは1を限定的に支持し、2が完全に未解決であることを示した。world branchを用意するだけでは因果理解にならず、branch選択条件の自律誘導が必要である。

## 他系列へ返す知見

- A: 確認候補の未来は、identity分離済みprogramから生成すれば別対象へ再束縛できる。ただしblocked/no-op条件を識別できない未来候補は不完全。
- B: operation/decoder分離の評価へ、別identity・reverse・composition実行probeを必須追加する。
- D: event schemaを低速統合する前に、別identity・逆操作・二段合成を通し、no-op条件が未解決なら暫定仮説に留める。
- E: binding分離は全面拒否を回避する前提になる。ただしenergyへ投入するbranch gating候補を別構造として生成する必要がある。

## 次の仮説

**Context-Conditioned Counterfactual Event Algebra**

同一operation nodeに対して、入力状態から以下の複数branch条件候補を生成する。

- action適用
- no-op
- blocked action
- inverse action
- non-target preservation
- sequential composition

状態中のどの残差がbranch選択へ必要かを、操作あり／なし、逆操作、別対象、時系列反復の予測差から競合させる。固定の「固定中」語句やmode slotは使用しない。

成功条件:

1. 通常・rename・reverse・other・compositionを維持
2. 完全未学習命令構文を0から改善
3. 観測前no-op予測を0から改善
4. 通常入力を拒否せずconfoundだけを選択
5. branch conditionを別表面表現へ転移
6. 1GB未満、候補読み出しと推論時間の回帰を抑制

## 完成判定

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
