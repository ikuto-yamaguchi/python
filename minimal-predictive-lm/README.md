# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測に必要な**最小記憶**と**最小計算**を数学的な下限から逆算する研究用ディレクトリです。

## 中心仮説

過去全文を保持する必要はない。同じ未来分布を与える履歴は、予測上は同一状態へ圧縮できる。

\[
h \sim h' \iff P(X_{future}\mid h)=P(X_{future}\mid h')
\]

ただし、最小状態数だけでは十分ではありません。状態をKビットへ圧縮できても、遷移表が `2^K` に膨張すればモデル記憶は最小になりません。

したがって、最終的な目的関数は少なくとも次を同時に最小化します。

\[
J = L_{prediction}
+ \lambda_s B(state)
+ \lambda_p L(transition\ program)
+ \lambda_r E[bits\ read]
+ \lambda_w E[bits\ written]
+ \lambda_o E[operations]
\]

- `B(state)`: 実行時の予測状態ビット数
- `L(transition program)`: 状態遷移法則そのものの記述長
- `bits read / written`: 動的メモリ通信量
- `operations`: 実際の演算量

## Phase 1: 最小予測状態の復元

真の最小状態数が既知の確率過程を使い、次を検証しました。

1. Hankel行列の階数から最小線形予測次元を復元できるか
2. 密な線形状態を離散的な因果状態へ「結晶化」できるか
3. 最小状態IDとテーブル参照だけで同じ確率分布を再現できるか
4. 有限サンプルのノイズ下で状態数をどう選ぶべきか

結果:

- IID過程はHankel rank 1、因果状態1、実行時状態メモリ0 bitとして復元
- 2〜8状態のmodulo過程で、既知の最小状態数を正確に復元
- SVDで得る最小次元表現は密で、1記号あたり `r^2` MACを要する
- 同じ予測を離散因果状態へ変換すると、0 MAC・2テーブル参照/記号になる
- 最大特異値ギャップによる次数選択は、真のrank 5をrank 1と誤判定
- 2分割データのHankel差分から演算子ノイズ床を推定するとrank 5を復元

詳細: [`results/phase1.md`](results/phase1.md)

## Phase 2: 遷移法則の因数分解

K個の独立ビットを持つkey-value予測言語を構築しました。異なる2つの記憶割当ては、必ずあるkeyへのQUERYで異なる次トークンを返すため、厳密予測には最低Kビット必要です。

結果:

- 因数分解レジスタ機械はデータ記憶Kビットで下限に一致
- 平坦な因果状態表はready状態だけで `2^K` 個
- K=32では疎な平坦遷移表でも約5.6TB
- 因数分解モデルは10 bytes相当の確率パラメータとKビット記憶で実現
- dense FP32状態と比べたデータ書込み量はK=32で約6656分の1

詳細: [`results/phase2.md`](results/phase2.md)

## Phase 3a: MDLによる予測プログラム探索

人間が必要なレジスタ数を指定せず、0〜16スロットと書込みアドレス規則を列挙し、次を最小化しました。

```text
query NLL
+ runtime data bits
+ self-delimiting program bits
```

8-key言語から100,000トークンを生成して探索した結果:

- 最良構造は **8スロット・write offset 0**
- 15,486回のQUERYを0誤りで再現
- 7スロットは940誤り、6スロットは1,902誤り
- 9〜16スロットも正確だが、余分な状態・プログラム記述長で敗北
- 必要な記憶量とsame-keyアドレス規則を予測圧力だけから再発見

詳細: [`results/phase3a.md`](results/phase3a.md)

## Phase 4a: 最初のコンパイル済み超軽量LM

予測残差を減らす文脈規則だけを追加し、held-out NLLの改善量が規則自身の記述長を上回る場合だけ残すバイトLMを実装しました。

選択された疎な規則をfailure-link状態機械へコンパイルし、頻出するfallback遷移だけを、保存bitあたりの計算削減量が大きい順にshortcut化します。

日本語会話・コード・ログ・数値・key-value系列を混ぜた決定的micro-corpusでの結果:

- 学習: 625,748 bytes、別seedテスト: 155,073 bytes
- 選択規則: **608**
- コンパイル状態: **696**
- 実行時状態: **10 bit**
- 独自バイナリの実ファイル: **10,999 bytes**
- テスト: **0.468469605 BPB**
- 平均遷移確認: **1.015644回/byte**
- 保存→再読込後もBPB完全一致

固定order比較:

| model | BPB | compact bytes |
|---|---:|---:|
| fixed 3-gram | 0.557296466 | 16,294 |
| fixed 4-gram | 0.531891477 | 33,383 |
| fixed 8-gram | 0.727351516 | 399,426 |
| **compiled residual LM** | **0.468469605** | **10,999** |

UTF-8の正当性は確率モデルに再学習させず、数bitの決定的UTF-8状態機械として分離しました。現在の生成は局所的には文章らしいものの、意味理解や長期的整合性はまだ弱く、open-domain LMではありません。

詳細: [`results/phase4a.md`](results/phase4a.md)

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .
mpm-phase1
mpm-phase2
mpm-phase3a
mpm-phase4a
python -m unittest discover -s tests -v
```

`mpm-phase4a` は `results/phase4a.mplm` として実際のモデルバイナリも生成します。

## 次の研究段階

Phase 4aは文字列の局所規則を自動選択できましたが、候補は連続バイト文脈に限定されています。次は、予測残差の構造から必要な演算候補そのものを生成します。

```text
観測系列
  ↓
予測誤差が分岐する履歴対を抽出
  ↓
区別に必要な最小情報を探索
  ↓
context rule / register / counter / stack / sparse map候補を生成
  ↓
予測損失 + 状態bit + プログラム記述長 + memory trafficで選択
  ↓
頻出経路だけ直接コンパイルし、surprise時だけ高コスト処理
```

さらにPhase 4aの確率分布テーブルを、共有可能な形態素・意味特徴や低rank残差関数へ因数分解し、**数十KB〜数MB級で会話能力を持つモデル**へ段階的に伸ばします。
