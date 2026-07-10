# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測に必要な**最小記憶**と**最小計算**を数学的な下限から逆算する研究用ディレクトリです。

## 中心仮説

過去全文を保持する必要はない。同じ未来分布を与える履歴は、予測上は同一状態へ圧縮できる。

\[
h \sim h' \iff P(X_{future}\mid h)=P(X_{future}\mid h')
\]

Phase 1では、真の最小状態数が既知の確率過程を使い、次を検証します。

1. Hankel行列の階数から最小線形予測次元を復元できるか
2. 密な線形状態を離散的な因果状態へ「結晶化」できるか
3. 最小状態IDとテーブル参照だけで同じ確率分布を再現できるか
4. 有限サンプルのノイズ下で状態数をどう選ぶべきか

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .
mpm-phase1
python -m unittest discover -s tests
```

## 現在の到達点

- IID過程はHankel rank 1、因果状態1、実行時状態メモリ0 bitとして復元
- 2〜8状態のmodulo過程で、既知の最小状態数を正確に復元
- SVDで得る最小次元表現は密で、1記号あたり `r^2` MACを要する
- 同じ予測を離散因果状態へ変換すると、0 MAC・2テーブル参照/記号になる
- 最大特異値ギャップによる次数選択は、真のrank 5をrank 1と誤判定
- 2分割データのHankel差分から演算子ノイズ床を推定するとrank 5を復元

詳細は [`results/phase1.md`](results/phase1.md) を参照してください。

## 次の研究段階

有限状態で説明できない情報だけを扱う、イベント駆動型の疎な残差メモリを追加します。

```text
離散因果状態（常時・O(1)）
        ↓ surpriseが低い
   テーブル遷移だけ
        ↓ surpriseが高い
疎な残差メモリを1〜数セルだけ更新
```

目標は、密な隠れベクトルを毎記号更新するのではなく、**新しい情報が発生したときだけ計算と書き込みを行うLM**です。
