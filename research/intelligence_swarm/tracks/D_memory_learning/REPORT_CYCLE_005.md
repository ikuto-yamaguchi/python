# 系列D Cycle 005 — Self-Grouped Episodic Identity Consolidation

## 仮説
実験器が与える同一episode groupingを廃止し、時系列日本語の表面重なり・時間近接・後続質問への予測利得から、同一対象・同一記憶episodeの候補を自己誘導できるかを検証した。未知表現は高速暫定記憶に保持し、曖昧な候補は可逆的に棄権する。

## 他系列との重複回避
- A: 確認発話や返答解釈ではなく、確認前の記憶episode grouping。
- B: operation graphのMDL圧縮ではなく、記憶のまとまりの自己誘導。
- C: 因果event branchではなく、事実episodeの束縛。
- E: energy緩和ではなく、時間近接と再利用に基づく記憶統合。

## 実験
48/180/540更新、seed 1/7/19。直接質問、代名詞、表記揺れ、長い言い換え質問、無関係発話干渉を評価した。固定slot名、外部LLM、RAG、ベクトルDBは未使用。比較は表面最近傍記憶と自己grouping記憶。

## 540更新・3 seed平均
| 指標 | 表面最近傍 | 自己grouping |
|---|---:|---:|
| online | 0.0020 | 0.0000 |
| direct | 0.0000 | 0.0000 |
| pronoun | 0.0000 | 0.0000 |
| variant | 0.0000 | 0.0000 |
| unseen query | 0.0000 | 0.0000 |
| model bytes | 52057 | 111427 |
| inference ms | 3.416 | 7.419 |
| reversible abstentions | 0 | 33.7 |

Peak RSSは308468 KiB（Pythonランタイム込み）。

## 判定
中核仮説は反証。両方式とも全評価軸がほぼ0で、自己groupingはモデルサイズと推論時間を悪化させた。時系列近接と文字重なりだけでは、対象・値・関係を分離できず、候補残差が助詞・述語・値を混在させた。可逆棄権は誤答を抑えたが、選択的な不確実性ではなく候補margin崩壊による全面的失敗である。

## 系列D固有の知見
同一episode groupingを外すと、これまで成立していた睡眠統合・再固定化解除の前提自体が崩れる。記憶更新則より上流に、episode identity候補を生成する機構が必要である。時間近接性は補助証拠にはなるが、単独では意味的共参照を形成しない。

## 他系列へ返す知見
- A: 対話状態候補の更新前に、どの発話が同一episodeかの不確実性を保持する必要がある。
- B: 可逆parse候補は、後続質問へのwrite/read成功で監査する必要がある。
- C: event identityとepisode identityは別に誘導しなければならない。
- E: grouping候補が異なる将来想起を生成しない限り、energyでは選別できない。

## 次仮説
**Predictive Retrieval Gain Grouping with Negative Evidence**。候補groupingごとに、後続質問への想起改善だけでなく、別episode質問への誤干渉、更新後の最新値保持、代名詞照応、反例によるgrouping解除を測定する。単なる時間近接・文字重なりを主目的から外し、異なる予測結果を生むgrouping候補のみ保持する。

高校生級未達。ネイティブ日本語コミュニケーション未達。弱いスマートフォン実機未検証。完成未達。
