# Phase 10b: 最小自然言語数学program

## 目的

Stage-C scorecardで数学がlevel 0だったため、最初の数学基盤として、自然言語から厳密な算術programを誘導します。問題文と答えのinteraction traceには演算labelを与えません。

## program同定

二つの数値を含むtraceについて、候補

```text
ADD
SUB
MUL
DIV
PERCENT_OF
```

を実行し、答えと一致するprogramを逆同定します。

\[
p^*(x,y,a)=\{p\mid p(x,y)=a\}
\]

一致候補が一つの場合のみ学習例として採用します。曖昧な例は、追加情報なしに恣意的に分類しません。

## 言語grounding

数値は規則へ記憶せず、発話から抽出した引数としてprogramへbindingします。語彙featureはoperationを選ぶ入口だけです。

\[
\hat p(u)=\arg\max_p\sum_{f\in F(u)}w(f,p)
\]

feature ruleは、同じprogramの複数例を覆い、他programを汚染しない候補から記述量あたりcoverageが最大のものをset coverで選びます。

## 結果

- training: 20例
- program: 5
- selected feature rules: 6
- program description: 642bit
- exact-surface held-out: 0%
- 未見数値・近い表現held-out: 10/10
- 生成した未見数値: 1,000/1,000
- 遠い数学語彙: 20%
- 10 interaction後: 100%
- 追加program: 282bit

これは数値の丸暗記ではなく、同じ小さなprogramを新しい引数へ適用できた結果です。

## 限界

一段の二項算術のみです。文章題、複数step、式変形、方程式、証明、幾何、確率、公開benchmarkは未達です。したがって数学のStage-C levelは2であり、open model比較可能なlevel 3/4ではありません。

次はevent graph上に中間変数、等式、量、単位、依存関係を追加し、program synthesisとproof traceを同じ表現で扱います。
