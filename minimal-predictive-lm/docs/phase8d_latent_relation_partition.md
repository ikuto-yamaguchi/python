# Phase 8d: latent relation partition from anonymous sensor cells

## 目的

Phase 8cではrelationの意味名は与えませんでしたが、effectがどのopaque channelで生じたかはsensor interfaceから観測できました。

Phase 8dではchannel IDを外します。learnerが受け取るのは次だけです。

- entityごとに属する2つのanonymous sensor cell
- utterance中のentityとvalue
- action前後4 stepのsensor timeline
- 新entityでの少数calibration trace

どのcellがlocation、ownerなどのrelationに対応するかはentityごとにpermuteされています。

## micro-world

hidden generatorは2 relationを持ちます。

```text
location: lag 2
owner:    lag 1
```

4 surface templatesがあります。

```text
{K}を{V}に移動
{K}の場所を{V}にする
{K}を{V}に渡す
{K}の担当を{V}にする
```

main learnerには、前2つが同じrelation、後2つが同じrelationだとは教えません。

entityごとのcell対応も異なります。

```text
箱A: location=a0, owner=a1
箱B: location=b1, owner=b0
箱C: location=c0, owner=c1
箱D: location=d1, owner=d0
```

## effect candidate抽出

各cellについて、baselineからutterance中のvalueへ最初に変化したlagだけを候補にします。

```text
candidate = (anonymous cell, first matching lag)
```

1 traceだけ、lag 1で誤ったcellにも同じvalueが現れ、lag 2で本当のcellが変わるambiguous noiseを入れます。

この段階ではどちらが真か決めません。複数template・複数entityに共通するrelation構造で後から解決します。

## relation partition探索

4 templateのset partitionをすべて列挙します。Bell number `B4=15` なので、小世界ではoracleとして全探索できます。

各clusterについて次を選びます。

- relation共通lag
- entityごとのanonymous cell

train traceを最も多く説明する組を選び、さらに新entityでのtransferを評価します。

## 新entityでの評価

新しい箱E・箱Fには、relationごとに1 templateだけcalibrationとして見せます。

```text
location calibration: {K}を{V}に移動
owner calibration:    {K}を{V}に渡す
```

評価では、同じrelationの別templateを使います。

```text
location held-out: {K}の場所を{V}にする
owner held-out:    {K}の担当を{V}にする
```

surface templateを4つの独立relationとして丸暗記すると、calibrationしたclusterとheld-out clusterが別なので転移できません。

## 目的関数

有限実験では次を使います。

```text
J = description bits
  + 512 * training effect errors
  + 1024 * new-entity validation errors
```

記述量には次を含めます。

- cluster schema
- templateからclusterへの割当
- entityごとのcluster-to-cell割当
- relation lag

## 成功条件

- true effectがcandidate集合から落ちない
- ambiguous traceを共有構造で正しいcell/lagへ解決
- hidden 2-relation partitionをexact recovery
- lag 1 / lag 2を復元
- training error 0
- relationごと1回のcalibrationから新entityで100% transfer
- merged、over-split、flat memorizationより生涯目的が小さい

## 結果の意味

選択されたpartitionは次です。

```text
location cluster:
  {K}を{V}に移動
  {K}の場所を{V}にする
  lag 2

owner cluster:
  {K}を{V}に渡す
  {K}の担当を{V}にする
  lag 1
```

relationの人間語ラベルはevaluation用です。learner内部ではcluster 0 / 1です。

4-cluster modelはtraining error 0ですが、新entityではcalibration templateからparaphraseへ情報を移せず0%です。2-cluster modelは100%です。

## スケーリング上の失敗

set partition全探索はBell numberで増えます。

| templates | partitions |
|---:|---:|
| 4 | 15 |
| 6 | 203 |
| 8 | 4,140 |
| 10 | 115,975 |
| 12 | 4,213,597 |

したがって、Phase 8dの全探索は下限・oracle比較用であり、汎用learnerには使えません。

## 表現スケーリング

32 surface templatesが2 latent relationsから生成される場合、entity-template個別割当は `O(E*T)`、latent partitionは `O(E*R + T log R)` です。

実験と同じ概念bit式では、entity 512で16,384bit対1,110bit、約14.76倍になります。

## 限界

- entityとそのsensor cell集合はinterfaceから与える
- relation数は未知だが、各entityにcellが2つという構造は既知
- effectは決定論的
- relationごとに固定lag
- utteranceのvalueがsensorにもそのまま現れる
- template DSLは制限済み
- 4 templateだけ全探索
- causal directionやhidden intermediary programは未発見

## 次段階

Phase 8eではBell全探索をやめ、residual collisionから必要なsplitだけを提案します。

1. 現在clusterで説明できないtraceを集める
2. cell・lag・結果の最小差分を見つける
3. cluster split候補を生成する
4. held-out regret削減が追加bit・探索費用を上回る場合だけ採用
5. 不要になったclusterをmerge / deleteする

さらに、relation数2固定、value完全一致、固定lagの仮定を順に外します。
