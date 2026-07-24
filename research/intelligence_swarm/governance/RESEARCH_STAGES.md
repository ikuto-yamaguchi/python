# Research Stages and Gates

## S1: Semantic Identity Birth — ACTIVE

問い: 生の自由日本語と観測・行為・結果から、何が同じ対象・変数・関係として再同定されるのか。

### Semantic Identity Gate G1

次をすべて満たすまでS2以降を本線化しない。

1. 3 seed以上で、未知語順・Rename・別表現のうち3条件以上において外部実行能力が0ではない。
2. Correct alignmentがshuffle/randomを絶対値0.15以上、かつseed分散を考慮して明確に上回る。
3. 同一latent unitがprospective predictionとinverse queryの双方で再利用される。
4. 対象交換または値交換で、対応するsupportだけが選択的に移動する。
5. Unit lesionで対応能力だけが30%以上相対低下し、非対応能力は概ね維持される。
6. Final answer、after、future、test labelを候補生成・rankingに利用していない。
7. 1GB未満で、弱いスマートフォンCPUに収まる更新・推論計算量を示す。

## S2: Operation and Goal Birth — BLOCKED BY G1

問い: 同じ対象に対して何が行われ、何を目指し、どの条件で成功するか。

Gate G2は、未知対象・未知表現で同一操作がrollout、inverse explanation、goal変更に再利用され、Correctがshuffle/randomを上回ることを要求する。

## S3: Causal Grounding and World Model — SUPPORTING S1, MAINLINE BLOCKED BY G1/G2

問い: 潜在単位と操作が、介入、時間順序、non-target保存、反実仮想を説明するか。

S1中のCは、因果graphを完成させるのではなく、identityを識別可能にする最小介入と反例を設計する。

## S4: Memory and Continual Learning — BLOCKED BY G1

問い: 再同定可能な単位を、いつ記憶し、どう更新し、いつ忘れるか。

取得時能力が0のまま、replay、consolidation、assembly、fast/slow memoryを最適化してはならない。取得成功後にのみ保持・干渉・忘却を測る。

## S5: Integrated General Intelligence — BLOCKED

同一モデルで自由対話、読解、推論、計画、因果、反実仮想、長期対話、継続学習、未知領域転移を評価する。

## 遷移規則

- Eだけが正式なstage変更を宣言する。
- Gate未達でも、上流gateを識別するための支援実験は許可する。
- 下流機構の局所成功を理由にstageを飛び越えない。
- 最大ボトルネックが変わった場合、次サイクルから全系列の優先順位を再配分する。
