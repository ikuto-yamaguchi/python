# RESET-E080 — R0 Research Reconstruction integration

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## 1. Prior-art / official-code duplication audit

E079までに固定したscore-based CRL、finite-sample CRL、Multi-View CRL、GPI、ReCITE、C3、CmIR、CausalVerse、MagicBench、AER、COGS等の境界を維持した。今回、RQ-001を採用へ反転できる「最新一次文献 + author-official code + exact commit + public numerical contract」の新しい組は確認できていない。文献名だけを追加してnovelty matrixを水増ししない。

RQ-001は引き続き広義棄却、狭義未採用とする。採用には既存baselineを差し引いたlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要である。

## 2. SILG / J-CRe3 reproduction progress

Canonical PR #409はopen / draft / mergeableで、headは`041e3579baaf5dbc35d533b3cf64143ce6515483`である。

One-step resume-equivalenceはcanonical PRのimmutable ledger上でaccepted:

- run `30300067389`
- job `90090542489`
- artifact `8666312079`
- artifact SHA-256 `34f02c802f6db15b55336a0547e3914846aad6d74783ebfc371d12ca6ac08115`
- frame transition `3840 -> 5760`
- exact learner batch / initial recurrent state / learner model / optimizer / scheduler / gradient / Python・NumPy・Torch RNG / stats / frame incrementが一致

これはcaptured official learner updateのexact replayだけを証明する。asynchronous queue continuation、100M horizon、能力再現は証明しない。

Official 100M continuation workflow `.github/workflows/r01_silg_official_100m_chunk.yml`は同じcanonical branchに存在する。seed 1、entropy 0.05、official sampling defaultsを保持し、最初のdurable checkpointとして1,000,000 framesをtargetにする。ただし、この統合時点でconnectorからpush-run本体のrun/job/artifactを独立確認できていないため、状態は`submitted / result unconfirmed`とする。

J-CRe3 numerical reproductionは0件のまま。

## 3. Matched controls

最新のqualified official-horizon checkpoint評価はまだ存在しないため、random / language-blind / state-only / shuffleは未測定。既存8件の131k-frame結果はshort-horizon negative archiveとしてのみ保持し、official baseline failureへ外挿しない。

最新short-horizon result:

- run `30240410850`, artifact `8644560521`
- Correct `3/60`, Random `4/60`
- Language-blind `0/60`, State-only `0/60`, Language-shuffle `3/60`
- Correct return `-1.7679994`, Random return `-1.1513333`
- qualification rejected

## 4. Model / RSS / runtime / seed / split

Official infrastructure probe remains the current resource anchor:

- run `30258965674`, artifact `8650362356`
- peak RSS `9,305,052 KiB`
- wall `631.66 s`
- throughput `63.83 frames/s`
- checkpoint frames `40,320`
- projected 100M wall `18.13 runner-days` per entropy/seed run

Official 100M contract remains model `multi`, stateful `false`, actors `30`, threads `4`, batch `24`, unroll `80`, learning rate `0.0005`, RMSprop, gradient clip `40`, seeds `1/7/19`, fixed RTFM train/test split.

## 5. Leakage / evaluation contract

PR-head checks show canonical instance identity, unified acceptance gate, artifact containment, raw-log binding, prediction topology, score dataset-contract binding, normalized holdout/cell identity are passing. `R0D core normalized cell identity` alone is failing and must be diagnosed independently; it is not evidence of model failure or capability regression.

The standalone canonical-instance-identity auditor is present and its focused workflow passes. Direct fail-closed integration into `validate_dataset()` and `score()` remains backlog work; until then the standalone audit must not be omitted from any claimed bundle.

No new capability-run leakage result exists. Latest short-horizon answer leakage remains `false`.

## 6. RQ-001 and stage gate

- broad RQ-001: rejected
- narrow RQ-001: not adopted
- new mechanism family: not recognized
- new intelligence principle: none
- capability progress: not recognized
- public baseline reproduced: false
- R0.2 qualified: 0
- R0.3 hidden intervention-target ablation: rejected / maintained
- novelty matrix: incomplete
- central-claim preregistration: incomplete
- high-school-level intelligence: unmet
- next stage: not proposed

## Next single actions

1. Resolve the failing `R0D core normalized cell identity` check without changing model or benchmark conditions.
2. Obtain the first official 1M checkpoint run/job/artifact and verify checkpoint frames, optimizer/scheduler state, command parity, bytes, SHA-256, RSS and runtime.
3. Only after a durable trained checkpoint exists, attach matched Correct/random/language-blind/state-only/shuffle evaluation and leakage audit.
4. Do not dispatch a new mechanism, toy task, alternate branch or capability claim.
