# 系列B Cycle 009 研究報告

## 仮説
**Execution-First Anti-Unification with MDL-Only Consolidation**（実行優先反統一と、統合専用MDL）

Cycle 008では、可逆・短記述な候補でも実行可能なrole/effect programにならず全面棄権した。本サイクルではMDLを候補生成・初期順位付けから外し、before/after差分から得た候補が観測afterを厳密再現する場合だけprogram候補へ昇格させた。MDLは保存単位の統合にのみ使う設計を最小実装した。

## 重複表

| 系列 | 最新中心 | 成功・失敗 | B候補との重複判定 |
|---|---|---|---|
| A | 証拠channel変化点 | drift誤確定を削減、候補世界生成は未成立 | 外部証拠校正なので非重複 |
| C | 複数operation効果factor | 5 signatureを形成、zero-shot意味転移は弱い | 因果condition形成は棄却 |
| D | 談話focus fast weights | 既知cueは強い、未知cue即時は失敗 | 記憶統合は棄却 |
| E | factor十分性と局所緩和 | candidate recall改善、margin 0 | energy選択は棄却 |
| B | execution-first anti-unification | 実行候補生成を先行しMDLを後段化 | 固有方向 |

継承知見:
- A: 内部圧縮・entropy低下は正しさを保証しない。
- C: 効果signatureは候補の監査信号になるが表面alias追加に留まり得る。
- D: 正しい候補がない場合、後続想起・統合は救えない。
- E: candidate recallとfactor selectionを分離測定する。

## 実装
固定entity/value一覧、形態素解析、意味slot、既成ontology、外部LLM、RAGは学習器へ与えていない。文字列before/afterの共通prefix/suffixと差分を用いて状態編集候補を作り、観測afterを厳密再現する候補のみ保持した。推論ではcommand中の未観測区間を状態skeletonへ再束縛し、最良scoreで実行結果が一意な場合だけ回答した。

## 360例・3 seed平均

| 指標 | surface-MDL | execution-first |
|---|---:|---:|
| 既知構文 | 0.0278 | 0.0278 |
| 未学習語順 | 0.0000 | 0.0000 |
| 未知述語 | 0.0778 | 0.0778 |
| 入れ子 | 0.0000 | 0.0000 |
| 主語省略 | 0.0056 | 0.0056 |
| 別状態表現 | 0.0000 | 0.0000 |
| モデルbytes | 4,104.3 | 4,104.3 |
| program数 | 24 | 24 |
| 既知推論ms | 1.1096 | 1.1335 |
| 既知候補読出し | 149.9 | 149.9 |

Peak RSS: 396,956 KiB（Python runtime込み）。推定計算量は学習 O(NL)、推論 O(P L² + H) で、今回P=24。モデルは1GB未満だが、能力が低いため弱いスマートフォン向け原理として採用不能。

## 反証
**中核仮説は反証。**

1. execution-firstとsurface-MDLの能力が完全に同一で、実行filterが候補集合を改善していない。
2. 既知構文さえ0.0278。before/afterを再現できることは、command中のどの区間が新値・述語・対象roleかを識別しない。
3. 未学習語順・入れ子・別状態表現は0。未知述語も0.0778に留まる。
4. 平均候補読出しは既知約150、未学習語順約316で、探索爆発を抑えられていない。
5. 共通prefix/suffixによる状態skeletonは状態表現変更で消滅し、relation quotientになっていない。
6. 可逆性、観測after再現、短い記述長を組み合わせても、生の日本語からargument roleとoperation primitiveは創発しない。

重要な否定結果:
> 単一episode内の実行再現はgroundingとして弱すぎる。反統一候補は、同一episodeのafter再現ではなく、保持したepisode群へのcross-episode再実行で生成段階から淘汰する必要がある。

## 系列B固有の進展
MDLを後段へ退けるだけでは不十分だと判明した。必要な順序は、(1) cross-episode executable proposal、(2) role/value permutation・identity rename・state realization変更での再実行監査、(3) その後にMDLで統合・保存、である。単一episodeのafter再現だけでは、表面編集候補が大量に残りcandidate precisionが上がらない。

## 他系列へ返す知見
- A: 質問対象候補は単一観測を説明するだけでなく、複数episodeへ再実行可能である必要がある。
- C: 単一operation効果の再現ではroleを特定できない。複数identity・relationでのcross-intervention probeが必要。
- D: 低速統合前に別episodeへの書込み・想起を実行し、候補precisionを監査する。
- E: candidate recallだけでなく、cross-episode実行結果で同型候補を商空間化してからenergyを適用する。

## 次仮説
**Cross-Episode Permutation-Complete Anti-Unification**（episode横断・置換完備反統一）

候補を学習元episode自身では評価せず、保持out episodeへidentity/value/roleを置換して再実行し、after再現、inverse再現、non-target保存、state realization間の同一effect、語順変更を同時に満たす場合だけprimitiveへ昇格する。

次回の必須条件:
- 既知0.0278を大幅改善
- 未学習語順と未知述語を同時改善
- candidate readsを32以下
- candidate recallとprecisionを別々に測定
- 32KB、5ms/query以下
- 自由日本語統合ゲートに回帰なし

## 再現
```bash
python research/intelligence_swarm/tracks/B_compression_symbols/execution_first_anti_unification_cycle9.py \
  --output research/intelligence_swarm/tracks/B_compression_symbols/results_cycle_009.json
```

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
