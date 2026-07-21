# 系列B Cycle 006 — Role-Factored Multi-View MDL Encoder

## 目的

Cycle 005では latent operation node と surface decoder の分離により保存重複は減ったが、未知語順・完全未学習同義動詞は0のままだった。本サイクルでは、before / command / after の複数viewから episode-local identity/value を可逆に分離し、命令残差をargument-role付きencoderとして再利用できるかを検証した。

## 他系列との重複表

| 系列 | 最新の中心機構 | 本サイクルで避けた重複 | 継承した知見 |
|---|---|---|---|
| A | 承認・否定による予測状態修復 | 質問生成・対話feedbackは扱わない | 候補entropyに見合う識別情報が必要 |
| C | identity分離型event program | 因果branch gatingは扱わない | operationとepisode bindingの分離は必要 |
| D | episode groupingと記憶統合 | 長期記憶・睡眠統合は扱わない | grouping候補は異なる将来結果を生む必要 |
| E | role構造付き条件分岐graph | energy緩和は扱わない | 境界数ではなく非同型role graphが必要 |

## 仮説

同一episodeのbefore / command / afterで反復する表面区間をepisode-local role bindingとして除去し、残った命令断片を低記述長のoperation encoderとして共有すれば、命令全体のliteral templateを保存する方式より、未知語順とrenameの組合せへ転移する。

反証条件は以下。

1. 未学習語順がliteral baselineを上回らない。
2. 完全未学習同義動詞が0のまま。
3. role分離による保存量・推論量の増加が能力向上に見合わない。
4. 自由日本語統合ゲートが0のまま。

## 実装

- 学習器にentity/value一覧、slot名、形態素解析器、固定ontologyを渡していない。
- beforeとcommandに共通する区間をidentity候補、commandとafterに共通する新規区間をnew-value候補として扱う。
- episode-local表面値を除いたcommand residueを文字2/3/4-gramで圧縮・共有する。
- literal graph baselineは `<E>` / `<V>` 化した命令全体が完全一致する場合だけ実行する。
- role encoderはoperation residueとno-op residueの近さから実行branchを選択する。

これは意味解析器ではなく、role factoringがどこまで表面語順依存を減らすかを測る最小probeである。

## 実験条件

- train sizes: 60 / 180 / 360
- seeds: 1 / 7 / 19
- splits: 既知構文、未学習語順、完全未学習同義動詞、全面rename、rename+未学習語順、no-op
- モデルサイズ、保存unit、推論時間、Peak RSSを測定

## 360例・3 seed平均

| 指標 | literal graph | role-factored encoder |
|---|---:|---:|
| 既知構文 | 1.0000 | 1.0000 |
| 未学習語順 | 0.0000 | **0.4778** |
| 完全未学習同義動詞 | 0.0000 | 0.0000 |
| rename | 1.0000 | 1.0000 |
| rename + 未学習語順 | 0.0000 | **0.4778** |
| no-op | 1.0000 | 1.0000 |
| model bytes | **18,157** | 144,725 |
| stored units | **456** | 462 |
| seen inference | **0.00059 ms** | 1.4115 ms |
| held-order inference | **0.00850 ms** | 1.8920 ms |

Peak RSSは303,756 KiB。Python runtime全体を含み、方式固有値でも弱いスマートフォン実測でもない。

## 判定

### 限定的支持

role-localな表面値を除いた命令残差を共有することで、完全一致baselineが0だった未学習語順とrename+未学習語順が約0.478まで改善した。したがって、**episode bindingとoperation residueを分離することは、限定的な語順不変性を得る部品として有効**である。

### 中核仮説の反証

完全未学習同義動詞は全seedで0。`移動`・`変更`など学習済み残差との文字重なりがなければ既知operationへ写像できない。argument roleを意味的に獲得したのではなく、既知predicate断片の位置変化へ部分的に耐えただけである。

さらにrole方式は、全学習episodeのresidue特徴を保持したため、literal baselineに対してモデルサイズ約7.97倍、推論時間は数百〜数千倍に悪化した。保存pattern自体は6種類へ圧縮できたが、特徴prototypeを重複保持しており、MDL実装として不十分である。

未学習語順でも約52.2%を棄権し、自由日本語統合ゲートは0。対象・操作・目的・因果・生成・対話・計画は成立していない。

## 先行研究との整合

MDLは表現の複雑度と一般化を結び付ける理論的枠組みを与える一方、圧縮だけで正しい意味表現が同定されるわけではない。構成的一般化研究でも、明示的な文法・辞書や実行分解などの追加構造が強い性能を生む一方、それらを手書きせず誘導することが難所として残る。今回も、role factoringで語順variantは改善したが、未知primitiveの意味同定には失敗した。

## 系列B固有の新知見

1. operation/decoder分離だけでなく、episode bindingをencoder入力から除くと語順variantへ部分転移する。
2. ただしrole edgeを表面共起から作るだけでは、未知predicateを既知operationへ結べない。
3. prototype重複を残したままrole候補を増やすと、圧縮原理に反して資源だけ悪化する。
4. 次に必要なのはspan境界ではなく、複数viewで同じ実行効果を持つpredicate fragmentを一つのprimitiveへ統合する**効果条件付きprimitive induction**である。

## 他系列へ返す知見

- A: 確認候補の文面差ではなく、role-factored operation候補の実行差を質問分割へ使うべき。
- C: identity分離後もpredicate encoderが表面依存なら、未知命令からevent programを呼び出せない。
- D: residue prototypeをepisode数だけ保存せず、反復して同じwrite/execute効果を持つものだけ低速primitiveへ統合すべき。
- E: role候補は境界差ではなく、異なるprimitive割当てと異なるworld transitionを生成して初めて非同型候補になる。

## 次の仮説

**Effect-Conditioned Primitive MDL with Held-Lexeme Bridging**

同一状態変化を起こす複数命令のpredicate区間を、文字類似ではなく before/after の実行効果で共同符号化する。各primitive候補は、surface fragment、argument-role edge、state-transition effect、decoder residueを双方向に持つ。完全未学習lexemeは直接意味付けできないため、別episodeでそのlexemeと実行効果が一度だけ同時観測された後、未知語順・rename・compositionへ転移するone-shot bridgingを主要評価にする。

必須成功条件:

- 未学習語順0.4778を上回る。
- 新lexemeを一回のeffect付き観測後に既知operationへ統合する。
- prototype保存をepisode数へ線形増加させない。
- model bytesと推論時間をCycle 006より大幅に削減する。
- no-op/confoundを文字列類似なしで分離する。

## 最終状態

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
