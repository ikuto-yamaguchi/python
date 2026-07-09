# SEM Tiny ABN

CD-SEM画像と設計パターン画像のペアを見て、`OK` / `NG` を高速に判定するための **TinyCNN + 軽量ABN** 実装です。

社内の弱めCPU環境でも試しやすいように、モデルはかなり小さめにしています。差分画像はファイルとして保存せず、学習・推論時にメモリ上で作ります。

## まず最初に読むところ

この実装は、次のようなデータを想定しています。

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

最初に実行するコマンドはこれです。

```bash
cd sem-tiny-abn
pip install -r requirements.txt

python -m sem_tiny_abn.train \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --out runs/sem_tiny_abn \
  --model tiny_abn \
  --image-size 128 \
  --epochs 30 \
  --batch-size 32 \
  --device cpu
```

学習が終わったら、評価します。

```bash
python -m sem_tiny_abn.evaluate \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --device cpu
```

## 何をするもの？

1サンプルにつき、次の2枚の画像を使います。

- SEM画像: 512×512 または 1024×1024 などのモノクロ画像
- Design画像: SEM画像と位置合わせ済みの設計パターン画像
- CSV: `OK` / `NG` のアノテーション

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

計算式はこうです。

```text
pos_diff = max(SEM_norm - soft_design, 0)
neg_diff = max(soft_design - SEM_norm, 0)
```

`soft_design` を使う理由は、設計画像の硬いエッジとSEM画像のぼやけたエッジをそのまま比較すると、少しのエッジ位置ずれでも過剰にNG寄りになりやすいからです。

## なぜ差分画像を保存しないの？

保存しません。

```text
悪い案:
  差分画像をPNGなどで保存する
  → ディスクI/Oが増える
  → ファイル管理が面倒
  → 学習前の前処理も重い

今回の案:
  学習・推論時にメモリ上で差分を作る
  → 速い
  → 管理が楽
  → SEM/Designへの回転・反転augmentationとも合わせやすい
```

そのため、差分画像を作ること自体による大きなタイムロスは避けています。

## 画像の回転・反転について

水平反転、垂直反転、90度回転は、SEM画像とDesign画像に **必ず同じ変換** をかけます。

```text
SEM画像      ┐
Design画像   ├─ 同じ回転・同じ反転
差分チャンネル ┘
```

これにより、方向依存性を減らしながら、SEMとDesignの対応関係は壊さないようにしています。

## CSV形式

基本形はこれです。

```csv
sem,design,label
sem_0001.png,design_0001.png,OK
sem_0002.png,design_0002.png,NG
```

列名は次の別名にも対応しています。

```text
SEM画像:
  sem, sem_path, sem_image, image_sem

Design画像:
  design, design_path, pattern, design_image, image_design

ラベル:
  label, target, class
```

画像パスは `--data-root` からの相対パスでOKです。

## 使う手順

```bash
cd sem-tiny-abn
python -m venv .venv
```

Linux / WSL の場合:

```bash
source .venv/bin/activate
```

Windows の場合:

```bash
.venv\Scripts\activate
```

必要ライブラリを入れます。

```bash
pip install -r requirements.txt
```

## 学習する

まずはこれで十分です。

```bash
python -m sem_tiny_abn.train \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --out runs/sem_tiny_abn \
  --model tiny_abn \
  --image-size 128 \
  --epochs 30 \
  --batch-size 32 \
  --device cpu
```

意味はこうです。

```text
--data-root
  SEM画像とDesign画像が入っているフォルダ

--csv
  sem, design, label が書かれたCSV

--out
  学習結果の保存先

--model tiny_abn
  TinyCNN + 軽量ABNを使う

--image-size 128
  512/1024画像を128×128に縮小して学習する
  速度優先なら128から開始

--device cpu
  CPUで実行する
```

## 評価する

```bash
python -m sem_tiny_abn.evaluate \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --device cpu
```

評価では、通常の正解率だけでなく、検査用途で重要な次の数も出します。

```text
false_ok:
  本当はNGなのにOKと判定した数
  一番危険

false_ng:
  本当はOKなのにNGと判定した数
  過検出
```

## 推論する

```bash
python -m sem_tiny_abn.predict \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out-csv runs/sem_tiny_abn/predictions.csv \
  --device cpu
```

Attention画像も保存したい場合:

```bash
python -m sem_tiny_abn.predict \
  --data-root /path/to/画像フォルダ \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out-csv runs/sem_tiny_abn/predictions.csv \
  --save-attention runs/sem_tiny_abn/attention \
  --device cpu
```

## CPU速度を測る

```bash
python -m sem_tiny_abn.benchmark \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --batch-size 1 \
  --iters 300 \
  --device cpu
```

## ONNXに変換する

```bash
python -m sem_tiny_abn.export_onnx \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out runs/sem_tiny_abn/model.onnx
```

ONNX化しておくと、あとでONNX RuntimeやOpenVINOでCPU推論を高速化しやすくなります。

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

形態差とエッジ位置ずれを分けて見たい場合の実験用です。

## OK/NGだけで始める場合

デフォルトはこれです。

```bash
--classes OK,NG --task multiclass
```

つまり、今のアノテーションがOK/NGだけでも使えます。

## あとから分類を増やす場合

コードを直さずに、クラス指定だけ変えられます。

例:

```bash
--classes OK,NG,EDGE_SHIFT,REVIEW
```

ただし、CSVの `label` にも同じラベルを書く必要があります。

例:

```csv
sem,design,label
sem_0001.png,design_0001.png,OK
sem_0002.png,design_0002.png,NG
sem_0003.png,design_0003.png,EDGE_SHIFT
sem_0004.png,design_0004.png,REVIEW
```

いきなり8分類にしなくても、まずは次の4分類くらいが現実的です。

```text
OK
NG
EDGE_SHIFT
REVIEW
```

## 100%精度について

この実装は高精度を狙うための土台ですが、未知データに対してモデル単体で100%を保証することはできません。

量産・検査用途で本当に大事なのは、単純な正解率よりも **false_okをどれだけ減らすか** です。

そのため、推論スクリプトには `--ok-threshold` を入れています。

例:

```bash
--ok-threshold 0.98
```

これは、OK確率が98%以上のときだけOKにする、という意味です。

```text
OK確率が高い:
  OK

OK確率が微妙:
  NG または REVIEW 側に倒す
```

OK/NGだけのラベル運用でも、この閾値を使うことで、危険な false OK を減らしやすくしています。

## 最初に試すおすすめ順

### 1. tiny_cnn

```bash
--model tiny_cnn
```

ABNなしの速度と精度を見る基準です。

### 2. tiny_abn

```bash
--model tiny_abn
```

まず使う本命です。

### 3. tiny_freq_abn

```bash
--model tiny_freq_abn
```

形態差と細かいエッジ反応を分けて見たい場合に試します。

## 実運用で見るべき指標

正解率だけでは危ないです。

必ず次を見てください。

```text
accuracy:
  全体正解率

false_ok:
  NGをOKにしてしまった数
  最重要

false_ng:
  OKをNGにしてしまった数
  過検出

attention:
  モデルが差分領域や形態差を見ているか
```

## 重要な注意

このモデルは、512×512や1024×1024の画像全体をそのまま重いResNetに入れるのではなく、128×128などへ縮小して軽量判定する設計です。

微小なbridge/breakを絶対に見たい場合は、将来的には次の構成が必要になるかもしれません。

```text
512/1024全体
  ↓
差分component抽出
  ↓
怪しい場所だけ128×128 patchに切り出し
  ↓
TinyABNでpatch判定
```

今回の実装は、その前段階として、まず全体縮小版で高速に試せるようにしています。
