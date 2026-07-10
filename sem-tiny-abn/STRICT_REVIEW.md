# 元ABN実装との厳密比較レビュー

比較対象:

- MPRG公式ABN: https://github.com/machine-perception-robotics-group/attention_branch_network
- ABN論文: https://openaccess.thecvf.com/content_CVPR_2019/html/Fukui_Attention_Branch_Network_Learning_of_Attention_Mechanism_for_Visual_Explanation_CVPR_2019_paper.html

## 1. Attentionを入れる位置

公式ABNは、中間特徴からAttention branchを分岐し、Attentionを掛けた特徴を後段のPerception branchへ通します。

```text
shared feature
  ├─ Attention branch → auxiliary logits + attention
  └─ (1 + attention) × shared feature → perception tail → final logits
```

旧TinyABNは最終特徴へAttentionを掛け、その直後にGAP+Linearを行っていました。後段で再解釈する層がなく、Attentionが分類精度向上へ寄与しにくい構造でした。修正版はshared trunkとperception tailを分離しています。

## 2. Attention branchの教師信号

公式ABNでは、クラス関連feature mapをGAPして補助分類し、そのmapからAttentionを生成します。旧実装は補助分類headとAttention生成headが別経路で、補助LossがAttention自体を十分に形作らない可能性がありました。

修正版は `class_maps → aux_logits` と `class_maps → attention` を共有します。

## 3. 正規化層

公式実装は大きなbatchを前提にBatchNormを使います。1024画像を弱いPCで学習するとbatch size 1〜4になりやすく、BatchNorm統計が不安定です。修正版はGroupNormを標準にし、BatchNormも比較用に選択可能です。

## 4. モデル容量

旧TinyABN width=1.0は約1万パラメータしかなく、複雑な形態差を学習するには過小な可能性が高い状態でした。修正版の標準構成は約19万パラメータ級で、width/depthを増やせます。それでもResNet18単体の約1170万パラメータより大幅に小さい範囲です。

軽量化率だけを目的にせず、validationのFalse OK/NGを見ながら容量を増やします。

## 5. 微小異常とpooling

Global Average Poolingだけでは、画像中のごく小さい異常応答が平均で薄まります。修正版はAverageとMaxを結合し、全体形態と局所ピークを両方残します。

## 6. 差分入力

旧実装の単純な `SEM - blurred design` は、輝度、白黒極性、数pxの位置ずれに敏感でした。

修正版:

- percentile正規化
- SEM極性の固定またはauto判定
- design blur
- designの膨張/収縮相当の許容帯
- 許容帯を超えた部分だけpos/neg差分化

これにより「形態は同じだがエッジ位置が少し違う」画像を差分だけでNGへ寄せる危険を減らします。

## 7. 学習Loss

公式ABNはAttention branch LossとPerception branch Lossを加算します。修正版も標準 `aux_weight: 1.0` としています。

旧Focal Lossはclass weight込みCEから `pt` を作っており、正しい確率項ではありませんでした。修正版は重みなしCEから `pt` を計算します。また、Focal Lossとclass weightの併用は過剰補正になり得るため、初期値は通常CrossEntropyです。

## 8. データリーク

画像単位のランダム分割では、同一設計、同一ウェハ、近接FOVがtrain/valへ分かれ、精度が不当に高くなる可能性があります。

CSVの `group`, `pattern_id`, `wafer`, `lot` を使えばgroup単位で分割します。最も厳密なのはCSVの `split` 列を明示する方法です。

## 9. 判定閾値

固定0.98は根拠がなく、モデルやデータごとに適切な値が変わります。修正版は検証データから、設定されたFalse OK率を満たすOK閾値を校正してcheckpointへ保存します。

ただし、閾値を決めたvalidationと最終性能を報告するtestは分離するのが理想です。

## 10. CPU高速化

パラメータ数が少ないdepthwise convolutionが、すべてのCPUで速いとは限りません。ライブラリやSIMD最適化によって通常3x3 Convの方が速い場合があります。

- `block_type: standard`: CPU標準候補
- `block_type: mobile`: パラメータ/メモリ削減候補

`model_summary.py` と `benchmark.py` で対象PC上の実測を優先します。

## 11. Frequency版

旧TinyFreqABNはチャンネル前半/後半をlow/highと呼んだだけで、周波数分離の保証がありませんでした。修正版は空間low-passとhigh residualへ明示分解します。

ただし、これは周波数画像再構成Lossを使うFrequency-Aware Spatial Attentionの完全再現ではありません。名称と説明で軽量近似だと明記しています。

## 12. 残る限界

- OK/NG画像ラベルだけでは、欠陥位置を直接教師にできない
- Attention mapは欠陥マスクの保証ではない
- 未知条件で100%は保証できない
- validationだけで閾値調整すると最終性能を過大評価し得る
- SEM/Designの白黒極性や許容pxは実データで確定が必要

したがって、独立testセット、装置/レイヤ/期間別評価、False OKの全件目視が必要です。
