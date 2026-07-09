# SEM Tiny ABN

CD-SEM画像と設計パターン画像のペアを見て、`OK` / `NG` を高速に判定するための **TinyCNN + 軽量ABN** 実装です。

実装は **PyTorch** です。学習はPyTorchで行い、推論高速化用にONNX出力もできます。

## 重要な方針変更

128×128固定はやめました。

微小なパターンや細いbridge/breakを見る用途では、128×128まで潰すと情報が消えます。現在のデフォルトは `image_size: 512` です。余裕があれば `1024` も使えます。

```text
軽さ優先:
  image_size: 256

まずの推奨:
  image_size: 512

微細差分重視:
  image_size: 1024
```

さらに、将来のためにタイル学習・タイル推論も入れています。

```text
全体を見る:
  crop_mode: resize

ランダムパッチで学習:
  crop_mode: random_tile
  tile_size: 256

高解像度をタイル走査で推論:
  python -m sem_tiny_abn.tile_predict
```

## まず最初にやること

`configs/default.yaml` を開いて、次の2つを書き換えてください。

```yaml
data_root: /path/to/画像フォルダ
csv: /path/to/annotations.csv
```

その後は、長いコマンドを書かずにこれで学習できます。

```bash
cd sem-tiny-abn
pip install -r requirements.txt
python -m sem_tiny_abn.train --config configs/default.yaml
```

評価はこれです。

```bash
python -m sem_tiny_abn.evaluate \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --device cpu
```

## データ形式

```text
任意のフォルダ/
  sem_0001.png
  design_0001.png
  sem_0002.png
  design_0002.png
  annotations.csv
```

CSVはこうです。

```csv
sem,design,label
sem_0001.png,design_0001.png,OK
sem_0002.png,design_0002.png,NG
```

## モデル入力

デフォルトでは、内部的に次の4チャンネルを作ってモデルに渡します。

```text
1. SEM_norm
   正規化したSEM画像

2. soft_design
   設計パターン画像を少しぼかしたもの

3. pos_diff
   SEM側に余計に出ている差分
   太り・余計な接続・bridge寄りの情報

4. neg_diff
   設計にはあるのにSEM側で足りない差分
   細り・欠け・break寄りの情報
```

差分画像は保存しません。学習・推論時にメモリ上で作ります。

```text
pos_diff = max(SEM_norm - soft_design, 0)
neg_diff = max(soft_design - SEM_norm, 0)
```

## 画像の回転・反転

水平反転、垂直反転、90度回転は、SEM画像とDesign画像に **必ず同じ変換** をかけます。

```text
SEM画像      ┐
Design画像   ├─ 同じ回転・同じ反転
差分チャンネル ┘
```

片方だけ回すことはありません。

## モデルの種類

### tiny_cnn

一番小さいモデルです。Attentionなし。

```text
用途:
  速度の基準を見る
  ABNなしでも十分か確認する
```

### tiny_abn

TinyCNNに軽量ABNを足したモデルです。まずはこれがおすすめです。

```text
用途:
  OK/NG判定
  Attention mapを人間が確認する
```

### tiny_freq_abn

特徴チャンネルを2つに分けて、粗いAttentionと細かいAttentionを出すモデルです。

```text
attention_low:
  大まかな形態・パターン構造を見る想定

attention_high:
  細かいエッジ・局所差分を見る想定
```

## 設定ファイルで管理する

毎回コマンドでパラメータを書く必要はありません。

`configs/default.yaml` を編集します。

```yaml
model: tiny_abn
image_size: 512
crop_mode: resize
tile_size: 256
width: 1.0
batch_size: 8
device: cpu
```

精度が足りなければ、段階的にこう増やします。

```yaml
width: 1.25
```

さらに強くするなら、

```yaml
width: 1.5
```

または、

```yaml
model: tiny_freq_abn
```

へ変更します。

## 誤判定を可視化する

OKなのにNG、NGなのにOKの画像を、SEM/Design/差分/Attentionで俯瞰するPNGとして保存できます。

```bash
python -m sem_tiny_abn.visualize_errors \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out runs/sem_tiny_abn/error_report \
  --device cpu
```

出力はこういう構成です。

```text
runs/sem_tiny_abn/error_report/
  false_ok/
    000001_NG_to_OK.png
  false_ng/
    000002_OK_to_NG.png
```

1枚のPNGに次を並べます。

```text
SEM
Design/soft_design
pos_diff
neg_diff
abs_diff
Attention
```

これで、単なる枚数だけでなく、どこを見て間違えたのかを確認できます。

## 高解像度タイル推論

512/1024全体を縮小せず、タイルで細かく見たい場合はこちらです。

```bash
python -m sem_tiny_abn.tile_predict \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out-csv runs/sem_tiny_abn/tile_predictions.csv \
  --tile-size 256 \
  --stride 128 \
  --device cpu
```

各画像を256×256タイルで走査し、最もNGっぽいタイルを画像全体の判定に反映します。微小なNGを拾いたい場合の安全寄り推論です。

## CPU速度を測る

```bash
python -m sem_tiny_abn.benchmark \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --batch-size 1 \
  --iters 300 \
  --device cpu
```

## モデル規模を確認する

```bash
python -m sem_tiny_abn.model_summary \
  --model tiny_abn \
  --image-size 512 \
  --width 1.0
```

`width` を変えることで、軽量版から少し大きめのモデルまで段階的に調整できます。

## ONNXに変換する

```bash
python -m sem_tiny_abn.export_onnx \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out runs/sem_tiny_abn/model.onnx
```

ONNX化しておくと、あとでONNX RuntimeやOpenVINOでCPU推論を高速化しやすくなります。

## 藤吉研究室のABNとの軽量性イメージ

本家ABNはResNetなどの通常backboneにAttention branchを足す構成です。今回のTinyABNは、最初からdepthwise separable convolution中心の小型backboneにしています。

ざっくりした想定はこうです。

```text
本家ABN + ResNet18級:
  数千万パラメータ級になりやすい
  精度は出やすいがCPUでは重い

今回の TinyABN width=1.0:
  かなり小さい
  CPUで試しやすい
  ただし軽すぎる場合は width を上げる

今回の TinyFreqABN:
  TinyABNより少し重い
  形態差と細部Attentionを分けて見たい場合に使う
```

正確なパラメータ数は `model_summary.py` で確認してください。

## 100%精度について

この実装は高精度を狙うための土台ですが、未知データに対してモデル単体で100%を保証することはできません。

量産・検査用途で本当に大事なのは、単純な正解率よりも **false_okをどれだけ減らすか** です。

そのため、推論スクリプトには `--ok-threshold` やタイル推論の `--ng-threshold` を入れています。

## 推奨の試し方

最初:

```yaml
model: tiny_abn
image_size: 512
crop_mode: resize
width: 1.0
batch_size: 8
```

微細差分が見えない場合:

```yaml
image_size: 1024
batch_size: 1
```

速度が厳しい場合:

```yaml
crop_mode: random_tile
tile_size: 256
batch_size: 16
```

精度が足りない場合:

```yaml
width: 1.5
```

形態差と細部を分けて見たい場合:

```yaml
model: tiny_freq_abn
```
