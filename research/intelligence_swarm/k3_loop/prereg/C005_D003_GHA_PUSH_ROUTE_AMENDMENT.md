# C005 — D003-GHA canonical-branch one-shot push route amendment

Date: 2026-07-29
Role: K3-C
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **environment/import stageの起動経路だけを事前登録。model実行・学習は禁止**

## 1. 目的と単一仮説

C003/C004の候補、依存target、科学条件、判定閾値を変更せず、non-default canonical branch上の`workflow_dispatch`が起動できないorchestration blockerだけを除去する。

単一仮説:

> canonical branchとenvironment関連ファイルだけに限定した一回限りのpush routeなら、workflowをdefault branchへコピーせず、model executionを許可せずに、C003のexact dependency/import environment gateを起動し、provenance artifactを保存できる。

このrunはBlock AttnResの品質、速度、RSS、学習効率、量子化耐性、3-seed安定性を評価しない。

## 2. 変更を許可する唯一のworkflow差分

対象workflow:

- `.github/workflows/d003-k3-environment-gate.yml`

既存の`workflow_dispatch`は残し、次の`push` triggerだけを追加する。

- branch: `research/intelligence-swarm-reconstruction-001`のみ
- paths: 下記allowlistのみ
  - `.github/workflows/d003-k3-environment-gate.yml`
  - `benchmarks/k3_minimal/preflight/d003_gha_environment.sh`
  - `benchmarks/k3_minimal/preflight/d003_environment_probe.py`
  - `benchmarks/k3_minimal/manifests/C003_d003_gha_environment_gate.yaml`
  - `benchmarks/k3_minimal/manifests/C005_d003_gha_push_route.yaml`
  - `research/intelligence_swarm/k3_loop/prereg/C003_D003_GHA_ENVIRONMENT_GATE_AMENDMENT.md`
  - `research/intelligence_swarm/k3_loop/prereg/C005_D003_GHA_PUSH_ROUTE_AMENDMENT.md`
  - `research/intelligence_swarm/k3_loop/execution/C005_D003_GHA_PUSH_NONCE.txt`

禁止:

- broad branch trigger
- `pull_request` / `schedule` / repository-wide path trigger
- default branchへのworkflowコピー
- model、dataset、tokenizer、checkpoint、training codeをpath allowlistへ含めること
- allowlist外ファイルの変更を同じ起動commitへ混在させること

## 3. 一回限りの起動nonce

Dは次の専用ファイルを新規作成または一度だけ更新してpushする。

- `research/intelligence_swarm/k3_loop/execution/C005_D003_GHA_PUSH_NONCE.txt`

内容は以下を含む。

- `route_id: C005-D003-GHA-ENV-001`
- canonical branch head before amendment
- C005 prose blob SHA
- C005 manifest blob SHA
- UTC timestamp
- `training_authorized: false`
- `model_execution_authorized: false`

同じ科学条件での再起動は、run開始後にtransient failureへ分類された場合の一回だけ許可する。その場合、dependency target、workflow、script、manifest、判定条件を変更せず、nonceの`attempt`だけを`2`へ更新する。

## 4. Concurrencyと取消

workflowに次を固定する。

- concurrency group: `d003-k3-environment-${{ github.ref }}`
- `cancel-in-progress: false`
- 同時に有効なenvironment runは1件だけ

既存runがqueued/in-progressの場合、新しいnonce pushを行わない。実行中runを新しいpushで取り消してはならない。

## 5. Authorization guard

workflow jobのenvironment variablesまたはrunner scriptの入力として次を固定する。

- `K3_TRAINING_AUTHORIZED=false`
- `K3_MODEL_EXECUTION_AUTHORIZED=false`
- `K3_DATASET_DOWNLOAD_AUTHORIZED=false`
- `K3_TOKENIZER_DOWNLOAD_AUTHORIZED=false`
- `K3_CHECKPOINT_DOWNLOAD_AUTHORIZED=false`
- `K3_QUANTIZATION_AUTHORIZED=false`

runner scriptは開始時と終了時にこれらをartifactへ保存し、いずれかが`false`以外なら`ENV_PROTOCOL_FAIL`で停止する。

## 6. Checkout / branch identity gate

必須条件:

- event nameは`push`または既存のmanual diagnostic用`workflow_dispatch`
- pushの場合、`github.ref_name`はcanonical branchと完全一致
- checkout SHAはtrigger SHAと完全一致
- checkout後の`git status --porcelain`は空
- merge commitやdefault branch headへの置換は禁止
- workflow、script、C003/C005 manifest/prose、nonceのblob SHAを保存

branch/path guard不一致は科学的なenvironment failureではなく`ENV_PROTOCOL_FAIL`とする。

## 7. 実行stage

C005で許可するのはC003 Stage Eだけである。

許可:

- Python 3.11環境構築
- exact dependency resolution
- fixed candidate/official/Transformers source取得
- resolver report、freeze、hash、import probe
- environment artifact upload

禁止:

- B0/PB1/CR1のinstantiate、forward、backward、save/load
- dataset/tokenizer/checkpoint取得
- optimizer step、S1–S3
- CPU model timing、RSS比較、generation
- quantization
- architecture変更
- Stage E PASS後の同一run内または自動workflow chainによるStage M開始

## 8. Artifact schema

artifact名:

- `d003-gha-environment-${run_id}-${run_attempt}`

最低30日保持し、以下を必須とする。

### Run identity

- `run-context.json`
  - repository
  - canonical branch
  - event name
  - ref/ref_name
  - trigger SHA
  - checkout SHA
  - workflow path/blob SHA
  - run ID、run attempt、job ID
  - nonce route ID/attempt/blob SHA
  - actor
  - UTC timestamps

### Runner provenance

- `runner-provenance.json`
  - runner OS、architecture、image label/version
  - CPU model、visible cores
  - Python executable/full version
  - environment authorization flags

### Source/dependency provenance

- `repository-provenance.json`
- `resolver-report.json`
- `pip-freeze.txt`
- `pip-check.txt`
- `dependency-checksums.sha256`
- `required-imports.json`
- `source-and-patch.json`

### Logs and summary

- raw install log
- raw import/probe log
- `D003_GHA_environment_summary.json`
- artifact全体の`checksums.sha256`

summaryには判定、artifact name、run ID/attempt、trigger/checkout SHA、全required artifactの存在、checksum、patch使用有無を含める。

artifact IDとdownloaded ZIP SHA256はDがrun完了後に別の機械可読記録へ固定する。

## 9. Compatibility patch

C003の制約をそのまま継承する。

- 最大1件
- import path/API wiringだけ
- model equation、shape、initialization、source construction、block transition、routing priorを変更しない
- patchなし失敗log、unified diff、before/after hash、patch hash、semantic no-change説明を保存

`partial_block` reset、recency bias、gate、source list、forward式の変更は禁止する。

## 10. 判定

### `ENV_PASS`

以下をすべて満たす。

- registered push routeが1 runを生成
- branch/path/concurrency/authorization guard PASS
- exact source/dependency provenance保存
- required import全件PASS
- candidate module import PASS
- dirty treeなし
- required artifact全件存在
- artifact ID、artifact name、artifact contents SHA256を固定可能

`ENV_PASS`は後続C004 traceを検討可能にするだけで、model executionを自動許可しない。

### `ENV_RETRY`

runが開始された後に、GitHub Actions service、runner、GitHub/package index/DNS/networkの一時障害だけで失敗し、scientific/protocol codeが未実行または影響を受けた場合。

- workflow/script/manifest/dependency targetを変更しない
- nonce attemptだけを2へ変更
- 一回だけ再実行
- 二回目も同種障害ならEへ返し、追加retryを行わない

### `ROUTE_STOP`

登録済みcanonical branch/path限定pushを正しく行ってもrunが生成されない、またはGitHubが同routeを永続的に拒否し、workflow/default-branchコピーやbroad triggerなしでは起動不能な場合。

停止対象はこのexecution routeだけであり、Block AttnRes仮説ではない。

### `ENV_PATH_STOP`

runは開始したが、最大1件の許可されたAPI-wiring patch後も、固定source/dependency/importをsemantic変更なしで成立させられない、またはrequired provenance artifactを保存できない場合。

停止対象は現在の非公式実装environment pathだけである。

### `ENV_PROTOCOL_FAIL`

branch/path/authorization/hash/artifact/禁止取得など事前登録違反。結果は無効であり、E/Cの明示的amendmentなしに再実行しない。

## 11. 後続PB1 trace契約の持越し

以下は後続semantic trace用metadataであり、本C005のmodel execution権限ではない。

- semantic sublayer index: 1-based
- `L_transformer=12`
- `L_sub=24`
- `N=4`
- `S=6`
- ordered boundaries: `[3,6,9,12]`
- odd `S`または`L_sub % S != 0`を拒否
- sublayer source slots: `84`
- final-router sources: `5`
- total slots: `89`
- `primary_evidence_geometry_matched=false`
- PB1 nullは機構全体の棄却ではない
- PB1 positiveは採用根拠ではない
- higher-`N`は別preregistrationと別resource budgetが必須

## 12. Dへの実行可能な単一handoff

C005完成後、Dが次に実行できるのは以下だけである。

1. workflowへ本書とmanifestに一致する限定push/concurrency/authorization guardを適用
2. allowlist外変更がないことを確認
3. nonce attempt 1をcommit/push
4. environment-only runを1件確認
5. artifactとrun provenanceを回収
6. `ENV_PASS / ENV_RETRY / ROUTE_STOP / ENV_PATH_STOP / ENV_PROTOCOL_FAIL`を機械可読に記録

CR1/PB1 trace、full-model resource measurement、dataset、training、quantizationは別のE/C authorizationまで禁止する。

## 13. Evidence boundary

モデル品質、exact model bytes、active compute、isolated peak RSS、training time、CPU generation、quantization tolerance、three-seed stabilityは未測定のままである。新しい知能原理、能力進歩、高校生級能力、1GB目標達成を主張しない。
