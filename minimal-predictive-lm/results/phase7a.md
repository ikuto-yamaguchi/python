# Phase 7a results: controlled conversation and instruction following

This phase asks whether the current minimum-machine line actually scales into interaction,
rather than only solving isolated micro-functions.

## Trial-and-error attempts

| attempt | turn accuracy | episode success | main failure |
|---|---:|---:|---|
| v0 literal scan agent | 35.3% | 2/8 | paraphrase, pronoun, correction, compound task, tool recovery |
| v1 canonical indexed agent | 82.4% | 6/8 | polite variants and sequential separator were not canonicalized |
| v2 normalized canonical agent | 100.0% | 8/8 | controlled grammar succeeds; unrestricted paraphrase remains weak |

## Open-form probe

The v2 agent passed **4/8 (50.0%)** colloquial/open-form turns.
Four residual rewrites raise the observed probe to **100.0%**, but a shifted colloquial probe reaches only **50.0%**.
This intentionally separate probe shows that perfect controlled-benchmark accuracy is not ordinary human conversation, and patching phrases can overfit.

## Scaling of fact lookup

| stored facts | linear scan reads/query | indexed reads/query | state bits |
|---:|---:|---:|---:|
| 16 | 16 | 1 | 288 |
| 64 | 64 | 1 | 1,536 |
| 256 | 256 | 1 | 7,680 |
| 1,024 | 1,024 | 1 | 36,864 |
| 4,096 | 4,096 | 1 | 172,032 |

The direct index keeps query reads constant in this benchmark, while exact fact storage grows
linearly because independent names and locations contain irreducible information.

## Dialogue-length scaling

Across 10,000 repeated relevant queries, persistent fact count stayed at 1 and state bits stayed at 6.
The transcript is not copied into active state; one indexed fact read is paid per query.

## Code-candidate scaling limitation

| candidate patches | exhaustive evaluations |
|---:|---:|
| 8 | 16 |
| 32 | 64 |
| 128 | 256 |
| 512 | 1,024 |
| 2,048 | 4,096 |

The current test-feedback task loop is linear in candidate count and therefore does not scale to real repositories.
A structural program synthesizer, admissible bounds, and repository indexing are required before LLM-level coding claims.

## Successful controlled transcript

- User: 試作品は棚Aにある。
- Machine: 了解。試作品は棚Aにあります。
- User: それを検査室へ移して。
- Machine: 試作品を検査室に移しました。
- User: 今どこ？
- Machine: 試作品は検査室にあります。

## Tool task with failure recovery

- User: transform関数をテストに通るよう修正して。
- Machine: 最初の `x + 1` は隠しテストで失敗しました。失敗を反映して `x * x + 1` に修正し、全テストに成功しました。
- Tool calls: 9
- Candidate evaluations: 6
- Final hidden tests: PASS

## Honest conclusion

The architecture now demonstrates multi-turn reference, exact unseen-name retention, correction,
compound instruction execution, and a test-failure/retry loop without a dense neural runtime.
It has **not** demonstrated open-domain conversation, broad instruction understanding, repository-scale
coding, or parity with a high-performance LLM. The dominant bottleneck has moved from fact lookup to
automatic induction of canonical intents, predicates, goals, and reusable programs from unrestricted text.
