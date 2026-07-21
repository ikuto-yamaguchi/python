# 系列E Cycle 005: Binding-Separated Counterfactual Attractor Programs

## 仮説

系列E Cycle 004では、反実仮想world branchを実行して候補を選別しようとしたものの、表面編集programへepisode固有identityが混入し、正常入力まで全面拒否した。

本サイクルでは、系列C Cycle 005の知見を取り込み、長期側のoperation nodeとepisode-localなentity/old/new bindingを分離した。そのうえで同一operationから action / no-op / reverse / other-identity / composition のbranchを生成し、局所energyまたはcross-world branch energyで候補を反復緩和する。

検証仮説は次である。

> operationとepisode bindingを分離すれば、Cycle 004のidentity leakageによる全面拒否を解消し、正常入力を維持しながらblocked入力だけを選択的に棄権できる。

## 他4系列との重複表

| 系列 | 最新の中心機構 | 今回の非重複点 |
|---|---|---|
| A | 質問・返答による予測状態の可逆改訂 | 外部対話ではなく、内部候補programのattractor選別 |
| B | operation node / surface decoder / episode bindingのMDL分離 | 圧縮率ではなく、cross-world実行整合性による候補選択 |
| C | identity-factored executable event branches | event algebra自体ではなく、複数候補間の緩和・棄権原理 |
| D | episode groupingと記憶統合 | 長期記憶ではなく、その場の構造候補の収束 |

系列Cから「operationとepisode identity/valueは別チャネルに置く」知見を継承した。系列Bからは表面literalをoperationと同一視しないこと、系列Dからは低margin候補を不可逆確定しないこと、系列Aからは候補世界が異なる予測を生成できなければ識別不能という知見を継承した。

## 実装

学習時には介入前後の文字差分と命令文からoperation nodeを誘導する。operation nodeには command skeleton と状態prefix/suffixのみを保存し、entity・old value・new valueは推論時に入力から複数binding候補として生成する。

各候補から次を実行する。

1. action world
2. inverse world
3. other-identity world
4. two-step composition
5. blocked-markerを含むcontext gate

比較方式:

- `local`: command skeleton類似度と適用可能性だけの局所energy
- `branch`: local energyにreverse復元、別identity再束縛、composition、blocked contextを追加

停止条件:

- 最良候補indexが前sweepと同じ
- 最大8 sweep

棄権条件:

- 最良・次点energy marginが0以下
- branch方式では最良energyが3.5超

## 実験条件

- training sizes: 48 / 192 / 384
- seeds: 1 / 7 / 19
- splitごとに20件/seed
- seen syntax
- entity rename
- completely unseen command syntax
- blocked/no-op context
- 最大64候補
- model bytes, Peak RSS, Python allocation peak, sweep数, active candidate数, marginを測定

再現:

```bash
python research/intelligence_swarm/tracks/E_constraint_relaxation/binding_separated_attractor_experiment.py \
  > research/intelligence_swarm/tracks/E_constraint_relaxation/results_cycle_005.json
```

## 384例・3 seed平均

| 指標 | local | branch |
|---|---:|---:|
| seen accuracy | 0.0000 | 0.0000 |
| seen abstention | 1.0000 | 1.0000 |
| rename accuracy | 0.0000 | 0.0000 |
| rename abstention | 1.0000 | 1.0000 |
| unseen syntax accuracy | 0.0000 | 0.0000 |
| unseen syntax abstention | 1.0000 | 1.0000 |
| blocked accuracy | 0.0000 | 0.0000 |
| blocked abstention | 1.0000 | 1.0000 |
| mean sweeps | 1.6125 | 1.6125 |
| active candidates | 64 | 64 |
| mean margin | 0.0000 | 0.0000 |

資源:

- model bytes: 4,923
- induced operation nodes: 30.33
- full experiment: 11.6767秒
- Python allocation peak: 393,507 bytes
- Peak RSS: 295,416 KiB（Python runtime込み）
- largest-run estimated score evaluations: 30,720

## 判定

**中核仮説は強く反証された。**

operationとepisode bindingを分離しても、local方式とbranch方式の全能力指標が完全に同一で、全splitがmargin 0による全面棄権となった。Cycle 004のidentity leakageだけが失敗原因ではなかった。

### 原因1: 候補構造が依然として同型

binding候補のentity/old/new境界は異なるが、多くの候補が同じ適用失敗または同じ表面置換結果を生成する。そのためreverse、other-identity、compositionを追加しても候補間energy差が生じない。

候補数64は構造多様性ではない。異なる候補が異なるworld transitionを生成していないため、energy landscapeが平坦化した。

### 原因2: operation nodeがsurface skeletonへ分裂

学習量48→384でoperation nodeが7.33→30.33へ増え、モデルbytesも1,229→4,923へ増加した。抽象operationが一つへ統合されたのではなく、命令surface skeletonごとのnodeへ断片化している。

binding分離はepisode identity leakageを減らしても、surface decoderとlatent operationの意味的商を形成していない。

### 原因3: blocked contextは意味factorではない

`固定中` / `保護中`という反復残差をcontext gateとして学習したが、候補間のbranch差を作らず、全候補へ同じ罰則を加えるだけである。これはaction/no-op/blockedを異なる実行graphとして生成したことにならない。

### 原因4: 緩和は安定して誤収束

発散はない。平均1.6 sweepで停止する。しかし停止先は正しいattractorではなく、全候補同率のmargin-collapse状態である。

- 局所最適: 全候補同率の平坦attractor
- 発散: なし
- 候補崩壊: 64候補が実質同型
- 選択的confound検出: 未成立
- unseen syntax: 未成立

## 系列E固有の新知見

> **operation/binding分離は必要条件だが十分条件ではない。energy緩和に必要なのは、境界やsurfaceだけが違う候補ではなく、異なるworld transitionを生成する意味的に非同型な候補graphである。**

さらに、branch条件をscalar penaltyとして追加しても、候補自身がaction/no-op/blockedを別々に実行生成しなければ選別力は生じない。

## 他系列へ返す知見

- A: 候補未来が表面差しか持たなければ、確認発話を生成しても本質的曖昧性を分離できない。
- B: operation encoder候補は、異なるargument-role graphと異なる実行結果を生成する必要がある。surface skeleton分離だけでは不足。
- C: action/no-op/blockedは同一operationへのscalar gateではなく、条件付きbranch programとして表現する必要がある。
- D: 暫定schema候補は、後続質問・更新に対して異なる想起結果を生まないなら別仮説として保持する価値がない。

## 次の仮説

**Role-Structured Conditional Attractor Graphs**

次はentity/old/newのspan境界候補だけでなく、次の構造が異なる候補graphを生成する。

1. argument role edge
2. operation target
3. relation being changed
4. context condition
5. action branch
6. no-op branch
7. blocked branch
8. inverse branch
9. non-target preservation branch

各候補は異なるworld transitionを実行し、可逆再構成、別identity再束縛、逆操作復元、blocked選択性、二段合成、後続観測予測で緩和する。

最低成功条件:

- seen accuracyを0から改善
- renameを0から改善
- normalを維持しblockedだけ選択的に棄権
- completely unseen syntaxを0から改善
- mean margin > 0
- surface skeleton数の線形増加を抑制

## 最終判定

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: 未達
