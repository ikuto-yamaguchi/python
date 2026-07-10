# SEM Tiny ABN

位置合わせ済みのSEM画像と設計パターン画像から、`OK` / `NG` を判定するPyTorch実装です。藤吉研究室/MPRGのABN構造を参考にしつつ、512〜1024画像、CPU、小さいbatch、微小欠陥を想定して再設計しています。

> 100%精度を保証するものではありません。検査用途では全体正答率より、NGをOKにする **False OK** を最優先で管理します。

## 厳密レビュー後に直した点

- Attentionを最終特徴へ掛けるだけの旧構造を廃止
- 本家ABNに合わせ、**中間特徴 → Attention → Perception tail** の順へ変更
- 補助分類とAttention mapを同じclass mapから生成
- batch size 1でも不安定になりにくいGroupNormを標準化
- 約1万パラメータだった過小モデルを、標準設定で約19万パラメータ級へ拡張
- Average Poolingだけで微小欠陥が薄まらないようAvg+Max poolingを採用
- 生の輝度差分をやめ、数pxの位置ずれを許容した `pos_diff` / `neg_diff` を生成
- 同一パターンや同一ウェハがtrain/valへ漏れないgroup-aware splitに対応
- 固定0.98ではなく、検証データからOK閾値を校正
- False OK率を最優先してbest checkpointを選択
- resume、last checkpoint、early stopping、勾配clipを追加
- 誤判定をSEM/Design/差分/AttentionのHTMLギャラリーで確認可能
- 危険なランダムタイル学習と、分布が変わるタイル推論を削除

詳細は [STRICT_REVIEW.md](STRICT_REVIEW.md) を参照してください。

## CSV

最小形式:

```csv
sem,design,label
sem_0001.png,design_0001.png,OK
sem_0002.png,design_0002.png,NG
```

精度評価を信用できるものにするため、可能なら `group` または `split` を追加してください。

```csv
sem,design,label,group,split
sem_0001.png,design_0001.png,OK,pattern_A,train
sem_0002.png,design_0002.png,NG,pattern_B,val
```

`group` の別名として `pattern_id`, `wafer`, `wafer_id`, `lot`, `lot_id` なども認識します。同じgroupはtrain/valへ跨ぎません。

## セットアップ

```bash
cd sem-tiny-abn
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`configs/default.yaml` の `data_root` と `csv` を変更します。

## 学習

```bash
python -m sem_tiny_abn.train --config configs/default.yaml
```

出力:

```text
runs/sem_tiny_abn/
  best.pt
  last.pt
  run_info.json
  train_log.json
```

中断再開:

```bash
python -m sem_tiny_abn.train \
  --config configs/default.yaml \
  --resume runs/sem_tiny_abn/last.pt
```

## 評価

```bash
python -m sem_tiny_abn.evaluate --config configs/default.yaml
```

`evaluation.json` に、argmax精度、閾値適用後精度、False OK/NG率、confusion matrixを保存します。

## 推論

```bash
python -m sem_tiny_abn.predict --config configs/default.yaml
```

学習時に検証データから決めた `decision_threshold` がcheckpointへ保存され、その値を使います。

## 誤判定の俯瞰レポート

```bash
python -m sem_tiny_abn.visualize_errors --config configs/default.yaml
```

以下を1枚に並べ、`error_report/index.html` から一覧できます。

- 正規化SEM
- soft design
- 許容帯付きabs diff
- pos diff
- neg diff
- SEMへのAttention overlay

## モデル規模と速度

```bash
python -m sem_tiny_abn.model_summary \
  --model tiny_abn \
  --image-size 512 \
  --width 1.0 \
  --depth 1 \
  --block-type standard
```

実データ前処理込み:

```bash
python -m sem_tiny_abn.benchmark \
  --config configs/default.yaml \
  --with-preprocess \
  --threads 1
```

パラメータ数が少なくてもdepthwise convolutionがCPUで速いとは限りません。`standard` と `mobile` を実機で比較してください。

## 段階的な拡張

最初:

```yaml
model: tiny_abn
width: 1.0
depth: 1
block_type: standard
```

容量不足なら:

```yaml
width: 1.5
```

さらに必要なら:

```yaml
depth: 2
```

周波数分離の実験版:

```yaml
model: tiny_freq_abn
```

`tiny_freq_abn` は固定low-passとhigh residualを用いる軽量近似であり、再構成Lossを使うFrequency-Aware ABN論文の完全再現ではありません。

## ONNX

```bash
python -m sem_tiny_abn.export_onnx \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out runs/sem_tiny_abn/model.onnx \
  --include-attention
```

ONNX Runtime/OpenVINOでの実速度は、PyTorchとは別に対象PCで測定してください。

## テスト

```bash
pip install -r requirements-dev.txt
pytest -q
```
