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

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .
mpm-phase1
mpm-phase2
mpm-phase3a
python -m unittest discover -s tests -v
```

## 次の研究段階

現在のPhase 3aは、候補DSLを人間が限定しています。次は、予測残差の構造から必要な演算候補そのものを生成します。

```text
観測系列
  ↓
予測誤差が分岐する履歴対を抽出
  ↓
区別に必要な情報ビットを同定
  ↓
register / counter / stack / sparse map候補を生成
  ↓
予測損失 + 状態bit + プログラム記述長 + memory trafficで選択
  ↓
surpriseが発生したイベントだけ疎に更新
```

目標は、密な隠れベクトルを毎記号更新するのではなく、**新しい情報が発生したときだけ状態構造を変化させるLM**です。
