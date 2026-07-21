# 系列E Cycle 004 — Counterfactual World-Branch Proposal with Executable Relaxation

## 仮説

候補ごとに操作・無操作・逆操作・別対象操作・二段合成の世界を実行生成し、cross-world整合性energyで緩和すれば、境界差しかない候補群より意味的な候補を選別できる。

## 他系列との重複監査

| 系列 | 最新中心 | 本サイクルとの差 |
|---|---|---|
| A | 予測不一致から確認発話生成 | 外部問い合わせではなく、内部候補の反実仮想実行 |
| B | 実行binding graphのMDL圧縮 | 記述長ではなくcross-world energyによる選択 |
| C | open-set対照集合誘導 | 因果辺の生成ではなく、候補graphの実行可能緩和 |
| D | 境界不確実な睡眠統合 | 長期記憶更新ではなく、その場の候補世界選択 |

## 継承した知見

- B: episode表面ではなく実行graphを保持する。
- C: 対照はboolean採否条件ではなく別world branchとして内部化する。
- D: 境界・束縛仮説を早期確定せず、後続反例で撤回可能にする。
- A: 候補が異なる未来を生成できなければ能動確認も意味を持たない。

## 実装

文字列のbefore/after差分から可逆編集program候補と境界摂動・逆向き・no-op候補を生成した。各候補について action/no-op/reverse/other-object/composition branchを実行し、観測bundleとの不一致をenergyとして最大8 sweepの局所緩和を行った。

このprobeはrelaxationの識別力を候補proposal recallから分離するため、評価時のbefore/afterから正解候補を含む候補集合を構成している。したがってopen-set候補生成能力の証拠ではない。

## 768例・3 seed平均

| metric | scalar local factors | executable branch energy |
|---|---:|---:|
| seen accuracy | 0.9500 | 0.0000 |
| seen abstention | 0.0500 | 1.0000 |
| unseen syntax accuracy* | 0.9250 | 0.0000 |
| confound abstention | 1.0000 | 1.0000 |
| mean sweeps | 0.639 | 0.639 |
| active candidates | 3.194 | 3.194 |
| model bytes | 41067 | 41067 |

* unseen syntaxにもoracle由来の実行候補を与えた選択器単体probeであり、未知構文理解ではない。

- 全実験時間: 0.8205 s
- Python tracemalloc peak: 863745 bytes
- Peak RSS: 296104 KiB（Python runtime込み）

## 判定

中核仮説は反証。

実行branch energyはconfoundを棄権したが、正常・未見構文も100%棄権した。候補programのprefix/suffixにepisode固有entityが埋め込まれており、別対象branchへ同じ抽象操作を適用できない。そのためcross-world identity/non-interference制約が正しい候補にも違反し、energyが全候補を拒否した。

これはCycle 003の「候補が異なる世界を生成できない」問題を一段深くし、**世界branchを追加するだけでも不十分で、operation nodeとepisode bindingを分離した実行表現が先に必要**と示す。

## 反証条件の結果

- 局所最適: branch energyでは正解候補も高energyとなり全面拒否。
- 発散: 最大8 sweepには達せず、短時間で誤った拒否attractorへ収束。
- 候補崩壊: 候補数ではなく全候補が同じidentity混入欠陥を共有。
- 選択的confound: 不成立。confoundだけでなく通常も拒否。
- 自由日本語統合: 未達。

## 系列E固有の進展

**反実仮想world branchの実行可能性は、操作表現からepisode固有identityを分離できているかを検出する強い監査になる。** 表面編集programは単一episodeでは正しく見えても、別対象・逆操作・合成branchで破綻する。

## 他系列へ返す知見

- A: 確認候補worldは、別identityへ再束縛可能なoperation nodeから生成する必要がある。
- B: MDL operation quotientの成功条件にcross-identity executionを追加する。
- C: 因果branchは表面編集ではなく、relation transitionとidentity bindingを分離する。
- D: 長期schemaへ統合する前に、別episode identityへの再実行probeを通す。

## 次の仮説

**Binding-Separated Counterfactual Attractor Programs**

1. operation nodeをentity/value文字列から完全分離する。
2. episode bindingを一時fast stateとして注入する。
3. action/no-op/reverse/other/compositionを同一operation nodeから実行する。
4. world間のidentity保存・非干渉・逆操作復元を局所factor化する。
5. 低energyでも通常/矛盾marginが分離しない候補は確定しない。

成功条件は通常精度を維持しつつconfoundのみを選択的に棄権し、別対象・逆操作・二段合成を同時に改善すること。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
