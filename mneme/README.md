# MNEME — トークナイザーフリー・外部完全記憶型の特化知能アーキテクチャ

**Memory-Native Efficient Model**(研究プロトタイプ)

> 仮説: 賢い(汎用処理能力を持つ)小さな知能コアと、圧倒的に正確で大量の外部記憶を分離すれば、はるかに少ない計算資源で複雑な特化タスクをこなせる。トークナイザーと「知識のパラメータ焼き込み」はどちらも特化 AI には不要である。

設計の詳細と関連研究は [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) を参照。

## アーキテクチャ概要

```
生バイト列(0-255。語彙表なし・OOV なし・前処理なし)
  │
  ▼
[1] EntropyPatcher   極小バイト LM(約 5 万パラメータ)が次バイト予測エントロピーを
  │                  推定し、情報量が跳ねる位置で可変長パッチに分割
  ▼                  → トークナイザーの完全な置き換え。潜在系列長はバイト列の約 1/6
[2] LatentCore       パッチ潜在列上の小さな因果 Transformer。知識を持たず処理に徹する
  │                  + MemoryAttention: 外部記憶からのゲート付き読み出し
  ▼
[3] EpisodicMemory   (key, value) 潜在ベクトルの外部完全記憶。
  │                  書き込みは append のみ(勾配 0)、読み出しはコサイン top-k 完全検索
  ▼
LocalDecoder         パッチ単位でバイト列を自己回帰復号
```

## 実験結果

### 実験 1: 知識想起 — 外部記憶 vs パラメータ記憶(`experiments/run_recall_benchmark.py`)

ランダムな key(8 文字)→ value(6 文字)の事実 N 件を保持し、完全一致で想起できるかを測定。両モデルはほぼ同規模(MNEME 68 万 / ベースライン 71 万パラメータ)。

- **MNEME**: 汎用コーデック(文字列⇄潜在の可逆写像)を**事実を一切見せずに一度だけ**学習。事実は外部記憶へ書き込むのみ
- **ベースライン**: 事実集合そのものを end-to-end 勾配学習で重みに焼き込む(通常の LLM の知識保持の縮図)

CPU(4 コア)での実測:

| 事実数 N | MNEME(外部記憶) | 知識の追加コスト | ベースライン(パラメータ記憶) | 知識の追加コスト |
|---:|---:|---|---:|---|
| 64 | 93.8% | 書込 0.02s・勾配 **0** step | 100.0% | 再学習 117s・勾配 2000 step |
| 256 | 96.5% | 書込 0.11s・勾配 **0** step | 100.0% | 再学習 112s・勾配 2000 step |
| 1024 | 93.8% | 書込 0.18s・勾配 **0** step | 100.0% | 再学習 97s・勾配 2000 step |
| 4096 | **94.3%** | 書込 0.66s・勾配 **0** step | **8.3%(崩壊)** | 再学習 98s・勾配 2000 step |

**読み方:**

1. **容量とコストの分離** — MNEME の精度は事実数に対して平坦(残り約 6% は復号誤りで、コーデックの学習を延ばせば縮む)。パラメータ記憶は固定学習予算では N=4096 で崩壊した。重みの記憶容量には上限(約 2 bit/パラメータ, Allen-Zhu & Li 2024)があるが、外部記憶はストアを足すだけで際限なく増える
2. **知識追加のコスト差が 5 桁** — 事実 1 件あたり: MNEME はエンコード 1 回(サブミリ秒・勾配 0)、ベースラインは全再学習が必要
3. **知識編集** — 学習に一度も出てこなかった新事実 5 件を書き込むだけで即座に想起できた(5 件中 4 件完全一致)。削除・上書きもエントリ単位で可能

### 実験 2: エントロピー動的パッチング(`experiments/run_patcher_demo.py`)

約 7 万パラメータの極小バイト LM を小コーパスで学習し、次バイト予測エントロピーが閾値(0.195 bits)を超える位置でパッチを区切った実測:

```
  [ 35 bytes -> 11 patches] Me|m|or|y |i|s |the mother |of all |wi|s|dom.
  [ 44 bytes ->  9 patches] T|h|e |qui|c|k brown fox |jumps over |the |lazy dog.
  [ 28 bytes -> 26 patches] z|q|x|v| |jk|w|p| |u|n|s|e|e|n| |b|y|t|e|s| |1|2|3|45
```

- 予測が容易な区間(`the mother `、`jumps over `)は 1 パッチに圧縮され、情報が跳ねる位置(単語頭・分布外の羅列)では細かく切れる — 計算資源が情報密度に比例して配分される
- ドメイン内テキストの平均パッチ長は **5.21 bytes/patch** → 知能コアが見る系列長はバイト列の 1/5.2、O(L²) の注意計算は約 **1/27**
- 語彙表は 0 エントリ。ドメインが変われば、この 7 万パラメータの推定器を差し替えるだけで本体の再学習なしに再適応できる(BPE 語彙の数千万パラメータの埋め込み表と対照的)

## 使い方

```bash
pip install -r requirements.txt   # torch のみ

python tests/test_mneme.py                    # スモークテスト(7 件)
python experiments/run_patcher_demo.py        # 実験 2: 動的パッチング(数分)
python experiments/run_recall_benchmark.py    # 実験 1: 知識想起(CPU で 30-40 分)
```

```python
from mneme import MemoryRecallModel, make_facts

model = MemoryRecallModel()
model.train_codec(steps=1500)        # 汎用の符号化・復号スキルを一度だけ学習

facts = make_facts(1000)             # 知識は…
model.write_facts(facts)             # …書き込むだけ(勾配 0 ステップ)
model.answer(["<key>"])              # 完全検索 + 復号で想起
```

## リポジトリ構成

```
mneme/
  mneme/
    patcher.py    エントロピー動的パッチング(トークナイザーの置き換え)
    memory.py     外部エピソード記憶(完全 top-k 検索・追記型)
    modules.py    バイトレベル符号化・復号(語彙 = 256 バイト + 特殊 3 記号)
    recall.py     知識想起の検証モデル(外部記憶 vs パラメータ記憶)
    lm.py         MnemeLM: 全コンポーネント結合の生成モデル
  experiments/    実験スクリプト
  tests/          スモークテスト
  docs/ARCHITECTURE.md  設計書(課題認識・設計原理・関連研究・今後の課題)
```

## 限界

本実装は数十万パラメータ規模・合成タスクでの**原理検証**である。実タスクへのスケール、近似最近傍検索(FAISS 等)への置き換え、多段の read→think→read 推論、書き込み方策の学習などは [docs/ARCHITECTURE.md の §6](docs/ARCHITECTURE.md) を参照。
