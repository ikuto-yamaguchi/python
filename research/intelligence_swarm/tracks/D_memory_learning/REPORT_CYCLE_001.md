# 系列D Cycle 001 — Structural Rebinding Consolidation

## 仮説

生のエピソードをそのまま検索するのではなく、複数エピソードから反復する文構造だけを低速記憶へ統合し、episode固有の対象・値は高速な可逆束縛へ分離すれば、巨大な固定パラメータへ事実を埋め込まずに、一回提示学習・上書き・干渉回避を実現できる。

今回の最小実装 `Structural Rebinding Memory` は次の二時間尺度を持つ。

1. **低速記憶**: 複数の質問応答エピソードから、statement/question間の最長共通部分と回答位置を使って構造schemaを統合する。
2. **高速記憶**: 新しい未ラベルstatementをschemaへ照合し、episode固有entityとvalueの束縛だけを保存する。
3. **想起**: 質問から同じschemaとentityを同定し、高速束縛を推論状態へ戻す。

これはベクトルDBや類似文検索ではなく、低速schemaと高速identity bindingを分離する機構プローブである。ただし初期schema誘導には質問応答例のanswer spanを使用しており、完全な自己教師あり構造創発ではない。

## 他系列との重複監査

| 系列 | 中心機構 | 今回との重複 | 判定 |
|---|---|---|---|
| A 予測状態 | 予測誤差・再帰状態・能動推論 | 状態保持という一般点のみ | 中心機構は非重複 |
| B 圧縮記号 | MDL残差・記号創発 | 複数例から不変構造を抽出する点 | Bの残差生成を使わず、記憶の二時間尺度と再束縛へ限定 |
| C 因果世界 | 介入安定イベント・因果グラフ | entity/value分離 | 因果・介入を扱わないため非重複 |
| E 制約緩和 | エネルギー・反復収束 | なし | 非重複 |
| 過去D #134–136 | 保存時期・驚き・干渉予算 | 継続学習という目的 | 更新採否ではなく、保存内容をschema/bindingへ分解するため別仮説 |
| PR #138 | 可逆episode binding | 強い近接 | #138は既知schema上の参照だった。今回は複数episodeから低速schemaを統合し、未ラベルstatementを一回で高速記憶へ書く点を検証 |

## 継承した知見

- PR #137/#138: 抽象roleとepisode固有identityを同じ表現へ潰してはいけない。
- 系列B Cycle 001: 未知表面を直接辞書化するより、再利用可能な固定構造と残差を分離する方がよい。
- 系列C Cycle 001: episode identityと抽象操作を別チャネルへ分けないと、介入整合性が過剰拒否する。

## 実験

- seed: 1 / 7 / 19
- 低速schema学習: 120エピソード
- 一回提示評価: 120件
- 言い換え評価: 60件
- 上書き干渉評価: 30件
- 関係系列: 保管場所、担当者、合言葉
- 比較:
  - raw episodic storage
  - structural rebinding consolidation
  - no-consolidation ablation

再現:

```bash
python research/intelligence_swarm/tracks/D_memory_learning/structural_rebinding_experiment.py
```

## 結果

3 seedすべて同一傾向だった。

| 方法 | 一回提示 | 言い換え | 最新上書き | model bytes | query latency |
|---|---:|---:|---:|---:|---:|
| raw episode | 0.000 | 0.000 | 0.000 | 32,120 | 約0.00008 ms |
| no consolidation | 0.000 | 0.000 | 0.000 | 15,276 | 約0.00016 ms |
| structural rebinding | **1.000** | **0.000** | **1.000** | 24,242 | 約0.00498 ms |

追加測定:

- 低速schema数: 3
- 高速binding数: 170
- 全方式を含む学習時間: 約0.00235秒 / seed
- Peak RSS: 277,744 KiB。ただしPython実行環境全体を含み、弱いスマートフォン実測ではない。
- 推定想起計算量: schema数を S、質問長を L として O(SL)。今回は S=3。
- 容量: 低速schema O(S)、高速束縛 O(B)。事実を固定パラメータへ埋め込まない。

## 支持された部分

- 反復構造を低速schema、episode固有値を高速束縛へ分けると、未ラベルstatementの一回提示後に未知entity/valueを想起できた。
- 同じentityへの後続観測は同じbindingを更新するため、最新値への上書きが成立した。
- 生エピソード保存だけ、または統合を止めたablationでは成立しなかった。

## 構造的反証

この仮説は**局所的にのみ支持**され、汎用知能経路としては現段階で棄却する。

1. 言い換え完全転移は全seedで0。schemaが表面patternへ固定されている。
2. 初期schema誘導にanswer spanを使用し、完全な自己教師あり学習ではない。
3. 関係系列は人工的な3構文であり、生の自由日本語の未知区間境界・入れ子・省略・曖昧性を扱わない。
4. 想起値を推論、計画、因果、反実仮想、自由生成へ統合していない。
5. 高速記憶は可逆なkey-value束縛であり、単独では意味記憶ではない。
6. raw episodic baselineは意図的に弱い。次回は表面類似検索、PR #138型可逆束縛、系列B残差schemaを強い比較対象として加える必要がある。

したがって、一回提示100%を日本語理解や一般知能の証拠として扱わない。

## 系列D固有の進展

今回の限定的な新規点は、`抽象schemaを学ぶこと` と `episode identityを記憶すること` を分離するだけでなく、**新しい未ラベル観測を低速schemaによって高速束縛へ変換する書き込み経路**を明示したことである。

## 他系列へ返す知見

- Bへ: 圧縮・MDLで得た構造候補は、知識そのものとして固定せず、未ラベル観測を高速bindingへ変換する書き込み器として評価すべき。
- Cへ: causal graphのnode identityは長期抽象nodeとepisode-local surface bindingを分離し、上書き可能なfast stateとして持つべき。
- Aへ: recurrent predictive stateへ全事実を焼き込まず、必要なbindingだけを想起時に注入する比較が必要。
- Eへ: 複数候補schemaの制約緩和では、surface identityをenergy stateへ潰さず別チャネルで保持する必要がある。

## 次の一点

次は `Answer-Free Predictive Rebinding` を反証する。系列BのMDL残差候補と、後続予測の改善だけを使い、answer spanなしでschemaとentity/value境界を誘導する。強いbaselineとして表面検索、PR #138型可逆束縛、今回方式を比較し、言い換え・主語省略・未知構文・干渉・長期保持を同時評価する。

- highschool_level_passed=false
- native_japanese_communication_passed=false
- weak_smartphone_verified=false
- completion=false
