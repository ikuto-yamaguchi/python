# Phase 8c: multiple latent relations under partial, noisy, delayed interaction

## 目的

Phase 8bは単一のkey-value relationについて、intent名やentity/location型を与えず、観測された状態差分から `SET(key,value)` / `GET(key)` と2つのsymbol roleを復元しました。

Phase 8cでは、単一relationという強い仮定を外し、次を同時に満たせるかを検証します。

- 複数のrelationが混在する
- 世界状態は部分的にしか観測されない
- effectが1 step遅れて現れることがある
- responseや同時effectにnoiseが混ざる
- 偶然の相関を表面規則として永久保存しない
- relation数が増えても全規則を毎回走査しない

## 観測表現

世界状態は、意味名を持たないopaque channelとkeyの組をslotとします。

```text
(channel, key) -> value
```

実験生成器だけが、次のhidden meaningを知っています。

```text
c0: object -> location
c1: object -> owner
c2: file -> dependency
```

main learnerには `location`、`owner`、`dependency` という名前を渡しません。ただし、effectがどのopaque channelで生じたかはsensor interfaceから観測可能です。この点は完全なrelation発見ではなく、言語を未知のeffect channelへ接地する実験です。

部分観測では、slotがsnapshotに存在しないことを削除と見なしません。

```text
missing = unknown
explicitly observed old != new = transition evidence
```

これにより、sensorが読まなかった事実を勝手に消去したと誤認するのを防ぎます。

## 操作誘導

### 即時SET

pre/postの両方で観測された単一slotが変化し、utteranceにkeyとnew valueが含まれる場合、強い `SET` 証拠とします。

### 部分観測SET

preでは対象slotが未観測で、postで初めて観測され、utteranceにkey/valueが含まれる場合、弱い `SET` 証拠とします。

### 遅延SET

immediate observationでは変化せず、delayed observationで単一slotが変化した場合、latency 1の `SET` とします。

### GET

状態変化がなく、utteranceにkey、responseにkeyと現在valueが含まれる場合、`GET` とします。

複数slotが同時に変化したtraceや、responseが観測状態と一致しないtraceは、単一操作へ強制的に割り当てません。

## noiseへの対応

生の差分推定は、偶然同時に起きた1本のexogenous changeを誤って言語規則と結び付けます。

```text
青い箱と倉庫について雑談した
```

という発言中に、偶然 `c0(青い箱)=倉庫` への変化が観測されたケースです。

支持数1のlearnerは、

```text
{K}と{V}について雑談した -> SET(c0,K,V)
```

を保存してしまいます。

Phase 8cでは、規則候補を次で採用します。

```text
support >= 2
and confidence_sum >= 1.4
```

これはnoiseの一般解ではありません。相関noiseや敵対的noiseには弱い単純な基準です。ただし、誤りをゼロに見せるためにtraceを捨てるのではなく、生の適合率96%という失敗を残したうえで、コンパイル段階のMDL選択がheld-out regretを下げるかを測ります。

## 表現候補の競争

同じvalidationで次を比較します。

1. `exact_surface`
   - 観測文と操作を完全記憶
2. `support_1_schema`
   - key/value slotを再利用するが、単発規則も保存
3. `robust_multi_relation_schema`
   - opaque relationごとのroleと、複数traceで支持された規則だけ保存

目的関数は今回の有限実験では次です。

```text
J = description_bits + 1024 * heldout_errors
```

索引、symbol role、relation ID、templateはdescription bitsへ含めます。

## 実行時索引

relationや規則が増えるたび全ruleを走査すると、表現を圧縮しても計算効率が落ちます。

各templateの固定literal部分から最長cueを選び、cueから候補規則へ直接routeします。

```text
{K}の持ち主は?        -> cue: の持ち主は?
{K}を{V}に移して      -> cue: に移して
{K}は{V}に依存する    -> cue: に依存する
```

cue indexのpointer bitもdescription lengthへ含めます。

## 新relationの追加

未知channel `c3` に対し、同一templateを持つ2つの一貫したtransitionを観測します。

```text
障害Aの優先度は高
障害Bの優先度は低
```

これにより新しいrelation schemaを1規則だけ追加し、

```text
障害Aの優先度は低
```

という未観測key/value組合せを処理できるか確認します。

単一traceだけでは、偶然の相関と区別できないため永続規則へ昇格させません。

## 成功条件

- full / partial / delayed SETをすべて復元
- GETをすべて復元
- 支持数1の偶然規則をコンパイルしない
- 3 relationの未知symbol組合せで100% exact operation
- role反転命令を拒否
- 索引込みの総bitで表面記憶より小さい
- 新relationを規則1個で追加し、held-out recombinationへ転移

## 限界

- opaque effect-channel IDは観測可能
- 言語候補は制限されたtemplate DSL
- latencyは1 stepのみ
- support thresholdはnoise modelとして非常に単純
- hidden stateや複数原因のcredit assignmentは未解決
- open-domainのpredicate、goal、tool programは未誘導

## 次段階

Phase 8dではchannel ID自体を直接使わず、複数sensor streamとaction resultの共変動からrelation partitionを探索します。

また、次を追加します。

- 2〜8 stepの遅延effect
- hidden intermediary state
- probabilistic effect
- contradictionとretraction
- 会話、文章、コード、tool actionの混合trace
- exhaustive partition oracleとのregret比較

候補relationを増やすだけでなく、既存relationのmerge、split、削除も同じ生涯目的で競わせます。
