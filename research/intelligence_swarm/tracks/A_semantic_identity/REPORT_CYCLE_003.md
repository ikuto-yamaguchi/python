# 系列A Semantic Identity Cycle 003

## 仮説

**Cross-Domain Consequence-Anchored Unit Rebirth from Few Observed Transitions**  
（少数の観測遷移からのdomain横断・結果接地unit再生成）

GOV-004 / PR #361 で AF-005 `Cross-Domain Consequence-Invariant Grounding` が本線へ昇格したため、語彙・座標・object indexを直接対応させる方式を棄却した。

未知domainでは、domain辞書や共有identityを与えず、16件（4 relation × 4 move）の観測episodeだけを局所更新へ使う。各episodeでは raw Japanese全文と、観測されたbefore→afterから得る匿名の結果signatureを結合する。テスト時は raw Japanese + before world + hypothetical target/moveだけを使い、future outcomeは使わない。

比較:

- Zero-shot: base domainだけで学習
- Correct adaptation: 新domainの観測遷移16件で局所更新
- Shuffled adaptation: 発話と観測結果の対応をshuffle
- Dose: 0 / 1 / 2 / 4 observation per relation×move
- Second opaque domain: 別の完全に異なる語彙体系で再実施

## 凍結族との分離

- span・位置・幅をsemantic unit候補にしない
- domain対応辞書、共有ID、固定ontologyを使わない
- MDL、graph、assembly、energyで後段選別しない
- post-treatment情報はadaptation時の観測としてのみ使用し、test時には使用しない
- unitは保存文字列ではなく、発話と選択的結果signatureの局所結合

## 3 seed平均

Joint chance = 0.03125、target chance = 0.125、move chance = 0.25。

| 条件 | Zero-shot joint | Correct adaptation | Shuffled adaptation | Correct-Shuffle |
|---|---:|---:|---:|---:|
| Held | 0.0347 | 0.0694 | 0.0347 | +0.0347 |
| Rename | 0.0139 | 0.0139 | 0.0139 | +0.0000 |
| 未知語順 | 0.0208 | 0.0208 | 0.0347 | -0.0139 |
| 主語省略 | 0.0208 | 0.0417 | 0.0069 | +0.0347 |
| 複数段落 | 0.0347 | 0.0833 | 0.0417 | +0.0417 |
| 自由日本語 | 0.0278 | 0.0486 | 0.0208 | +0.0278 |

追加:

- Held target: Correct 0.1944 / Shuffle 0.1042
- Held move: Correct 0.3472 / Shuffle 0.2778
- Inverse: Correct 0.2500 / Shuffle 0.2431
- 2つ目の完全別語彙domain・自由日本語: Correct 0.0139 / Shuffle 0.0069
- Held dose joint: 0-shot 0.0347 / 1-shot 0.0694 / 2-shot 0.0833 / 4-shot 0.0694
- Held Correct-Shuffle gap: 平均 0.0347、正方向seed 2/3、最小gap 0.0000

## 判定

**限定支持だが、能力上の進歩は認定しない。G1未達。**

新domainの観測遷移16件を正しく対応させると、Held、主語省略、複数段落、自由日本語でZero-shotおよびShuffleより改善した。特にHeldは joint 0.0694 対 shuffle 0.0347、target 0.1944 対 0.1042 だった。

これは、対応辞書なしでも**新domain内で観測した選択的結果を足場に、発話―結果unitを再生成できる弱い信号**である。過去のzero-shot構造可換性だけとは根本前提が異なる。

ただし、次の理由でSemantic Identity Birthとは認定しない。

1. Renameと未知語順ではCorrect-Shuffle差が消失または逆転する。
2. Inverse queryはchanceと同じ 0.2500。
3. 2つ目のdomainでは自由日本語jointが 0.0139 に留まる。
4. Held gapは3 seed中2 seedのみ正で、最小gapは0。
5. relationとmoveのopaque tokenを新domain内で再利用しており、任意の未観測言い換えを結果から生成できていない。

したがって得られたものは `few-observation domain-local consequence grounding` であり、cross-domain semantic identityではない。

## 反証条件と知見

- Zero-shotで意味は移らない。
- 正しい観測対応は一部条件を改善するが、結果signatureだけでは言い換え同値類とinverse利用を形成しない。
- observation doseを増やしても単調改善せず、4-shot jointは1-shot以下だった。単純Hebbian蓄積は干渉を受ける。
- 次は結果が同じ発話を束ねるだけでなく、**未知表現を能動的に同じ結果へ接地する識別行為**が必要。

## 他系列へ返す知見

- B: operation unitは新domainの観測遷移から局所再生成できる可能性があるが、inverse/goal利用を別gateにする。
- C: adaptation episodeの選択的結果が必要条件。結果対応shuffleでHeld能力が落ちる一方、全表現では一貫しない。
- D: Heldだけを記憶資格にしない。Rename・未知語順・inverse・second-domainを同時通過するunitは0。
- E: AF-005は限定継続可能。ただし「少数観測だけでcross-domain semantics成立」は支持されず、domain-local groundingへ証拠ラベルを縮小する。

## 資源量

- Matrix: 65,536 bytes
- Adaptation: 16 records/domain
- Peak RSS: 113,036 KiB（Python + NumPy runtime込み）
- 3 seed総時間: 9.1967 sec
- Update: 約16,384 ops/episode
- Inference: 約16,384 ops/option、32 options/query
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証

## 次の仮説

**Active Consequence Disambiguation for Novel-Utterance Unit Birth**

未知発話を受けた際、既存unitへ強制割当てせず、候補unitが異なる結果を予測する最小の観測・介入を選ぶ。得られた結果から発話を局所接地し、同じ発話を見ていないparaphrase、inverse、second-domainへ転送できるか検証する。

進歩条件:

- Rename、未知語順、自由日本語、second-domainの全てで Correct-Shuffle joint差 +0.10以上
- inverse > 0.40
- 3/3 seedで正方向
- post-treatment leakageなし

- Semantic Identity Gate G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
